

import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA"

# Словарь для хранения бюджета пользователя
user_budget = {}

# Получение предложений с Bybit P2P
def get_bybit_offers():
    url = "https://api2.bybit.com/fiat/otc/item/online"
    params = {
        "userId": "",
        "tokenId": "USDT",
        "currencyId": "KZT",
        "payment": [],
        "side": "1",
        "size": "10",
        "page": "1"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=params, headers=headers)
        data = response.json()
        items = data.get("result", {}).get("items", [])
        result = ""
        for item in items[:3]:
            price = item["price"]
            bank = ", ".join(item["paymentMethods"])
            nick = item["nickName"]
            min_limit = item["minAmount"]
            max_limit = item["maxAmount"]
            result += "Продавец: {}\nБанк: {}\nКурс: {}₸\nЛимит: {}–{}₸\n\n".format(nick, bank, price, min_limit, max_limit)
        return result or "Нет доступных предложений."
    except Exception as e:
        return f"Ошибка при получении данных: {e}"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот для мониторинга выгодных предложений на Bybit P2P по тенге.")

def set_budget(update: Update, context: CallbackContext):
    try:
        budget = int(context.args[0])
        user_id = update.effective_user.id
        user_budget[user_id] = budget
        update.message.reply_text(f"Бюджет установлен: {budget}₸")
    except:
        update.message.reply_text("Пожалуйста, укажи бюджет: /budget 50000")

def info(update: Update, context: CallbackContext):
    offers = get_bybit_offers()
    update.message.reply_text(offers)

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("budget", set_budget))
    dp.add_handler(CommandHandler("info", info))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
