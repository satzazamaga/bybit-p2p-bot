from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = "8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA"
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для отслеживания выгодных P2P-сделок на Bybit.\n\n"
        "Вот список команд:\n"
        "/budget 10000 — установить бюджет\n"
        "/cancel — отменить бюджет\n"
        "/bank Kaspi — фильтр по банку (Kaspi, Halyk, БЦК)\n"
        "/bank all — показать все банки\n"
        "/status — текущие лучшие предложения\n"
        "/currency — список отслеживаемых валют\n"
        "/help — помощь"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# Команда /budget
async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        user_id = update.effective_user.id
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["budget"] = amount
        await update.message.reply_text(f"Бюджет установлен: {amount} ₸")
    except (IndexError, ValueError):
        await update.message.reply_text("Пример: /budget 10000")

# Команда /cancel
async def cancel_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and "budget" in user_data[user_id]:
        del user_data[user_id]["budget"]
        await update.message.reply_text("Бюджет отменён.")
    else:
        await update.message.reply_text("Бюджет ещё не установлен.")

# Команда /bank
async def set_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bank = context.args[0].capitalize()
        user_id = update.effective_user.id
        user_data[user_id] = user_data.get(user_id, {})
        if bank == "All":
            user_data[user_id]["bank"] = "all"
            await update.message.reply_text("Фильтр по банку отключён.")
        elif bank in ["Kaspi", "Halyk", "Бцк"]:
            user_data[user_id]["bank"] = bank
            await update.message.reply_text(f"Выбран банк: {bank}")
        else:
            await update.message.reply_text("Доступные банки: Kaspi, Halyk, БЦК")
    except IndexError:
        await update.message.reply_text("Пример: /bank Kaspi")

# Команда /currency
async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отслеживаемые валюты: USDT, BTC, TON. Скоро добавлю больше.")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    budget = user_data.get(user_id, {}).get("budget", "не установлен")
    bank = user_data.get(user_id, {}).get("bank", "все банки")

    await update.message.reply_text(
        f"Текущий статус:\n"
        f"Бюджет: {budget}\n"
        f"Банк: {bank}\n\n"
        f"(Пока что это тестовые данные. Скоро будет подключён реальный P2P API Bybit)"
    )

# Команда по умолчанию
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Введите /help для списка доступных.")

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("budget", set_budget))
    app.add_handler(CommandHandler("cancel", cancel_budget))
    app.add_handler(CommandHandler("bank", set_bank))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("currency", currency))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Бот запущен...")
    app.run_polling()
