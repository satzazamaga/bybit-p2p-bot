from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

TOKEN = "8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA"

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Данные пользователей
user_data = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для отслеживания выгодных P2P-сделок на Bybit.\n"
        "Напиши /help чтобы узнать, что я умею."
    )

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Доступные команды:
/start — запуск бота
/help — список команд
/budget [сумма] — установить бюджет
/cancel — сбросить бюджет
/bank [Kaspi|Halyk|БЦК|all] — выбрать банк
/status — показать текущие курсы (пример)
/currency — показать отслеживаемые валюты
""")

# /budget
async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        try:
            amount = float(context.args[0])
            user_data.setdefault(user_id, {})["budget"] = amount
            await update.message.reply_text(f"Бюджет установлен: {amount} тг")
        except ValueError:
            await update.message.reply_text("Введите корректную сумму.")
    else:
        await update.message.reply_text("Пример: /budget 10000")

# /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and "budget" in user_data[user_id]:
        del user_data[user_id]["budget"]
        await update.message.reply_text("Бюджет сброшен.")
    else:
        await update.message.reply_text("Бюджет не был установлен.")

# /bank
async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.args:
        bank_name = context.args[0].lower()
        if bank_name in ['kaspi', 'halyk', 'бцк', 'all']:
            user_data.setdefault(user_id, {})["bank"] = bank_name
            await update.message.reply_text(f"Банк выбран: {bank_name.capitalize()}")
        else:
            await update.message.reply_text("Доступные банки: Kaspi, Halyk, БЦК, all.")
    else:
        await update.message.reply_text("Пример: /bank Kaspi")

# /currency
async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отслеживаемые валюты: USDT")

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Примерные фейковые данные (замени позже на реальные из Bybit API)
    await update.message.reply_text(
        "Пример предложения:\n\n"
        "Банк: Kaspi\n"
        "Курс: 477.5 тг\n"
        "Доступно: 1500 USDT\n"
        "Мин. сумма: 10 000 тг\n"
        "Время: 12:42"
    )

# Запуск приложения
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("budget", budget))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("currency", currency))
    app.add_handler(CommandHandler("status", status))

    print("Бот запущен...")
    app.run_polling()
