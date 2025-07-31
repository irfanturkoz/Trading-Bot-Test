from flask import Flask, request, jsonify
import os
import threading
import time

app = Flask(__name__)

# Bot'u ayrı bir thread'de başlat
def start_bot():
    print("🤖 Bot başlatılıyor...")
    
    # Daha uzun bekle
    print("⏳ 30 saniye bekleniyor...")
    time.sleep(30)
    
    try:
        from telegram_bot import bot
        print("✅ Bot import edildi")
        
        # Webhook'u zorla temizle
        try:
            bot.remove_webhook()
            print("✅ Webhook temizlendi")
        except Exception as e:
            print(f"⚠️ Webhook temizleme hatası: {e}")
        
        # Bot'u başlat
        print("🔄 Bot polling başlatılıyor...")
        bot.polling(none_stop=True, timeout=60)
        
    except Exception as e:
        print(f"❌ Bot hatası: {e}")
        if "Conflict: terminated by other getUpdates request" in str(e):
            print("⚠️ Diğer bot instance'ı tespit edildi!")
            print("🔄 300 saniye (5 dakika) bekleniyor...")
            time.sleep(300)
            # Tekrar dene
            start_bot()
        else:
            print("🔄 60 saniye bekleniyor...")
            time.sleep(60)
            start_bot()

# Bot thread'ini başlat
print("🚀 Bot thread'i başlatılıyor...")
bot_thread = threading.Thread(target=start_bot, daemon=True)
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