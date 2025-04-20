import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN')
AUTHORIZED_USERS = [6037372226]  # Ваш ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Бот запущен и работает!")

def run_bot():
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Регистрация команд
        application.add_handler(CommandHandler("start", start))
        # Добавьте другие обработчики здесь
        
        # Создаем новый event loop для этого процесса
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(application.run_polling())
    except Exception as e:
        print(f"Ошибка бота: {e}")
