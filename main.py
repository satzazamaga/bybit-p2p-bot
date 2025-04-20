from flask import Flask
import threading
from bot import main as run_bot
import logging
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ P2P Bot Active | Bybit Monitor"

def run_bot_wrapper():
    try:
        run_bot()
    except Exception as e:
        logger.critical(f"Бот упал: {str(e)}")

if __name__ == '__main__':
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot_wrapper, daemon=True)
    bot_thread.start()
    
    # Запуск веб-сервера
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
