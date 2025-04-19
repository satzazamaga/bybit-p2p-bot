import os
import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from dotenv import load_dotenv  # Импорт для работы с .env файлами

# Загрузка переменных окружения из .env файла
load_dotenv()

# 🔐 Токен и настройки
API_TOKEN = os.getenv('API_TOKEN')  # Загрузка токена из переменной окружения
OWNER_ID = 5791850798

if API_TOKEN is None:
    raise ValueError("API_TOKEN is not set. Please set the API_TOKEN environment variable.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ⚖️ Настройки по умолчанию
min_filter_spread = 5
max_filter_spread = 50
currencies = ['USDT', 'BTC', 'TON']
banks = []
check_interval = 5  # минут
history_log = []
is_checking = False

# 🔹 Меню кнопок
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(
    KeyboardButton('📅 Статус'),
    KeyboardButton('📈 Запустить мониторинг'),
    KeyboardButton('⏹️ Остановить мониторинг'),
    KeyboardButton('📃 История'),
    KeyboardButton('⚖️ Установить фильтр'),
    KeyboardButton('💱 Изменить валюту'),
    KeyboardButton('🏛️ Изменить банки'),
    KeyboardButton('⏲️ Изменить интервал'),
    KeyboardButton('🔧 Помощь')
)

# ========== 🔧 Команды ==========

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🚀 Бот запущен! Используй кнопки ниже для управления:", reply_markup=menu)

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("""
ℹ️ Доступные команды:
/start — запустить бота
/status — текущие настройки
/set_filter [мин] [макс] — установить диапазон минимального и максимального спреда
/currencies [валюты] — изменить список валют
/banks [список банков] — изменить список банков
/interval [минуты] — изменить интервал проверки
/start_check — запустить проверку вручную
/stop_check — остановить проверку
/history — последние уведомления
/reset — сбросить все фильтры
/help — помощь
""", reply_markup=menu)

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    await message.answer(
        f"📊 Статус:\n\n🌐 Валюты: {', '.join(currencies)}\n"
        f"🔄 Минимальный спред: {min_filter_spread}₸\n"
        f"🔄 Максимальный спред: {max_filter_spread}₸\n"
        f"🏛️ Банки: {'все' if not banks else ', '.join(banks)}\n"
        f"⏰ Интервал: {check_interval} мин\n"
        f"📢 Мониторинг: {'ВКЛ' if is_checking else 'ВЫКЛ'}"
    )

@dp.message_handler(commands=['set_filter'])
async def set_filter_cmd(message: types.Message):
    global min_filter_spread, max_filter_spread
    try:
        args = message.get_args().split()
        if len(args) == 2:
            min_filter_spread = int(args[0])
            max_filter_spread = int(args[1])
            await message.answer(f"✅ Фильтр установлен: от {min_filter_spread}₸ до {max_filter_spread}₸")
        else:
            await message.answer("❌ Введите два числа: /set_filter <мин> <макс>")
    except ValueError:
        await message.answer("❌ Введите целые числа: /set_filter 5 50")

@dp.message_handler(commands=['currencies'])
async def set_currencies(message: types.Message):
    global currencies
    args = message.get_args().split()
    if args:
        currencies = args
        await message.answer(f"🌐 Валюты обновлены: {', '.join(currencies)}")
    else:
        await message.answer("Пример: /currencies USDT BTC")

@dp.message_handler(commands=['banks'])
async def set_banks(message: types.Message):
    global banks
    args = message.get_args().split()
    banks = args
    await message.answer(f"🏛️ Банки обновлены: {'все' if not banks else ', '.join(banks)}")

@dp.message_handler(commands=['interval'])
async def set_interval(message: types.Message):
    global check_interval
    try:
        value = int(message.get_args())
        check_interval = value
        await message.answer(f"⏰ Интервал обновлён: {check_interval} минут")
    except ValueError:
        await message.answer("❌ Укажите число: /interval 10")

@dp.message_handler(commands=['reset'])
async def reset_filters(message: types.Message):
    global min_filter_spread, max_filter_spread, currencies, banks
    min_filter_spread = 5
    max_filter_spread = 50
    currencies = ['USDT', 'BTC', 'TON']
    banks = []
    await message.answer("♻️ Настройки сброшены по умолчанию")

@dp.message_handler(commands=['history'])
async def history(message: types.Message):
    if history_log:
        await message.answer("\n\n".join(history_log[-5:]))
    else:
        await message.answer("🔐 История пуста")

# ========== 🔹 Мониторинг сделок Bybit ==========

async def check_market():
    global history_log
    while is_checking:
        results = []
        now = datetime.now().strftime("%H:%M:%S")
        for currency in currencies:
            payload_buy = {
                "userId": "",
                "tokenId": currency,
                "side": "1",
                "currencyId": "KZT",
                "payment": banks if banks else [],
                "page": 1,
                "size": 1,
                "amount": "",
                "authMaker": False
            }
            payload_sell = payload_buy.copy()
            payload_sell["side"] = "0"

            try:
                response_buy = requests.post("https://api2.bybit.com/fiat/otc/item/online", json=payload_buy)
                response_sell = requests.post("https://api2.bybit.com/fiat/otc/item/online", json=payload_sell)
                buy_data = response_buy.json()
                sell_data = response_sell.json()

                if response_buy.status_code == 200 and response_sell.status_code == 200:
                    if not buy_data['result']['items'] or not sell_data['result']['items']:
                        results.append(f"❌ Извините, на данный момент подходящих предложений для {currency} нет.")
                        continue
                    
                    buy_price = float(buy_data['result']['items'][0]['price'])
                    sell_price = float(sell_data['result']['items'][0]['price'])
                    spread = sell_price - buy_price

                    if min_filter_spread <= spread <= max_filter_spread:
                        result = f"[{now}] {currency}: ✅ Купить за {buy_price}₸ / ❌ Продать за {sell_price}₸ — Спред: {spread:.2f}₸"
                        results.append(result)

                else:
                    reason = buy_data.get("ret_msg", "Неизвестная ошибка с получением данных.")
                    results.append(f"⚠️ Не могу получить информацию для {currency}: {reason}")

            except Exception as e:
                results.append(f"⚠️ Ошибка при получении данных: {str(e)}")

        if results:
            for r in results:
                history_log.append(r)
                await bot.send_message(OWNER_ID, r)

        await asyncio.sleep(check_interval * 60)

@dp.message_handler(commands=['start_check'])
async def start_check(message: types.Message):
    global is_checking
    if not is_checking:
        is_checking = True
        await message.answer("📈 Мониторинг включен")
        asyncio.create_task(check_market())
    else:
        await message.answer("⚠️ Уже работает")

@dp.message_handler(commands=['stop_check'])
async def stop_check(message: types.Message):
    global is_checking
    is_checking = False
    await message.answer("⏹️ Мониторинг остановлен")

# ========== ▶️ Запуск ==========

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
