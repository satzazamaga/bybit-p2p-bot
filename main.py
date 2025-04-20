from flask import Flask
import threading
from bot import main as run_bot
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "P2P Monitor Bot is running! 🚀 /status - проверка работы"

@app.route('/ping')
def ping():
    """Эндпоинт для поддержания активности"""
    logger.info("Получен ping-запрос")
    return "pong"

def run_bot_in_thread():
    """Запуск бота в отдельном потоке"""
    try:
        logger.info("Starting Telegram bot...")
        run_bot()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == '__main__':
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask-сервер
    app.run(host='0.0.0.0', port=10000)
