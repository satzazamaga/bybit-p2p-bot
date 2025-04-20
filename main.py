import os
from flask import Flask
import threading
from bot import main as run_bot

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот активен | /start в Telegram"

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
