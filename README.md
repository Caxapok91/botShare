# 🤖 Receipt Split Bot

**Telegram бот для разделения чеков между друзьями с ИИ-распознаванием**

[![Telegram](https://img.shields.io/badge/Telegram-@YourBot-blue?style=flat-square&logo=telegram)](https://t.me/your_bot)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?style=flat-square&logo=railway)](https://railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![Gemini](https://img.shields.io/badge/Powered%20by-Gemini-4285F4?style=flat-square&logo=google)](https://deepmind.google/technologies/gemini/)

---

## 📱 Что умеет бот

| Функция | Описание |
|---------|----------|
| 🧠 **Умное распознавание** | ИИ (Google Gemini) читает чек и автоматически находит все позиции |
| 📦 **Поштучное разделение** | "Тартар 4 шт" → 4 отдельные кнопки, каждую можно отдать разному человеку |
| 👥 **Любое количество людей** | Разделите чек на 2, 5 или 15 человек |
| 💰 **Автоматический подсчёт** | Бот сам посчитает сумму для каждого |
| ✅ **Простой интерфейс** | Инлайн-кнопки — всё в одном чате |
| 🔒 **Безопасно** | Ваши данные не хранятся, токены в переменных окружения |

---

## 🎬 Как пользоваться

```mermaid
flowchart LR
    A[📸 Отправить фото чека] --> B[🧠 ИИ распознаёт позиции]
    B --> C[👥 Ввести количество человек]
    C --> D[✅ Выбрать товары для каждого]
    D --> E[📊 Получить итоги]
Пошаговая инструкция
Отправьте боту фото чека (сфотографируйте чётко, при хорошем освещении)

Дождитесь распознавания — бот покажет все найденные позиции

Введите количество человек — на скольких делим чек

Для каждого человека выбирайте товары — просто нажимайте на кнопки

Нажмите "Подтвердить эту часть" — бот покажет итог

🖼️ Пример работы
text
📸 Отправка фото чека
    ↓
🏪 Магазин: Перекрёсток
💰 Сумма: 1 234.56 ₽
📦 Позиций: 8 шт.

👥 На сколько человек делим чек?
    ↓
👤 Человек 1 из 3
Выберите товары, за которые платит этот человек.

[🥛 Молоко — 79.99₽]  [🍞 Хлеб — 45.50₽]
[🧀 Сыр — 199.99₽]    [🥩 Мясо — 345.00₽]
[🥦 Брокколи — 89.90₽]

➡️ Подтвердить эту часть
🛠️ Технологии
Компонент	Технология
Язык	Python 3.11
Бот-фреймворк	python-telegram-bot 20.7
ИИ распознавание	Google Gemini API
Обработка изображений	Pillow
Хостинг	Railway
🚀 Быстрый старт для разработки
Локальный запуск
bash
# Клонировать репозиторий
git clone https://github.com/ваш-аккаунт/receipt-split-bot.git
cd receipt-split-bot

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать файл с токенами
echo "TELEGRAM_TOKEN=ваш_токен" > .env
echo "GEMINI_API_KEY=ваш_ключ" >> .env

# Запустить бота
python main.py
Переменные окружения
Переменная	Описание
TELEGRAM_TOKEN	Токен бота от @BotFather
GEMINI_API_KEY	API ключ от Google AI Studio
📁 Структура проекта
text
receipt-split-bot/
├── main.py              # Основной код бота
├── requirements.txt     # Зависимости
├── runtime.txt          # Версия Python
├── README.md            # Этот файл
└── .gitignore           # Игнорируемые файлы
🔐 Безопасность
Токены хранятся в переменных окружения, не в коде

Файл tok.py добавлен в .gitignore

Используется .env для локальной разработки

📝 Лицензия
MIT © 2026

🙏 Благодарности
Google Gemini — за мощное ИИ-распознавание

python-telegram-bot — за отличный фреймворк

Railway — за удобный хостинг

📞 Контакты
По вопросам и предложениям: @ваш_телеграм

⭐ Поставьте звезду, если проект полезен!

text

## 📝 Как использовать

1. **Создайте файл `README.md`** в корне вашего репозитория
2. **Скопируйте текст** выше в этот файл
3. **Замените ссылки** на свои:
   - `https://t.me/your_bot` → ссылка на вашего бота
   - `@YourBot` → username вашего бота
   - `@ваш_телеграм` → ваш Telegram
   - `ваш-аккаунт` → ваш GitHub username

4. **Залейте на GitHub**:
```bash
git add README.md
git commit -m "Add beautiful README"
git push
