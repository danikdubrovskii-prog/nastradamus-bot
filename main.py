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
BOT_TOKEN = "8004087167:AAEeWgNFJhBPZ4sDIFRpmq7KyIZSwr6D8lk"
logging.basicConfig(level=logging.INFO)

# Parse mode через DefaultBotProperties (новый способ в aiogram 3.13.1)
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

def add_user(user_id, birth_date, zodiac, eastern):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users (user_id, birth_date, zodiac, eastern, lang, subscribed) VALUES (?, ?, ?, ?, "ru", 0)',
              (user_id, birth_date, zodiac, eastern))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def set_lang(user_id, lang):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET lang = ? WHERE user_id = ?', (lang, user_id))
    conn.commit()
    conn.close()

def toggle_subscribe(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET subscribed = 1 - subscribed WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_subscribed_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE subscribed = 1')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

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

def get_fortune():
    return random.choice([
        "Сегодня удача в мелочах.",
        "Не бойтесь рисковать — звёзды на вашей стороне.",
        "Любовь стучится в дверь. Откройте.",
        "День идеален для новых начинаний."
    ])

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

def years_kb():
    kb = InlineKeyboardMarkup(row_width=4)
    for y in range(2005, 1919, -1):
        kb.add(InlineKeyboardButton(str(y), callback_data=f"year_{y}"))
        if len(kb.inline_keyboard[-1]) == 4:
            break
    return kb

def main_menu(lang='ru'):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Сегодня" if lang=='ru' else "Today", callback_data="today"))
    kb.add(InlineKeyboardButton("Фортуна" if lang=='ru' else "Fortune", callback_data="fortune"))
    kb.add(InlineKeyboardButton("Язык / Lang", callback_data="lang"))
    kb.add(InlineKeyboardButton("Подписка" if lang=='ru' else "Subscribe", callback_data="subscribe"))
    return kb

# === РЕГИСТРАЦИЯ ===
@dp.message(Command("start"))
async def start(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        lang = user[4] if len(user) > 4 else 'ru'
        await message.answer("Главное меню:", reply_markup=main_menu(lang))
        return
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
    await call.message.edit_text("Выберите год:", reply_markup=years_kb())

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

    add_user(call.from_user.id, f"{day}.{month}.{year}", zodiac, eastern)

    await call.message.edit_text(
        f"Регистрация завершена!\n"
        f"Дата: {day}.{month}.{year}\n"
        f"Знак: {zodiac}\n"
        f"Восточный: {eastern}"
    )
    await asyncio.sleep(1)
    await call.message.answer("Главное меню:", reply_markup=main_menu())

# === МЕНЮ ===
@dp.callback_query(lambda c: c.data == "today")
async def today_horoscope(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    if user:
        await call.message.edit_text(f"Гороскоп на сегодня для {user[2]}:\n\nХороший день!")

@dp.callback_query(lambda c: c.data == "fortune")
async def fortune(call: types.CallbackQuery):
    await call.message.edit_text(f"Колесо Фортуны:\n\n{get_fortune()}")
    await asyncio.sleep(2)
    lang = get_user(call.from_user.id)[4] if get_user(call.from_user.id) else 'ru'
    await call.message.answer("Меню:", reply_markup=main_menu(lang))

@dp.callback_query(lambda c: c.data == "lang")
async def change_lang(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    new_lang = 'en' if (user and user[4] == 'ru') else 'ru'
    set_lang(call.from_user.id, new_lang)
    await call.message.edit_text(f"Язык: {new_lang.upper()}")
    await asyncio.sleep(1)
    await call.message.answer("Menu:", reply_markup=main_menu(new_lang))

@dp.callback_query(lambda c: c.data == "subscribe")
async def subscribe_btn(call: types.CallbackQuery):
    toggle_subscribe(call.from_user.id)
    lang = get_user(call.from_user.id)[4] if get_user(call.from_user.id) else 'ru'
    status = "включена" if get_user(call.from_user.id)[5] else "отключена"
    await call.message.edit_text(f"Подписка {status}!")
    await asyncio.sleep(1)
    await call.message.answer("Меню:", reply_markup=main_menu(lang))

# === КОМАНДЫ ===
@dp.message(Command("subscribe"))
async def subscribe_cmd(message: types.Message):
    toggle_subscribe(message.from_user.id)
    await message.answer("Подписка включена!")

@dp.message(Command("unsubscribe"))
async def unsubscribe_cmd(message: types.Message):
    toggle_subscribe(message.from_user.id)
    await message.answer("Подписка отключена!")

@dp.message(Command("myinfo"))
async def myinfo(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        await message.answer(f"Ваши данные:\nДата: {user[1]}\nЗнак: {user[2]}\nВосточный: {user[3]}")
    else:
        await message.answer("Нет данных. /start")

# === РАССЫЛКА ===
async def daily_horoscope():
    users = get_subscribed_users()
    for uid in users:
        try:
            user = get_user(uid)
            await bot.send_message(uid, f"Доброе утро!\nГороскоп для {user[2]}: Хороший день!")
        except:
            pass

# === ЗАПУСК ===
async def on_startup(dispatcher):
    init_db()
    scheduler.add_job(daily_horoscope, 'cron', hour=8, minute=0)
    scheduler.start()
    print("Бот запущен...")

if __name__ == '__main__':
    dp.startup.register(on_startup)
    asyncio.run(dp.start_polling(bot))
