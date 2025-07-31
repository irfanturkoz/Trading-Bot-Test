import telebot
from telebot import types
import json
import os
from datetime import datetime
from license_manager import LicenseManager
from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID

# Bot başlat
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Lisans yöneticisi
license_manager = LicenseManager()

# Kullanıcı durumları
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Bot başlangıç mesajı"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Lisans kontrolü
    license_status, license_result = check_user_license(user_id)
    
    if license_status:
        # Kullanıcının lisansı var
        license_info = license_result
        welcome_text = f"""
🤖 **Hoş Geldiniz {user_name}!**

✅ **Lisansınız Aktif!**

📦 **Paket:** {license_info['type'].upper()}
💰 **Fiyat:** ${license_info['price']}
📅 **Aktifleştirme:** {license_info['activated_date'][:10]}
"""
        
        if license_info['expiry_date']:
            welcome_text += f"⏰ **Bitiş:** {license_info['expiry_date'][:10]}\n"
        else:
            welcome_text += "⏰ **Bitiş:** Sınırsız\n"
        
        welcome_text += """
🚀 **Bot Kullanıma Hazır!**

Komutlar:
/scan - Coin taraması başlat
/status - Lisans durumu
/help - Yardım
"""
        
        # Ana menü butonları
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🔍 Coin Tara"))
        markup.row(types.KeyboardButton("📊 Lisans Durumu"))
        markup.row(types.KeyboardButton("❓ Yardım"))
        
    else:
        # Kullanıcının lisansı yok
        welcome_text = f"""
🤖 **Hoş Geldiniz {user_name}!**

❌ **Lisansınız Yok!**

🔑 **Lisans Anahtarınızı Giriniz:**
Lisans anahtarınızı buraya yazın.

💬 **Lisans Satın Almak İçin:**
@tgtradingbot ile iletişime geçin.

📦 **Paketler:**
• 1 Aylık: $200
• 3 Aylık: $500
• Sınırsız: $1500
"""
        
        # Lisans giriş durumunu ayarla
        user_states[user_id] = "waiting_license"
        
        # Lisans giriş butonu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🔑 Lisans Anahtarı Gir"))
        markup.row(types.KeyboardButton("💬 Lisans Satın Al"))
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    """Yardım mesajı"""
    help_text = """
❓ **Yardım**

🔍 **Coin Tara:** Otomatik coin taraması başlatır
📊 **Lisans Durumu:** Mevcut lisans bilgilerini gösterir
🔑 **Lisans Anahtarı Gir:** Yeni lisans anahtarı girmenizi sağlar

💬 **Destek:** @tgtradingbot
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def send_status(message):
    """Lisans durumu"""
    user_id = message.from_user.id
    license_status, license_result = check_user_license(user_id)
    
    if license_status:
        license_info = license_result
        status_text = f"""
📊 **Lisans Durumu**

✅ **Durum:** Aktif
📦 **Paket:** {license_info['type'].upper()}
💰 **Fiyat:** ${license_info['price']}
📅 **Aktifleştirme:** {license_info['activated_date'][:10]}
"""
        
        if license_info['expiry_date']:
            expiry_date = datetime.fromisoformat(license_info['expiry_date'])
            remaining_days = (expiry_date - datetime.now()).days
            status_text += f"⏰ **Bitiş:** {license_info['expiry_date'][:10]}\n"
            status_text += f"📊 **Kalan:** {max(0, remaining_days)} gün\n"
        else:
            status_text += "⏰ **Bitiş:** Sınırsız\n"
        
        status_text += f"""
✅ **Özellikler:**
"""
        for feature in license_info['features']:
            status_text += f"• {feature}\n"
    else:
        status_text = """
❌ **Lisans Bulunamadı!**

🔑 **Lisans Anahtarınızı Gönderin:**
Lisans anahtarınızı buraya yazın.

💬 **Lisans Satın Almak İçin:**
@tgtradingbot ile iletişime geçin.
"""
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['scan'])
def start_scan(message):
    """Coin taraması başlat"""
    user_id = message.from_user.id
    license_status, license_result = check_user_license(user_id)
    
    if not license_status:
        error_text = """
❌ **Lisans Gerekli!**

🔑 **Lisans Anahtarınızı Giriniz:**
Lisans anahtarınızı buraya yazın.

💬 **Lisans Satın Almak İçin:**
@tgtradingbot ile iletişime geçin.

📦 **Paketler:**
• 1 Aylık: $200
• 3 Aylık: $500
• Sınırsız: $1500
"""
        # Lisans giriş durumunu ayarla
        user_states[user_id] = "waiting_license"
        
        # Lisans giriş butonu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🔑 Lisans Anahtarı Gir"))
        markup.row(types.KeyboardButton("💬 Lisans Satın Al"))
        
        bot.reply_to(message, error_text, parse_mode='Markdown', reply_markup=markup)
        return
    
    # Tarama başlat
    bot.reply_to(message, "🔍 Coin taraması başlatılıyor...\n\n⏳ Bu işlem birkaç dakika sürebilir.")
    
    # Burada gerçek tarama fonksiyonu çağrılacak
    # Şimdilik demo mesajı
    import time
    time.sleep(2)
    
    scan_result = """
🎯 **Tarama Tamamlandı!**

📊 **Sonuçlar:**
• Taranan Coin: 150+
• Bulunan Fırsat: 3
• Tarama Süresi: 2.5 dakika

🚨 **Fırsatlar:**
1. BTCUSDT - Long (TOBO) - %2.8 potansiyel
2. ETHUSDT - Short (OBO) - %1.9 potansiyel  
3. ADAUSDT - Long (Falling Wedge) - %3.2 potansiyel

📱 **Detaylı bildirimler gönderildi!**
"""
    
    bot.reply_to(message, scan_result, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🔍 Coin Tara")
def handle_scan_button(message):
    """Coin tara butonu"""
    start_scan(message)

@bot.message_handler(func=lambda message: message.text == "📊 Lisans Durumu")
def handle_status_button(message):
    """Lisans durumu butonu"""
    send_status(message)

@bot.message_handler(func=lambda message: message.text == "❓ Yardım")
def handle_help_button(message):
    """Yardım butonu"""
    send_help(message)

@bot.message_handler(func=lambda message: message.text == "🔑 Lisans Anahtarı Gir")
def handle_license_button(message):
    """Lisans anahtarı gir butonu"""
    bot.reply_to(message, "🔑 **Lisans Anahtarınızı Gönderin:**\n\nLisans anahtarınızı buraya yazın.")
    user_states[message.from_user.id] = "waiting_license"

@bot.message_handler(func=lambda message: message.text == "💬 Lisans Satın Al")
def handle_buy_license(message):
    """Lisans satın al butonu"""
    buy_text = """
💬 **Lisans Satın Alma**

📦 **Paketler:**
• 1 Aylık: $200
• 3 Aylık: $500 (İndirimli)
• Sınırsız: $1500

✅ **Özellikler:**
• Otomatik coin tarama
• Telegram bildirimleri
• Formasyon analizi
• Risk/ödül hesaplama
• 3 TP seviyesi

🔗 **İletişim:** @tgtradingbot
"""
    bot.reply_to(message, buy_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_license")
def handle_license_input(message):
    """Lisans anahtarı girişi"""
    user_id = message.from_user.id
    license_key = message.text.strip()
    
    # Lisans anahtarını doğrula
    is_valid, result = license_manager.validate_license(license_key)
    
    if is_valid:
        # Lisans geçerli
        license_info = result
        
        # Kullanıcı lisansını kaydet
        save_user_license(user_id, license_info)
        
        success_text = f"""
✅ **Lisans Doğrulandı!**

📦 **Paket:** {license_info['type'].upper()}
💰 **Fiyat:** ${license_info['price']}
📅 **Aktifleştirme:** {license_info['activated_date'][:10]}
"""
        
        if license_info['expiry_date']:
            success_text += f"⏰ **Bitiş:** {license_info['expiry_date'][:10]}\n"
        else:
            success_text += "⏰ **Bitiş:** Sınırsız\n"
        
        success_text += """
🚀 **Bot Başlatılıyor!**

🔍 **Coin Tara** butonuna basarak tarama başlatabilirsiniz.
"""
        
        # Ana menü butonları
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🔍 Coin Tara"))
        markup.row(types.KeyboardButton("📊 Lisans Durumu"))
        markup.row(types.KeyboardButton("❓ Yardım"))
        
        bot.reply_to(message, success_text, parse_mode='Markdown', reply_markup=markup)
        
        # Admin'e bildirim gönder
        admin_notification = f"""
🆕 **Yeni Lisans Aktifleştirildi!**

👤 **Kullanıcı:** {message.from_user.first_name}
🆔 **User ID:** {user_id}
📦 **Paket:** {license_info['type'].upper()}
💰 **Fiyat:** ${license_info['price']}
🔑 **Anahtar:** {license_key[:10]}...
"""
        bot.send_message(ADMIN_CHAT_ID, admin_notification, parse_mode='Markdown')
        
    else:
        # Lisans geçersiz
        error_text = f"""
❌ Yanlış Lisans Anahtarı!

🔑 Gönderilen: {license_key}

⚠️ Bu lisans anahtarı geçersiz!

💬 Lisans Satın Almak İçin:
@tgtradingbot ile iletişime geçin.

📦 Paketler:
• 1 Aylık: $200
• 3 Aylık: $500
• Sınırsız: $1500

🔑 Tekrar denemek için lisans anahtarınızı gönderin:
"""
        
        # Lisans giriş durumunu koru
        user_states[user_id] = "waiting_license"
        
        # Lisans giriş butonu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🔑 Lisans Anahtarı Gir"))
        markup.row(types.KeyboardButton("💬 Lisans Satın Al"))
        
        bot.reply_to(message, error_text, reply_markup=markup)
    
    # Kullanıcı durumunu temizle
    user_states.pop(user_id, None)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Diğer tüm mesajlar"""
    user_id = message.from_user.id
    license_status, license_result = check_user_license(user_id)
    
    if not license_status:
        # Lisans yoksa lisans anahtarı iste
        bot.reply_to(message, "🔑 **Lisans Anahtarınızı Gönderin:**\n\nLisans anahtarınızı buraya yazın.\n\n💬 **Lisans Satın Almak İçin:** @tgtradingbot")
    else:
        # Lisans varsa yardım mesajı
        bot.reply_to(message, "❓ Yardım için /help yazın.\n🔍 Coin taraması için '🔍 Coin Tara' butonuna basın.")

def check_user_license(user_id):
    """Kullanıcının lisansını kontrol eder"""
    try:
        if os.path.exists(f"user_licenses/{user_id}.json"):
            with open(f"user_licenses/{user_id}.json", 'r') as f:
                license_data = json.load(f)
            
            # Süre kontrolü
            if license_data['expiry_date']:
                expiry_date = datetime.fromisoformat(license_data['expiry_date'])
                if datetime.now() > expiry_date:
                    return False, "Lisans süresi dolmuş"
            
            return True, license_data
    except Exception as e:
        pass
    
    return False, "Lisans bulunamadı"

def save_user_license(user_id, license_info):
    """Kullanıcı lisansını kaydeder"""
    try:
        # Klasör oluştur
        os.makedirs("user_licenses", exist_ok=True)
        
        # Lisans bilgilerini kaydet
        license_data = {
            "user_id": user_id,
            "license_key": license_info['key'],
            "type": license_info['type'],
            "price": license_info['price'],
            "activated_date": license_info['activated_date'],
            "expiry_date": license_info['expiry_date'],
            "features": license_info['features']
        }
        
        with open(f"user_licenses/{user_id}.json", 'w') as f:
            json.dump(license_data, f, indent=2)
            
    except Exception as e:
        print(f"Lisans kaydedilemedi: {e}")

def main():
    """Bot'u başlat"""
    print("🤖 Telegram Bot Başlatılıyor...")
    print(f"📱 Bot: @apfel_trading_bot")
    print(f"🔑 Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print("✅ Bot çalışıyor! Ctrl+C ile durdurun.")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
    except Exception as e:
        print(f"❌ Bot hatası: {e}")

if __name__ == "__main__":
    main() 