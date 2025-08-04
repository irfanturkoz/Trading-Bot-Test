import telebot
import os
from dotenv import load_dotenv
from botanlik import main as bot_main
import threading
import time

# .env dosyasını yükle
load_dotenv()

# Bot token'ını al
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
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
        bot_main()
    except Exception as e:
        bot_status["message"] = f"Bot hatası: {str(e)}"
    finally:
        bot_status["running"] = False
        bot_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")

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

def main():
    """Ana fonksiyon"""
    print("🚀 Telegram Bot başlatılıyor...")
    print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
    
    try:
        # Bot'u başlat
        bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"❌ Bot hatası: {e}")

if __name__ == "__main__":
    main() 