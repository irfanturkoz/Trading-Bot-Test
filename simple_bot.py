import telebot
from telebot import types
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Bot token'ını environment variable'dan al
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN environment variable bulunamadı!")
    print("💡 .env dosyası oluşturun ve TELEGRAM_BOT_TOKEN ekleyin")
    raise ValueError("Bot token bulunamadı!")

print("✅ Simple bot: Token environment variable'dan yüklendi")

# Bot başlat
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Bot başlangıç mesajı"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    welcome_text = f"""
🤖 **Hoş Geldiniz {user_name}!**

Bu test bot'udur. Çalışıyor mu kontrol ediyoruz.

Komutlar:
/test - Test mesajı
/status - Bot durumu
"""
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧪 Test"))
    markup.row(types.KeyboardButton("📊 Durum"))
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['test'])
def test_message(message):
    """Test mesajı"""
    bot.reply_to(message, "✅ Test başarılı! Bot çalışıyor!")

@bot.message_handler(commands=['status'])
def status_message(message):
    """Durum mesajı"""
    bot.reply_to(message, "🟢 Bot aktif ve çalışıyor!")

@bot.message_handler(func=lambda message: message.text == "🧪 Test")
def handle_test_button(message):
    """Test butonu"""
    bot.reply_to(message, "✅ Test butonu çalışıyor!")

@bot.message_handler(func=lambda message: message.text == "📊 Durum")
def handle_status_button(message):
    """Durum butonu"""
    bot.reply_to(message, "🟢 Bot durumu: AKTİF")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Tüm mesajları yakala"""
    bot.reply_to(message, f"📝 Mesajınız: {message.text}")

def main():
    """Bot'u başlat"""
    print("🤖 Test Bot Başlatılıyor...")
    print(f"📱 Bot: @apfel_trading2_bot")
    print(f"🔑 Token: {BOT_TOKEN[:20]}...")
    print("✅ Bot çalışıyor! Ctrl+C ile durdurun.")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
    except Exception as e:
        print(f"❌ Bot hatası: {e}")

if __name__ == "__main__":
    main() 