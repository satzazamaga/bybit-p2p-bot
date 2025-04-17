import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests

# Установите свой токен, который ты получил через BotFather
TOKEN = "8093706202:AAHRJz_paYKZ0R50TbUhcprxXmJd0VXy_mA"

# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация переменных
user_budget = None
selected_bank = 'all'
currency_list = ['USDT', 'BTC']
p2p_url = 'https://api.bybit.com/p2p/'

# Функция для старта
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет! Я помогу тебе найти выгодные предложения на Bybit P2P.\n"
                              "Используй /help для получения списка команд.")

# Функция для вывода помощи
def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("""
Доступные команды:
• /start — Запустить бота
• /budget [сумма] — Установить бюджет для сделок
• /cancel — Отключить бюджетный режим
• /bank [Название банка] — Фильтрация по банку (например, Kaspi, Halyk)
• /bank all — Показать все банки
• /status — Показать текущие лучшие курсы
• /currency — Список отслеживаемых валют
""")

# Функция для установки бюджета
def budget(update: Update, context: CallbackContext) -> None:
    global user_budget
    if context.args:
        try:
            user_budget = float(context.args[0])
            update.message.reply_text(f"Бюджет установлен: {user_budget} тг")
        except ValueError:
            update.message.reply_text("Неверный формат. Введите сумму в тг.")
    else:
        update.message.reply_text("Пожалуйста, укажите сумму.")

# Функция для отмены бюджета
def cancel(update: Update, context: CallbackContext) -> None:
    global user_budget
    user_budget = None
    update.message.reply_text("Бюджетный режим отключен.")

# Функция для выбора банка
def bank(update: Update, context: CallbackContext) -> None:
    global selected_bank
    if context.args:
        bank = context.args[0]
        if bank.lower() in ['kaspi', 'halyk', 'бцк', 'all']:
            selected_bank = bank.lower()
            update.message.reply_text(f"Фильтрация установлена по банку: {selected_bank.capitalize()}")
        else:
            update.message.reply_text("Неизвестный банк. Доступные банки: Kaspi, Halyk, БЦК, all.")
    else:
        update.message.reply_text("Пожалуйста, укажите банк.")

# Функция для получения текущих курсов
def status(update: Update, context: CallbackContext) -> None:
    # Пример запроса к P2P API Bybit, в реальности нужно подставить реальный эндпоинт
    response = requests.get(f'{p2p_url}/marketplace')
    data = response.json()
    
    # Здесь необходимо фильтровать данные по выбранному банку и курсу
    if data:
        offers = data.get('offers', [])
        message = "Текущие предложения:\n"
        for offer in offers:
            if selected_bank == 'all' or offer['bank'] == selected_bank:
                message += f"Банк: {offer['bank']}, Курс: {offer['rate']} тг/USDT, Сумма: {offer['amount']} USDT\n"
        update.message.reply_text(message if message else "Нет доступных предложений.")
    else:
        update.message.reply_text("Ошибка получения данных с Bybit.")

# Функция для вывода списка валют
def currency(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Отслеживаемые валюты: " + ", ".join(currency_list))

# Функция для обработки ошибок
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

# Основная функция для запуска бота
def main():
    updater = Updater(TOKEN)

    # Регистрация обработчиков команд
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("budget", budget))
    dispatcher.add_handler(CommandHandler("cancel", cancel))
    dispatcher.add_handler(CommandHandler("bank", bank))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("currency", currency))

    # Логирование ошибок
    dispatcher.add_error_handler(error)

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
