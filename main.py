import os
import json
import logging
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

import PIL.Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
import google.generativeai as genai


# ===== КОНФИГУРАЦИЯ =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Проверка, что токены заданы
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан! Установите переменную окружения.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY не задан! Установите переменную окружения.")

TELEGRAM_CHANNEL_ID = "-1003352192902"  # ID вашего канала для логов

genai.configure(api_key=GEMINI_API_KEY)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ===== МОДЕЛИ ДАННЫХ =====

@dataclass
class SingleItem:
    id: int
    name: str
    price: float
    is_selected: bool = False
    selected_for_part: Optional[int] = None


@dataclass
class Receipt:
    items: List[SingleItem] = field(default_factory=list)
    total: float = 0.0
    store: str = ""


@dataclass
class SplitSession:
    receipt: Receipt
    total_parts: int
    current_part: int = 1
    temp_selected_ids: List[int] = field(default_factory=list)


# ===== ЛОГИКА РАСПОЗНАВАНИЯ =====

class ReceiptParser:
    @staticmethod
    async def parse_receipt(image_path: str) -> Receipt:
        prompt = """
        Ты — ассистент по чекам. Проанализируй фото и верни ТОЛЬКО чистый JSON:
        {
            "store": "название магазина",
            "items": [{"name": "товар", "price": 100.0, "qty": 1}],
            "total": 100.0
        }
        Правила:
        1. Если товар в количестве N шт, создай N отдельных записей в списке "items".
        2. Цену за 1 шт вычисляй (общая цена / количество).
        3. Игнорируй скидки, налоги и ИТОГО как отдельные товары.
        """

        try:
            # Используем with, чтобы гарантированно закрыть файл для Windows
            with PIL.Image.open(image_path) as img:
                response = await asyncio.to_thread(model.generate_content, [prompt, img])

            text = response.text.strip()
            # Очистка от markdown-опоясывания
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            data = json.loads(text.strip())

            receipt = Receipt(
                store=data.get("store", "Неизвестно"),
                total=float(data.get("total", 0))
            )

            for idx, item_data in enumerate(data.get("items", [])):
                receipt.items.append(SingleItem(
                    id=idx,
                    name=item_data.get("name", "Товар"),
                    price=float(item_data.get("price", 0))
                ))
            return receipt
        except Exception as e:
            logger.error(f"Ошибка Gemini: {e}")
            raise Exception("Не удалось корректно распознать чек.")


# ===== КЛАВИАТУРЫ =====

def get_items_keyboard(items: List[SingleItem], selected_ids: List[int]) -> InlineKeyboardMarkup:
    keyboard = []
    available = [i for i in items if not i.is_selected]

    for item in available:
        is_checked = "✅ " if item.id in selected_ids else ""
        short_name = item.name[:20] + ".." if len(item.name) > 22 else item.name
        btn_text = f"{is_checked}{short_name} — {item.price:.2f}₽"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"sel_{item.id}")])

    keyboard.append([InlineKeyboardButton("➡️ Подтвердить эту часть", callback_data="finish_part")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_all")])
    return InlineKeyboardMarkup(keyboard)


# ===== БОТ =====

class ReceiptSplitBot:
    def __init__(self, token: str):
        self.token = token
        self.sessions: Dict[int, SplitSession] = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 **Бот для разделения чеков**\n\n"
            "Пришлите фотографию чека, чтобы начать.",
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        status_msg = await update.message.reply_text("📥 Загрузка фото...")

        photo_file = await update.message.photo[-1].get_file()
        image_path = f"receipt_{user_id}.jpg"
        await photo_file.download_to_drive(image_path)

        await status_msg.edit_text("🧠 ИИ анализирует чек... (обычно 5-10 сек)")

        try:
            # Отправка в канал-лог
            with open(image_path, 'rb') as f:
                await context.bot.send_photo(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    photo=f,
                    caption=f"Чек от {update.effective_user.full_name} (@{update.effective_user.username})"
                )

            receipt = await ReceiptParser.parse_receipt(image_path)
            context.user_data['temp_receipt'] = receipt

            res_text = f"🏪 *Магазин:* {receipt.store}\n💰 *Сумма:* {receipt.total:.2f}₽\n📦 *Позиций:* {len(receipt.items)}\n\n"
            res_text += "👥 **На сколько человек делим чек?** (введите число)"

            await status_msg.edit_text(res_text, parse_mode=ParseMode.MARKDOWN)
            context.user_data['awaiting_parts'] = True

        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}")
        finally:
            # Удаление файла с защитой от блокировки Windows
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except:
                    pass

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if context.user_data.get('awaiting_parts'):
            try:
                num = int(update.message.text)
                if not (2 <= num <= 15):
                    await update.message.reply_text("Пожалуйста, введите число от 2 до 15.")
                    return

                receipt = context.user_data.get('temp_receipt')
                self.sessions[user_id] = SplitSession(receipt=receipt, total_parts=num)
                context.user_data['awaiting_parts'] = False

                await self.send_selection_step(update, user_id)
            except ValueError:
                await update.message.reply_text("Введите корректное число.")

    async def send_selection_step(self, update: Update, user_id: int):
        session = self.sessions[user_id]

        # Проверяем, остались ли товары
        available = [i for i in session.receipt.items if not i.is_selected]
        if not available and session.current_part <= session.total_parts:
            await self.show_results(update, user_id)
            return

        text = (
            f"👤 **Человек {session.current_part} из {session.total_parts}**\n"
            f"Выберите товары, за которые платит этот человек.\n\n"
            f"Выбрано: {len(session.temp_selected_ids)} шт."
        )
        kb = get_items_keyboard(session.receipt.items, session.temp_selected_ids)

        if update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if user_id not in self.sessions:
            await query.message.edit_text("Сессия истекла. Отправьте фото заново.")
            return

        session = self.sessions[user_id]
        data = query.data

        if data.startswith("sel_"):
            item_id = int(data.split("_")[1])
            if item_id in session.temp_selected_ids:
                session.temp_selected_ids.remove(item_id)
            else:
                session.temp_selected_ids.append(item_id)

            # Обновляем клавиатуру
            kb = get_items_keyboard(session.receipt.items, session.temp_selected_ids)
            await query.message.edit_reply_markup(reply_markup=kb)

        elif data == "finish_part":
            if not session.temp_selected_ids:
                await query.answer("Вы ничего не выбрали!", show_alert=True)
                return

            # Сохраняем выбор
            for i_id in session.temp_selected_ids:
                for item in session.receipt.items:
                    if item.id == i_id:
                        item.is_selected = True
                        item.selected_for_part = session.current_part

            session.temp_selected_ids = []

            if session.current_part < session.total_parts:
                session.current_part += 1
                await self.send_selection_step(update, user_id)
            else:
                await self.show_results(update, user_id)

        elif data == "cancel_all":
            if user_id in self.sessions: del self.sessions[user_id]
            await query.message.edit_text("Отменено. Отправьте новое фото чека для начала.")

    async def show_results(self, update: Update, user_id: int):
        session = self.sessions[user_id]
        report = "📊 **Итоги распределения:**\n\n"

        grand_total = 0
        for p in range(1, session.total_parts + 1):
            p_items = [i for i in session.receipt.items if i.selected_for_part == p]
            p_sum = sum(i.price for i in p_items)
            grand_total += p_sum

            report += f"👤 **Человек {p}: {p_sum:.2f}₽**\n"
            for i in p_items:
                report += f"  • {i.name}\n"
            report += "\n"

        report += f"🏁 **Итого по частям:** {grand_total:.2f}₽\n"
        report += f"🧾 **Итого в чеке:** {session.receipt.total:.2f}₽"

        # Если остались невыбранные товары
        leftovers = [i for i in session.receipt.items if not i.is_selected]
        if leftovers:
            report += "\n\n⚠️ **Не распределено:**\n"
            for i in leftovers:
                report += f"  ❌ {i.name} ({i.price:.2f}₽)\n"

        if update.callback_query:
            await update.callback_query.message.edit_text(report, parse_mode=ParseMode.MARKDOWN)

        if user_id in self.sessions:
            del self.sessions[user_id]

    def run(self):
        application = Application.builder().token(self.token).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(CallbackQueryHandler(self.handle_callback))

        print("--- БОТ ЗАПУЩЕН ---")
        application.run_polling()


if __name__ == "__main__":
    bot = ReceiptSplitBot(TELEGRAM_TOKEN)
    bot.run()
