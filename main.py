import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

API_TOKEN = '8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA'  # Вставь свой токен
OWNER_ID = 5791850798  # твой Telegram ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Настройки
filter_spread = 5
currencies = ['USDT', 'BTC', 'TON']
banks = []
check_interval = 5  # в минутах
history_log = []
is_checking = False

# Клавиатура с кнопками для команд
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton('/start_check'), KeyboardButton('/stop_check'))
menu.add(KeyboardButton('/status'), KeyboardButton('/history'))
menu.add(KeyboardButton('/reset'), KeyboardButton('/help'))

# ========== Команды ==========

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Бот запущен. Ниже меню для управления:", reply_markup=menu)

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("""Меню команд:
/start_check — начать мониторинг
/stop_check — остановить
/status — текущие настройки
/history — последние сделки
/reset — сброс настроек
/help — помощь
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

# ========== Проверка предложений (реальный запрос) ==========

async def check_market():
    global history_log
    while is_checking:
        results = []
        now = datetime.now().strftime("%H:%M:%S")
        for currency in currencies:
            try:
                # Получение данных с Bybit P2P (реальный запрос)
                url = f'https://api.bybit.com/v2/public/orderbook/L2?symbol={currency}USDT'
                response = requests.get(url)
                data = response.json()

                if data['ret_code'] == 0:
                    buy_price = float(data['result'][0]['price'])
                    sell_price = float(data['result'][1]['price'])
                    spread = sell_price - buy_price

                    if spread >= filter_spread:
                        result = f"[{now}] {currency}: Купить за {buy_price}₸ / Продать за {sell_price}₸ — Спред: {spread}₸"
                        results.append(result)

            except Exception as e:
                logging.error(f"Ошибка при запросе данных: {e}")

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
        await message.answer("Мониторинг включен.")
        asyncio.create_task(check_market())
    else:
        await message.answer("Мониторинг уже работает.")

@dp.message_handler(commands=['stop_check'])
async def stop_check(message: types.Message):
    global is_checking
    is_checking = False
    await message.answer("Мониторинг остановлен.")

# ========== Запуск ==========

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
