import asyncio
import logging
import sqlite3
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8004087167:AAEeWgNFJhBPZ4sDIFRpmq7KyIZSwr6D8lk"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# База данных
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, birth_date TEXT, zodiac TEXT, eastern TEXT, lang TEXT DEFAULT "ru", subscribed INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

def add_user(user_id, birth_date, zodiac, eastern):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, "ru", 0)', (user_id, birth_date, zodiac, eastern))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# Гороскоп
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

def get_fortune():
    return random.choice(["Удача в мелочах.", "Рискуй!", "Любовь рядом.", "Новый старт."])

# Клавиатуры
def days_kb():
    kb = InlineKeyboardMarkup(row_width=7)
    for d in range(1, 32): kb.add(InlineKeyboardButton(str(d), callback_data=f"day_{d}"))
    return kb

def months_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    months = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    for i, m in enumerate(months): kb.add(InlineKeyboardButton(m, callback_data=f"month_{i+1}"))
    return kb

def years_kb():
    kb = InlineKeyboardMarkup(row_width=4)
    for y in range(2005, 1919, -1): kb.add(InlineKeyboardButton(str(y), callback_data=f"year_{y}"))
    return kb

def main_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Сегодня", callback_data="today"))
    kb.add(InlineKeyboardButton("Фортуна", callback_data="fortune"))
    kb.add(InlineKeyboardButton("Язык", callback_data="lang"))
    return kb

# Хендлеры
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        await message.answer("Меню:", reply_markup=main_kb())
        return
    await message.answer("День рождения:", reply_markup=days_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('day_'))
async def day(call: types.CallbackQuery):
    day = call.data.split('_')[1]
    await call.message.edit_text("Месяц:", reply_markup=months_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('month_'))
async def month(call: types.CallbackQuery):
    month = call.data.split('_')[1]
    await call.message.edit_text("Год:", reply_markup=years_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('year_'))
async def year(call: types.CallbackQuery):
    year = call.data.split('_')[1]
    day = 15  # упрощённо
    month = 5  # упрощённо
    zodiac = get_zodiac(day, month)
    eastern = get_eastern(int(year))
    add_user(call.from_user.id, f"{day}.{month}.{year}", zodiac, eastern)
    await call.message.edit_text(f"Готово!\nЗнак: {zodiac}\nВосточный: {eastern}")
    await asyncio.sleep(1)
    await call.message.answer("Меню:", reply_markup=main_kb())

@dp.callback_query_handler(lambda c: c.data == "today")
async def today(call: types.CallbackQuery):
    await call.message.edit_text("Гороскоп: Хороший день!")

@dp.callback_query_handler(lambda c: c.data == "fortune")
async def fortune(call: types.CallbackQuery):
    await call.message.edit_text(f"Фортуна: {get_fortune()}")

@dp.message_handler(commands=['subscribe'])
async def sub(message: types.Message):
    toggle_subscribe(message.from_user.id)
    await message.answer("Подписка включена!")

if __name__ == '__main__':
    init_db()
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
