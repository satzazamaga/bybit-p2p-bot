from flask import Flask
import asyncio
from bot import run_bot
import logging
import os
import threading

app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ P2P Bot Active | Bybit Monitor"

def run_async_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == '__main__':
    # Запуск бота в отдельном потоке с собственным event loop
    bot_thread = threading.Thread(target=run_async_bot, daemon=True)
    bot_thread.start()
    
    # Запуск Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
