from flask import Flask, request, jsonify
import os
from telegram_bot import bot
import threading
import time

app = Flask(__name__)

# Webhook URL'si
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

# Bot'u webhook ile başlat
def setup_webhook():
    if WEBHOOK_URL:
        try:
            bot.remove_webhook()
            bot.set_webhook(url=WEBHOOK_URL)
            print(f"✅ Webhook ayarlandı: {WEBHOOK_URL}")
            return True
        except Exception as e:
            print(f"❌ Webhook hatası: {e}")
            return False
    return False

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    bot.process_new_updates([update])
    return jsonify({"status": "ok"})

# Bot'u arka planda çalıştır (fallback olarak)
def run_bot():
    print("🤖 Bot polling başlatılıyor...")
    while True:
        try:
            print("🔄 Bot polling başlatılıyor...")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Bot hatası: {e}")
            if "Conflict: terminated by other getUpdates request" in str(e):
                print("⚠️ Diğer bot instance'ı tespit edildi. 30 saniye bekleniyor...")
                time.sleep(30)
            else:
                time.sleep(10)
            print("🔄 Bot yeniden başlatılıyor...")

# Webhook ayarlanmamışsa polling kullan
if not setup_webhook():
    print("🔄 Webhook ayarlanamadı, polling kullanılıyor...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
else:
    print("✅ Webhook modu aktif!")

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