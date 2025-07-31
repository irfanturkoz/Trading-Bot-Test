from flask import Flask, request, jsonify
import os
from telegram_bot import bot
import threading
import time

app = Flask(__name__)

# Bot'u arka planda çalıştır
def run_bot():
    print("🤖 Bot başlatılıyor...")
    while True:
        try:
            print("🔄 Bot polling başlatılıyor...")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Bot hatası: {e}")
            time.sleep(10)
            print("🔄 Bot yeniden başlatılıyor...")

# Bot thread'ini başlat
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

@app.route('/')
def home():
    return jsonify({
        "status": "Bot çalışıyor!",
        "message": "Telegram bot aktif durumda"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 