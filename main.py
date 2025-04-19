import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

API_TOKEN = '8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA'
OWNER_ID = 5791850798  # Твой Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройки по умолчанию
filter_spread = 5
currencies = ['USDT', 'BTC', 'TON']
banks = []
check_interval = 5  # в минутах
history_log = []
is_checking = False

# Меню кнопок
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(
    KeyboardButton('🚀 Начать мониторинг'), KeyboardButton('🛑 Остановить мониторинг')
).add(
    KeyboardButton('📊 Статус'), KeyboardButton('📜 История')
).add(
    KeyboardButton('🔁 Сброс настроек'), KeyboardButton('❓ Помощь')
)

# ========== Команды ==========

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Выбирай действие ниже:", reply_markup=menu)

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("""
🤖 Доступные команды:
🚀 /start_check — начать мониторинг
🛑 /stop_check — остановить
📊 /status — текущие настройки
📜 /history — последние сделки
🔁 /reset — сброс настроек
❓ /help — помощь

Дополнительно:
/set_filter 5 — минимальный спред
/currencies USDT BTC — валюты
/banks Kaspi Халык — банки
/interval 5 — интервал (мин)
    """, reply_markup=menu)

@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    await message.answer(
        f"📊 Статус:
Валюты: {', '.join(currencies)}
Спред: {filter_spread}₸
Банки: {'все' if not banks else ', '.join(banks)}
Интервал: {check_interval} мин
Мониторинг: {'🟢 ВКЛ' if is_checking else '🔴 ВЫКЛ'}"
    )

@dp.message_handler(commands=['set_filter'])
async def set_filter(message: types.Message):
    global filter_spread
    try:
        value = int(message.get_args())
        filter_spread = value
        await message.answer(f"✅ Спред установлен: {filter_spread}₸")
    except:
        await message.answer("Введите число: /set_filter 5")

@dp.message_handler(commands=['currencies'])
async def set_currencies(message: types.Message):
    global currencies
    args = message.get_args().split()
    if args:
        currencies = args
        await message.answer(f"✅ Валюты обновлены: {', '.join(currencies)}")
    else:
        await message.answer("Пример: /currencies USDT BTC")

@dp.message_handler(commands=['banks'])
async def set_banks(message: types.Message):
    global banks
    args = message.get_args().split()
    banks = args
    await message.answer(f"✅ Банки обновлены: {'все' if not banks else ', '.join(banks)}")

@dp.message_handler(commands=['interval'])
async def set_interval(message: types.Message):
    global check_interval
    try:
        value = int(message.get_args())
        check_interval = value
        await message.answer(f"⏱ Интервал обновлён: {check_interval} мин")
    except:
        await message.answer("Пример: /interval 10")

@dp.message_handler(commands=['reset'])
async def reset_filters(message: types.Message):
    global filter_spread, currencies, banks
    filter_spread = 5
    currencies = ['USDT', 'BTC', 'TON']
    banks = []
    await message.answer("🔁 Настройки сброшены.")

@dp.message_handler(commands=['history'])
async def history(message: types.Message):
    if history_log:
        await message.answer("\n\n".join(history_log[-5:]))
    else:
        await message.answer("📜 История пуста.")

# ========== Проверка сделок (реально через Bybit API) ==========
async def check_market():
    global history_log
    while is_checking:
        try:
            results = []
            now = datetime.now().strftime("%H:%M:%S")
            for currency in currencies:
                response_buy = requests.get(f"https://api2.bybit.com/fiat/otc/item/online", params={
                    "userId": "",
                    "tokenId": currency,
                    "currencyId": "KZT",
                    "payment": banks,
                    "side": "1",
                    "size": "10",
                    "page": "1"
                }).json()

                response_sell = requests.get(f"https://api2.bybit.com/fiat/otc/item/online", params={
                    "userId": "",
                    "tokenId": currency,
                    "currencyId": "KZT",
                    "payment": banks,
                    "side": "2",
                    "size": "10",
                    "page": "1"
                }).json()

                buy_price = float(response_buy['result']['items'][0]['price'])
                sell_price = float(response_sell['result']['items'][0]['price'])
                spread = sell_price - buy_price

                if spread >= filter_spread:
                    result = f"[{now}] {currency} — Купить: {buy_price}₸ / Продать: {sell_price}₸ ➡ Спред: {spread:.2f}₸"
                    results.append(result)

            if results:
                for r in results:
                    history_log.append(r)
                    await bot.send_message(OWNER_ID, r)

        except Exception as e:
            logging.warning(f"Ошибка при проверке рынка: {e}")

        await asyncio.sleep(check_interval * 60)

# ========== Обработчики кнопок и команд ==========

@dp.message_handler(lambda message: message.text == '🚀 Начать мониторинг' or message.text.startswith('/start_check'))
async def start_check(message: types.Message):
    global is_checking
    if not is_checking:
        is_checking = True
        await message.answer("🚀 Мониторинг включен.")
        asyncio.create_task(check_market())
    else:
        await message.answer("Мониторинг уже работает.")

@dp.message_handler(lambda message: message.text == '🛑 Остановить мониторинг' or message.text.startswith('/stop_check'))
async def stop_check(message: types.Message):
    global is_checking
    is_checking = False
    await message.answer("🛑 Мониторинг остановлен.")

@dp.message_handler(lambda message: message.text == '📊 Статус')
async def show_status_button(message: types.Message):
    await status(message)

@dp.message_handler(lambda message: message.text == '📜 История')
async def show_history_button(message: types.Message):
    await history(message)

@dp.message_handler(lambda message: message.text == '🔁 Сброс настроек')
async def reset_button(message: types.Message):
    await reset_filters(message)

@dp.message_handler(lambda message: message.text == '❓ Помощь')
async def help_button(message: types.Message):
    await help_cmd(message)

# ========== Запуск ==========
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
