
import logging
import os
import requests
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime
import asyncio

# Инициализация бота
API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройки пользователя
user_settings = {
    "budget": None,
    "bank": None,
    "watch_mode": True
}

CURRENCIES = ["USDT", "USDC", "BTC", "ETH", "TRX", "SOL", "XRP", "LTC", "DAI", "TUSD", "FDUSD"]
BANKS = ["Kaspi", "Halyk", "БЦК"]

# Получение P2P предложений с Bybit
async def get_p2p_offers():
    offers = []
    headers = {"Content-Type": "application/json"}
    for currency in CURRENCIES:
        try:
            response = requests.post(
                "https://api2.bybit.com/fiat/otc/item/online",
                json={
                    "userId": "",
                    "tokenId": currency,
                    "currencyId": "KZT",
                    "payment": [],
                    "side": "1",
                    "size": 10,
                    "page": 1
                },
                headers=headers,
                timeout=10
            )
            data = response.json()
            for item in data.get("result", {}).get("items", []):
                price = float(item["price"])
                bank = item["payments"][0]["paymentName"]
                if not user_settings["bank"] or bank.lower() == user_settings["bank"].lower():
                    offers.append((currency, price, bank))
        except Exception as e:
            logging.error(f"Ошибка при получении {currency}: {e}")
    return offers

# Генерация текста с предложениями
def generate_offer_text(offers):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [f"Выгодные предложения на {now}:"]
    for currency, price, bank in offers:
        lines.append(f"{currency} - {price} KZT [{bank}]")
    return "\n".join(lines)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Я бот для мониторинга выгодных предложений на Bybit P2P по тенге.")

@dp.message_handler(commands=['budget'])
async def set_budget(message: types.Message):
    try:
        budget = int(message.get_args())
        user_settings["budget"] = budget
        await message.answer(f"Бюджет установлен: {budget} тенге.")
    except:
        await message.answer("Укажи бюджет числом, например: /budget 10000")

@dp.message_handler(commands=['cancel'])
async def cancel_budget(message: types.Message):
    user_settings["budget"] = None
    await message.answer("Мониторинг по бюджету отменён.")

@dp.message_handler(commands=['bank'])
async def set_bank(message: types.Message):
    arg = message.get_args()
    if arg.lower() == "all":
        user_settings["bank"] = None
        await message.answer("Теперь отображаются предложения по всем банкам.")
    elif arg.capitalize() in BANKS:
        user_settings["bank"] = arg
        await message.answer(f"Теперь показываю предложения только по банку: {arg}")
    else:
        await message.answer("Банк не найден. Доступные: Kaspi, Halyk, БЦК, all")

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    offers = await get_p2p_offers()
    text = generate_offer_text(offers[:5])
    await message.answer(text)

# Отправка в фоне уведомлений
async def background_monitor():
    await bot.wait_until_ready()
    while True:
        if user_settings["watch_mode"]:
            offers = await get_p2p_offers()
            text = generate_offer_text(offers[:3])
            try:
                await bot.send_message(chat_id=os.getenv("USER_ID"), text=text)
            except Exception as e:
                logging.error(f"Ошибка отправки уведомления: {e}")
        await asyncio.sleep(300)  # каждые 5 минут

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(background_monitor())
    executor.start_polling(dp, skip_updates=True)
