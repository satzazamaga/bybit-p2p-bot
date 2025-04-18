import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

API_TOKEN = 'ТОКЕН_ТВОЕГО_БОТА'  # Замени на свой токен
OWNER_ID = 5791850798  # Твой Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Меню кнопок
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton('/start_check'), KeyboardButton('/stop_check'))
menu.add(KeyboardButton('/status'), KeyboardButton('/history'))
menu.add(KeyboardButton('/reset'), KeyboardButton('/help'))

# Настройки
filter_spread = 5
currencies = ['USDT', 'BTC', 'TON']
banks = []  # Например: ['KASPI_BANK', 'HALYK_BANK']
check_interval = 5  # минут
history_log = []
is_checking = False

# Команды
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Бот запущен. Ниже меню для управления:", reply_markup=menu)

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("""
Доступные команды:
/start — запустить бота
/status — текущие настройки
/set_filter [число] — установить минимальный спред
/currencies [валюты] — изменить список валют
/banks [список банков] — изменить список банков
/interval [минуты] — изменить интервал проверки
/start_check — запустить проверку вручную
/stop_check — остановить проверку
/history — последние уведомления
/reset — сбросить все фильтры
/help — показать это сообщение
""", reply_markup=menu)

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    await message.answer(
        f"Валюты: {', '.join(currencies)}\nМинимальный спред: {filter_spread}₸\n"
        f"Банки: {'все' if not banks else ', '.join(banks)}\nИнтервал: {check_interval} мин\nМониторинг: {'ВКЛ' if is_checking else 'ВЫКЛ'}"
    )

@dp.message_handler(commands=['set_filter'])
async def set_filter(message: types.Message):
    global filter_spread
    try:
        value = int(message.get_args())
        filter_spread = value
        await message.answer(f"Минимальный спред установлен: {filter_spread}₸")
    except:
        await message.answer("Введите число: /set_filter 5")

@dp.message_handler(commands=['currencies'])
async def set_currencies(message: types.Message):
    global currencies
    args = message.get_args().split()
    if args:
        currencies = args
        await message.answer(f"Отслеживаемые валюты: {', '.join(currencies)}")
    else:
        await message.answer("Пример: /currencies USDT BTC")

@dp.message_handler(commands=['banks'])
async def set_banks(message: types.Message):
    global banks
    args = message.get_args().split()
    banks = args
    await message.answer(f"Банки обновлены: {'все' if not banks else ', '.join(banks)}")

@dp.message_handler(commands=['interval'])
async def set_interval(message: types.Message):
    global check_interval
    try:
        value = int(message.get_args())
        check_interval = value
        await message.answer(f"Интервал обновлён: каждые {check_interval} минут")
    except:
        await message.answer("Пример: /interval 10")

@dp.message_handler(commands=['reset'])
async def reset_filters(message: types.Message):
    global filter_spread, currencies, banks
    filter_spread = 5
    currencies = ['USDT', 'BTC', 'TON']
    banks = []
    await message.answer("Настройки сброшены по умолчанию.")

@dp.message_handler(commands=['history'])
async def history(message: types.Message):
    if history_log:
        await message.answer("\n\n".join(history_log[-5:]))
    else:
        await message.answer("История пуста.")

@dp.message_handler(commands=['start_check'])
async def start_check(message: types.Message):
    global is_checking
    if not is_checking:
        is_checking = True
        await message.answer("Мониторинг включен.")
        asyncio.create_task(check_market())
    else:
        await message.answer("Мониторинг уже работает.")

@dp.message_handler(commands=['stop_check'])
async def stop_check(message: types.Message):
    global is_checking
    is_checking = False
    await message.answer("Мониторинг остановлен.")

# Реальный мониторинг Bybit P2P
async def check_market():
    global history_log
    while is_checking:
        now = datetime.now().strftime("%H:%M:%S")
        for currency in currencies:
            try:
                params = {
                    "userId": "",
                    "tokenId": currency,
                    "currencyId": "KZT",
                    "payment": banks,
                    "side": "1",
                    "size": "",
                    "page": 1,
                    "amount": "",
                    "authMaker": False,
                    "canTrade": False
                }
                buy_response = requests.post("https://api2.bybit.com/fiat/otc/item/online", json=params, timeout=10).json()

                params["side"] = "0"
                sell_response = requests.post("https://api2.bybit.com/fiat/otc/item/online", json=params, timeout=10).json()

                buy_price = float(buy_response['result']['items'][0]['price'])
                sell_price = float(sell_response['result']['items'][0]['price'])
                spread = sell_price - buy_price

                if spread >= filter_spread:
                    msg = (
                        f"[{now}] {currency}\n"
                        f"🔹 Купить за {buy_price:.2f}₸\n"
                        f"🔸 Продать за {sell_price:.2f}₸\n"
                        f"📊 Спред: {spread:.2f}₸"
                    )
                    history_log.append(msg)
                    await bot.send_message(OWNER_ID, msg)

            except Exception as e:
                await bot.send_message(OWNER_ID, f"[{now}] Ошибка по {currency}: {e}")

        await asyncio.sleep(check_interval * 60)

# Запуск
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
