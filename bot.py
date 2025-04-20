import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN')
AUTHORIZED_USERS = [6037372226]  # Ваш ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Бот запущен!")

async def run_bot():
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        # Добавьте другие обработчики здесь
        
        await application.run_polling()
    except Exception as e:
        logging.critical(f"Ошибка бота: {e}")
        raise
