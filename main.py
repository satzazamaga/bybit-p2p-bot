# main.py

import asyncio
import logging
from aiohttp import ClientSession
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.ext import Defaults
from datetime import datetime

TOKEN = "8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA"
CHECK_INTERVAL = 300  # каждые 5 минут

user_data = {}
tracked_currencies = ["USDT", "BTC", "TON", "ETH", "BNB", "SOL", "TRX", "DOGE", "SHIB", "DAI"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_offers(session, currency, side, uid):
    url = f"https://api2.bybit.com/fiat/otc/item/online"
    payload = {
        "userId": "",
        "tokenId": currency,
        "currencyId": "KZT",
        "payment": [],
        "side": side,
        "size": "",
        "page": 1,
        "amount": "",
        "authMaker": False,
        "rows": 10
    }

    bank_filter = user_data[uid].get("bank", None)
    if bank_filter and bank_filter != "All":
        payload["payment"] = [bank_filter]

    try:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return data.get("result", {}).get("items", [])
    except Exception as e:
        logger.error(f"Ошибка при получении офферов: {e}")
        return []

def calculate_spread(buy_price, sell_price):
    try:
        return round((sell_price - buy_price) / buy_price * 100, 2)
    except ZeroDivisionError:
        return 0

def check_spread_valid(spread, uid):
    user_spread = user_data[uid].get("spread", (5.0, 100.0))
    return user_spread[0] <= spread <= user_spread[1]

async def check_bybit_all_users(app):
    async with ClientSession() as session:
        for uid in user_data:
            message_lines = []
            for currency in tracked_currencies:
                buy_offers = await fetch_offers(session, currency, "Buy", uid)
                sell_offers = await fetch_offers(session, currency, "Sell", uid)

                if buy_offers and sell_offers:
                    best_buy = float(buy_offers[0]['adv']['price'])
                    best_sell = float(sell_offers[0]['adv']['price'])
                    spread = calculate_spread(best_buy, best_sell)

                    if check_spread_valid(spread, uid):
                        message_lines.append(
                            f"{currency}: Спред {spread}%\n"
                            f"Покупка: {best_buy} ₸\nПродажа: {best_sell} ₸\n"
                            f"{'-'*30}"
                        )

            if message_lines:
                await app.bot.send_message(chat_id=uid, text="\n".join(message_lines))
            else:
                await app.bot.send_message(chat_id=uid, text="Нет подходящих предложений")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    user_data[uid] = {"spread": (5.0, 100.0)}
    await update.message.reply_text("Бот запущен. Используй /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start – Запуск бота\n"
        "/check – Проверка вручную\n"
        "/budget [сумма] – Установить бюджет\n"
        "/cancel – Отменить бюджет\n"
        "/bank [Kaspi|Halyk|БЦК|All] – Фильтр по банку\n"
        "/status – Показать текущие настройки\n"
        "/spread [от] [до] – Задать спред в %\n"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    await update.message.reply_text("Проверка предложений...")
    await check_bybit_all_users(context.application)

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    try:
        amount = float(context.args[0])
        user_data.setdefault(uid, {})["budget"] = amount
        await update.message.reply_text(f"Бюджет установлен: {amount} ₸")
    except:
        await update.message.reply_text("Используй: /budget 10000")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    user_data.get(uid, {}).pop("budget", None)
    await update.message.reply_text("Бюджет отменён.")

async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("Укажи банк: /bank Kaspi, /bank Halyk, /bank БЦК, /bank All")
        return
    bank = context.args[0]
    user_data.setdefault(uid, {})["bank"] = bank
    await update.message.reply_text(f"Фильтр по банку: {bank}")

async def spread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    try:
        from_val = float(context.args[0])
        to_val = float(context.args[1])
        user_data.setdefault(uid, {})["spread"] = (from_val, to_val)
        await update.message.reply_text(f"Спред фильтр установлен: от {from_val}% до {to_val}%")
    except:
        await update.message.reply_text("Используй: /spread 1.0 10.0")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    data = user_data.get(uid, {})
    budget = data.get("budget", "Не установлен")
    bank = data.get("bank", "All")
    spread = data.get("spread", (5.0, 100.0))
    await update.message.reply_text(
        f"Текущий статус:\n"
        f"Бюджет: {budget} ₸\n"
        f"Банк: {bank}\n"
        f"Спред: от {spread[0]}% до {spread[1]}%"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).defaults(Defaults(parse_mode="HTML")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("budget", budget))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("spread", spread))
    app.add_handler(CommandHandler("status", status))

    job_queue = app.job_queue
    job_queue.run_repeating(lambda ctx: asyncio.create_task(check_bybit_all_users(app)), interval=CHECK_INTERVAL)

    app.run_polling()
