import threading
import time
import os
from flask import Flask, jsonify
import telebot
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Flask app
app = Flask(__name__)

# Bot token'ını al
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ BOT_TOKEN bulunamadı!")
    exit(1)

# Bot'u oluştur
bot = telebot.TeleBot(BOT_TOKEN)

# Bot durumu
bot_status = {
    "running": False,
    "last_run": None,
    "message": "Bot başlatılmadı"
}

def run_bot_analysis():
    """Bot analizini ayrı thread'de çalıştır"""
    global bot_status
    bot_status["running"] = True
    bot_status["message"] = "Bot analizi çalışıyor..."
    
    try:
        from botanlik import main as bot_main
        bot_main()
    except Exception as e:
        bot_status["message"] = f"Bot hatası: {str(e)}"
    finally:
        bot_status["running"] = False
        bot_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")

# Telegram bot komutları
@bot.message_handler(commands=['start'])
def start_command(message):
    """Bot'u başlat"""
    user_id = message.from_user.id
    username = message.from_user.username or "Bilinmeyen"
    
    welcome_text = f"""
🚀 **Botanlik Bot Hoş Geldin!**

👤 **Kullanıcı:** @{username}
🆔 **ID:** {user_id}

📊 **Bot Durumu:** {bot_status["message"]}

**Komutlar:**
/start - Bot'u başlat
/status - Bot durumunu kontrol et
/analyze - Manuel analiz başlat
/stop - Bot'u durdur

⚠️ **Not:** Bot otomatik olarak çalışır ve sinyalleri Telegram'a gönderir.
    """
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_command(message):
    """Bot durumunu göster"""
    status_text = f"""
📊 **Bot Durumu:**

🔄 **Çalışma Durumu:** {'✅ Çalışıyor' if bot_status["running"] else '❌ Durdu'}
⏰ **Son Çalışma:** {bot_status["last_run"] or "Henüz çalışmadı"}
📝 **Mesaj:** {bot_status["message"]}
    """
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['analyze'])
def analyze_command(message):
    """Manuel analiz başlat"""
    if bot_status["running"]:
        bot.reply_to(message, "❌ Bot zaten çalışıyor! Önce /stop ile durdurun.")
        return
    
    bot.reply_to(message, "🚀 Manuel analiz başlatılıyor...")
    
    # Analizi ayrı thread'de başlat
    thread = threading.Thread(target=run_bot_analysis)
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=['stop'])
def stop_command(message):
    """Bot'u durdur"""
    if bot_status["running"]:
        bot_status["running"] = False
        bot_status["message"] = "Bot durduruldu"
        bot.reply_to(message, "🛑 Bot durduruldu!")
    else:
        bot.reply_to(message, "❌ Bot zaten durmuş durumda!")

@bot.message_handler(commands=['help'])
def help_command(message):
    """Yardım mesajı"""
    help_text = """
📚 **Botanlik Bot Yardım**

**Komutlar:**
/start - Bot'u başlat ve hoş geldin mesajı
/status - Bot durumunu kontrol et
/analyze - Manuel analiz başlat
/stop - Bot'u durdur
/help - Bu yardım mesajını göster

**Özellikler:**
🔍 Otomatik formasyon analizi
📊 Yüksek kaliteli sinyaller
📈 Risk/Ödül hesaplaması
🖼️ Grafik görselleştirme
📱 Telegram bildirimleri

**Destek:**
Sorun yaşarsanız admin ile iletişime geçin.
    """
    
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Bilinmeyen komutlar için"""
    bot.reply_to(message, "❓ Bilinmeyen komut. /help yazarak komutları görebilirsiniz.")

# Flask routes
@app.route('/')
def home():
    return jsonify({
        "status": "Botanlik Bot API çalışıyor",
        "bot_status": bot_status,
        "endpoints": {
            "/": "Ana sayfa",
            "/status": "Bot durumu",
            "/start": "Bot'u başlat",
            "/health": "Sağlık kontrolü"
        }
    })

@app.route('/status')
def get_status():
    return jsonify(bot_status)

@app.route('/start')
def start_bot():
    if not bot_status["running"]:
        thread = threading.Thread(target=run_bot_analysis)
        thread.daemon = True
        thread.start()
        return jsonify({"message": "Bot başlatıldı", "status": "success"})
    else:
        return jsonify({"message": "Bot zaten çalışıyor", "status": "already_running"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

def run_flask():
    """Flask uygulamasını çalıştır"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram_bot():
    """Telegram botunu çalıştır"""
    print("🚀 Telegram Bot başlatılıyor...")
    print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
    
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"❌ Bot hatası: {e}")

def main():
    """Ana fonksiyon - hem Flask hem Telegram botu çalıştır"""
    print("🚀 Botanlik Bot başlatılıyor...")
    print("📱 Telegram Bot: Aktif")
    print("🌐 Admin Panel: Aktif")
    
    # Flask'i ayrı thread'de başlat
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Telegram botunu ana thread'de çalıştır
    run_telegram_bot()

if __name__ == "__main__":
    main() 