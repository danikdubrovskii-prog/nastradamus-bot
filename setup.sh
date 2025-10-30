#!/bin/bash

# setup.sh — создаёт все нужные файлы для бота
echo "Запуск setup.sh — создаю файлы..."

# === 1. Создаём requirements.txt ===
cat > requirements.txt << 'EOF'
aiogram==3.13.1
apscheduler==3.11.0
EOF

# === 2. Создаём config.py (токен бота) ===
cat > config.py << 'EOF'
BOT_TOKEN = "8004087167:AAEeWgNFJhBPZ4sDIFRpmq7KyIZSwr6D8lk"
EOF

# === 3. Создаём main.py (рабочий бот на aiogram 3.13.1) ===
cat > main.py << 'EOF'
import asyncio
import logging
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === КОНФИГ ===
from config import BOT_TOKEN
logging.basicConfig(level=logging.INFO)

default = DefaultBotProperties(parse_mode='HTML')
bot = Bot(token=BOT_TOKEN, default=default)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# === БАЗА ДАННЫХ ===
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            birth_date TEXT,
            zodiac TEXT,
            eastern TEXT,
            lang TEXT DEFAULT 'ru',
            subscribed INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# === ГОРОСКОП ===
def get_zodiac(day, month):
    if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "Овен"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "Телец"
    if (month == 5 and day >= 21) or (month == 6 and day <= 21): return "Близнецы"
    if (month == 6 and day >= 22) or (month == 7 and day <= 22): return "Рак"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "Лев"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "Дева"
    if (month == 9 and day >= 23) or (month == 10 and day <= 23): return "Весы"
    if (month == 10 and day >= 24) or (month == 11 and day <= 22): return "Скорпион"
    if (month == 11 and day >= 23) or (month == 12 and day <= 21): return "Стрелец"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "Козерог"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "Водолей"
    return "Рыбы"

def get_eastern(year):
    animals = ["Обезьяна", "Петух", "Собака", "Свинья", "Крыса", "Бык", "Тигр", "Кролик", "Дракон", "Змея", "Лошадь", "Коза"]
    return animals[(year - 1900) % 12]

# === КЛАВИАТУРЫ ===
def days_kb():
    kb = InlineKeyboardMarkup(row_width=7)
    for d in range(1, 32):
        kb.add(InlineKeyboardButton(str(d), callback_data=f"day_{d}"))
    return kb

def months_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    months = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    for i, m in enumerate(months):
        kb.add(InlineKeyboardButton(m, callback_data=f"month_{i+1}"))
    return kb

def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Сегодня", callback_data="today"))
    kb.add(InlineKeyboardButton("Подписка", callback_data="subscribe"))
    return kb

# === РЕГИСТРАЦИЯ ===
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Выберите день рождения:", reply_markup=days_kb())

@dp.callback_query(lambda c: c.data and c.data.startswith('day_'))
async def select_day(call: types.CallbackQuery):
    day = call.data.split('_')[1]
    await dp.current_state(user=call.from_user.id).set_data({"day": day})
    await call.message.edit_text("Выберите месяц:", reply_markup=months_kb())

@dp.callback_query(lambda c: c.data and c.data.startswith('month_'))
async def select_month(call: types.CallbackQuery):
    state = dp.current_state(user=call.from_user.id)
    data = await state.get_data()
    data["month"] = call.data.split('_')[1]
    await state.set_data(data)
    await call.message.edit_text("Выберите год (1920–2005):", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(str(y), callback_data=f"year_{y}")] for y in range(2005, 1919, -1)]
    ))

@dp.callback_query(lambda c: c.data and c.data.startswith('year_'))
async def select_year(call: types.CallbackQuery):
    state = dp.current_state(user=call.from_user.id)
    data = await state.get_data()
    data["year"] = call.data.split('_')[1]
    await state.finish()

    day = int(data["day"])
    month = int(data["month"])
    year = int(data["year"])
    zodiac = get_zodiac(day, month)
    eastern = get_eastern(year)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users (user_id, birth_date, zodiac, eastern) VALUES (?, ?, ?, ?)',
              (call.from_user.id, f"{day}.{month}.{year}", zodiac, eastern))
    conn.commit()
    conn.close()

    await call.message.edit_text(
        f"Регистрация завершена!\n"
        f"Дата: {day}.{month}.{year}\n"
        f"Знак: {zodiac}\n"
        f"Восточный: {eastern}"
    )
    await asyncio.sleep(1)
    await call.message.answer("Меню:", reply_markup=main_menu())

# === МЕНЮ ===
@dp.callback_query(lambda c: c.data == "today")
async def today_horoscope(call: types.CallbackQuery):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT zodiac FROM users WHERE user_id = ?', (call.from_user.id,))
    row = c.fetchone()
    conn.close()
    if row:
        await call.message.edit_text(f"Гороскоп для {row[0]}:\n\nХороший день!")

@dp.callback_query(lambda c: c.data == "subscribe")
async def subscribe(call: types.CallbackQuery):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET subscribed = 1 WHERE user_id = ?', (call.from_user.id,))
    conn.commit()
    conn.close()
    await call.message.edit_text("Подписка включена!")
    await asyncio.sleep(1)
    await call.message.answer("Меню:", reply_markup=main_menu())

# === ЗАПУСК ===
async def on_startup(dispatcher):
    init_db()
    scheduler.add_job(lambda: print("Рассылка..."), 'cron', hour=8)
    scheduler.start()
    print("Бот запущен...")

if __name__ == '__main__':
    dp.startup.register(on_startup)
    asyncio.run(dp.start_polling(bot))
EOF

echo "setup.sh: все файлы созданы!"
EOF
