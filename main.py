> …:
import asyncio
import json
import aiohttp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, JobQueue
)
from datetime import datetime

TOKEN = "8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA"

user_data = {}
CURRENCIES = ["USDT", "BTC", "TON", "ETH", "DAI", "TRX", "SOL", "BUSD", "XRP", "SHIB"]
CHECK_INTERVAL = 300  # 5 минут

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот работает!\n\n"
        "Команды:\n"
        "/budget 10000 — установить бюджет\n"
        "/cancel — отменить бюджет\n"
        "/bank Kaspi — фильтр по банку (Kaspi, Halyk, БЦК)\n"
        "/bank all — показать все банки\n"
        "/spread 1 10 — фильтр по спреду в % (от и до)\n"
        "/currency — отслеживаемые валюты\n"
        "/status — текущие параметры\n"
        "/check — сразу проверить выгодные сделки\n"
        "/help — список команд"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        uid = update.effective_user.id
        user_data[uid] = user_data.get(uid, {})
        user_data[uid]["budget"] = amount
        await update.message.reply_text(f"Бюджет установлен: {amount} ₸")
    except:
        await update.message.reply_text("Пример: /budget 10000")

async def cancel_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_data and "budget" in user_data[uid]:
        del user_data[uid]["budget"]
        await update.message.reply_text("Бюджет отменён.")
    else:
        await update.message.reply_text("Бюджет не установлен.")

async def set_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bank = context.args[0].capitalize() if context.args else "All"
    if bank in ["Kaspi", "Halyk", "Бцк", "All"]:
        user_data[uid] = user_data.get(uid, {})
        user_data[uid]["bank"] = bank
        await update.message.reply_text(f"Банк установлен: {bank}")
    else:
        await update.message.reply_text("Доступные банки: Kaspi, Halyk, БЦК или all")

async def set_spread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = update.effective_user.id
        min_spread = float(context.args[0])
        max_spread = float(context.args[1])
        user_data[uid] = user_data.get(uid, {})
        user_data[uid]["spread"] = (min_spread, max_spread)
        await update.message.reply_text(f"Фильтр спреда установлен: от {min_spread}% до {max_spread}%")
    except:
        await update.message.reply_text("Пример: /spread 1 10")

async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отслеживаемые валюты: " + ", ".join(CURRENCIES))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = user_data.get(uid, {})
    await update.message.reply_text(
        f"Текущие параметры:\n"
        f"Бюджет: {u.get('budget', 'не установлен')}\n"
        f"Банк: {u.get('bank', 'все')}\n"
        f"Спред: {u.get('spread', 'от 5% по умолчанию')}"
    )

async def check_bybit(context: ContextTypes.DEFAULT_TYPE):
    url = "https://api2.bybit.com/fiat/otc/item/online"
    async with aiohttp.ClientSession() as session:
        for uid in user_data:
            for side in ["BUY", "SELL"]:
                for currency in CURRENCIES:
                    payload = {
                        "userId": "",
                        "tokenId": currency,
                        "currencyId": "KZT",
                        "payment": [],
                        "side": side,
                        "size": "",
                        "page": 1,
                        "rows": 5,
                        "amount": "",
                        "authMaker": False
                    }

> …:
bank_filter = user_data[uid].get("bank", None)
                    if bank_filter and bank_filter != "All":
                        payload["payment"] = [bank_filter]
                    try:
                        async with session.post(url, json=payload) as resp:
                            data = await resp.json()
                            items = data.get("result", {}).get("items", [])
                            if len(items) >= 2:
                                price1 = float(items[0]["price"])
                                price2 = float(items[1]["price"])
                                spread = abs(price1 - price2)
                                spread_percent = (spread / price2) * 100
                                min_s, max_s = user_data[uid].get("spread", (5, 100))
                                if min_s <= spread_percent <= max_s:
                                    msg = (
                                        f"Валюта: {currency}\n"
                                        f"Тип: {'Покупка' if side == 'BUY' else 'Продажа'}\n"
                                        f"Цена 1: {price1} ₸\n"
                                        f"Цена 2: {price2} ₸\n"
                                        f"Спред: {spread:.2f} ₸ ({spread_percent:.2f}%)\n"
                                        f"Банк: {bank_filter or 'Все'}"
                                    )

                                    # расчет по бюджету
                                    budget = user_data[uid].get("budget", None)
                                    if budget:
                                        quantity = round(budget / price1, 4)
                                        msg += f"\n\nУ тебя бюджет: {budget} ₸\n"
                                        msg += f"Ты можешь {'купить' if side == 'BUY' else 'продать'}: {quantity} {currency}"

                                    msg += f"\nВремя: {datetime.now().strftime('%H:%M:%S')}"
                                    await context.bot.send_message(chat_id=uid, text=msg)
                    except Exception as e:
                        print(f"Ошибка при получении данных: {e}")

async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    class DummyContext:
        bot = context.bot

    await check_bybit(DummyContext())
    await update.message.reply_text("Проверка завершена.")

async def init_job_queue(app):
    app.job_queue.run_repeating(check_bybit, interval=CHECK_INTERVAL, first=5)

if name == "__main__":
    app = ApplicationBuilder().token(TOKEN).post_init(init_job_queue).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("budget", set_budget))
    app.add_handler(CommandHandler("cancel", cancel_budget))
    app.add_handler(CommandHandler("bank", set_bank))
    app.add_handler(CommandHandler("spread", set_spread))
    app.add_handler(CommandHandler("currency", currency))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("check", check_now))
    app.add_handler(MessageHandler(filters.COMMAND, help_command))

    print("Бот запущен с автообновлением...")
    app.run_polling()
