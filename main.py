from flask import Flask
from bot import run_bot
import multiprocessing
import os

app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ P2P Bot Active | Bybit Monitor"

def start_bot():
    run_bot()

if __name__ == '__main__':
    # Запуск бота в отдельном процессе
    bot_process = multiprocessing.Process(target=start_bot)
    bot_process.start()
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    
    # По завершении
    bot_process.terminate()
