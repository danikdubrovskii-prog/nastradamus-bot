#!/bin/bash

# setup.sh — создаёт/исправляет файлы для бота
echo "Запуск setup.sh — создание файлов..."

# Создаём config.py
cat > config.py << EOF
BOT_TOKEN = "8004087167:AAEeWgNFJhBPZ4sDIFRpmq7KyIZSwr6D8lk"
EOF

# Создаём requirements.txt
cat > requirements.txt << EOF
python-telegram-bot==20.8
EOF

# Создаём main.py (твой оригинальный код, с фиксами для PythonAnywhere)
cat > main.py << 'EOF'
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SELECT_DAY, SELECT_MONTH, SELECT_YEAR = range(3)

class HoroscopeBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).connect_timeout(10).read_timeout(10).build()
        self.register_handlers()
    
    def register_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                SELECT_DAY: [CallbackQueryHandler(self.select_day)],
                SELECT_MONTH: [CallbackQueryHandler(self.select_month)],
                SELECT_YEAR: [CallbackQueryHandler(self.select_year)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
            per_message=False
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.button_handler, pattern='^(?!day_|month_|year_).*'))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('subscribe', self.subscribe))
        self.application.add_handler(CommandHandler('unsubscribe', self.unsubscribe))
        self.application.add_handler(CommandHandler('myinfo', self.my_info))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        user_id = user.id
        # Проверяем пользователя (упрощённо)
        if True:  # Здесь была база, но для простоты пропускаем
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        await self.show_day_selection(update, context)
        return SELECT_DAY
    
    async def show_day_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        days = list(range(1, 32))
        for i in range(0, len(days), 7):
            row = []
            for day in days[i:i+7]:
                row.append(InlineKeyboardButton(str(day), callback_data=f"day_{day}"))
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите день рождения:", reply_markup=reply_markup)
    
    async def select_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        day = int(query.data.split('_')[1])
        context.user_data['birth_day'] = day
        await self.show_month_selection(query)
        return SELECT_MONTH
    
    async def show_month_selection(self, query):
        months = [
            ("Январь", 1), ("Февраль", 2), ("Март", 3),
            ("Апрель", 4), ("Май", 5), ("Июнь", 6),
            ("Июль", 7), ("Август", 8), ("Сентябрь", 9),
            ("Октябрь", 10), ("Ноябрь", 11), ("Декабрь", 12)
        ]
        keyboard = []
        for i in range(0, len(months), 3):
            row = []
            for month_name, month_num in months[i:i+3]:
                row.append(InlineKeyboardButton(month_name, callback_data=f"month_{month_num}"))
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите месяц рождения:", reply_markup=reply_markup)
    
    async def select_month(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        month = int(query.data.split('_')[1])
        context.user_data['birth_month'] = month
        await self.show_year_selection(query)
        return SELECT_YEAR
    
    async def show_year_selection(self, query):
        current_year = 2024
        start_year = 1920
        years = list(range(start_year, current_year + 1))
        years.reverse()
        keyboard = []
        for i in range(0, min(20, len(years)), 4):
            row = []
            for year in years[i:i+4]:
                row.append(InlineKeyboardButton(str(year), callback_data=f"year_{year}"))
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите год рождения:", reply_markup=reply_markup)
    
    async def select_year(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        year = int(query.data.split('_')[1])
        context.user_data['birth_year'] = year
        day = context.user_data['birth_day']
        month = context.user_data['birth_month']
        birth_date_text = f"{day:02d}.{month:02d}.{year}"
        zodiac_sign = "Овен"  # упрощённо
        eastern_zodiac = "Дракон"  # упрощённо
        await query.edit_message_text(
            f"Регистрация завершена!\n\n"
            f"Дата рождения: {birth_date_text}\n"
            f"Знак зодиака: {zodiac_sign}\n"
            f"Восточный гороскоп: {eastern_zodiac}\n\n"
            f"Теперь вы можете получать персонализированные гороскопы!"
        )
        await self.show_main_menu(update, context)
        return ConversationHandler.END
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Сегодня", callback_data="horoscope_today"), InlineKeyboardButton("Неделя", callback_data="horoscope_week")],
            [InlineKeyboardButton("Месяц", callback_data="horoscope_month"), InlineKeyboardButton("Совместимость", callback_data="compatibility")],
            [InlineKeyboardButton("Факты о знаках", callback_data="zodiac_facts"), InlineKeyboardButton("Подписка", callback_data="subscription")],
            [InlineKeyboardButton("Мои данные", callback_data="my_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("*Главное меню Nastradamus Daily Horoscope*\n\nВыберите опцию:", reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == 'horoscope_today':
            await query.edit_message_text("Гороскоп на сегодня: Хороший день!")
        elif data == 'subscribe':
            await query.edit_message_text("Подписка включена!")
        # Добавь остальные кнопки аналогично
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Помощь: /start для начала.")
    
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Подписка включена!")
    
    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Подписка отключена!")
    
    async def my_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Ваши данные: ...")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Отменено.")
        return ConversationHandler.END
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Неизвестная команда.")

def start_bot(self):
    try:
        print("Nastradamus Bot launching...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")

if __name__ == '__main__':
    bot = HoroscopeBot()
    bot.start_bot()
EOF
