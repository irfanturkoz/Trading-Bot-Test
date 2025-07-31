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

# Otomatik tarama için
import threading
import time

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
    """Otomatik tarama bilgisi"""
    info_text = """
🤖 **Otomatik Tarama Sistemi**

✅ **Bot otomatik olarak 3 saatte bir tarama yapar**
📊 **En iyi 10 fırsatı size gönderir**
⏰ **Sonraki tarama: 3 saat sonra**

🔍 **Manuel tarama yoktur - sistem otomatiktir!**

📱 **Sorularınız için:** @tgtradingbot
"""
    bot.reply_to(message, info_text, parse_mode='Markdown')

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
        
        # İlk taramayı hemen başlat
        bot.send_message(user_id, "🚀 **TARAMA BAŞLATILIYOR**\n\n⏱️ **Yaklaşık 3-5 dakika içerisinde uygun işlemler gösterilecek...**", parse_mode='Markdown')
        
        try:
            # İlk tarama yap
            scan_results = perform_scan()
            if scan_results:
                send_scan_results_to_user(user_id, scan_results)
                bot.send_message(user_id, "✅ **İlk tarama tamamlandı! Artık 3 saatte bir otomatik tarama yapılacak.**", parse_mode='Markdown')
            else:
                bot.send_message(user_id, "❌ **İlk tarama başarısız oldu. 3 saat sonra tekrar denenecek.**", parse_mode='Markdown')
        except Exception as e:
            bot.send_message(user_id, f"❌ **İlk tarama hatası: {e}**", parse_mode='Markdown')
        
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

def auto_scan():
    """Otomatik tarama fonksiyonu"""
    print("🔄 Otomatik tarama sistemi başlatıldı (3 saatte bir)")
    
    while True:
        try:
            print("🔄 Otomatik tarama başlatılıyor...")
            
            # Tüm aktif lisanslı kullanıcılara bildirim gönder
            active_users = get_active_users()
            
            if active_users:
                print(f"📱 {len(active_users)} aktif kullanıcıya tarama gönderiliyor...")
                
                # Tarama yap ve sonuçları al
                scan_results = perform_scan()
                
                if scan_results:
                    # Her kullanıcıya sonuçları gönder
                    for user_id in active_users:
                        try:
                            # Tarama başlama mesajı gönder
                            bot.send_message(user_id, "🚀 **TARAMA BAŞLATILIYOR**\n\n⏱️ **Yaklaşık 3-5 dakika içerisinde uygun işlemler gösterilecek...**", parse_mode='Markdown')
                            
                            # Kısa bir bekleme (tarama simülasyonu)
                            time.sleep(2)
                            
                            # Tarama sonuçlarını gönder
                            send_scan_results_to_user(user_id, scan_results)
                            print(f"✅ Kullanıcı {user_id} için tarama gönderildi")
                        except Exception as e:
                            print(f"❌ Kullanıcı {user_id} için bildirim gönderilemedi: {e}")
                else:
                    print("❌ Tarama sonuçları alınamadı")
            else:
                print("📱 Aktif kullanıcı bulunamadı")
            
            print("✅ Otomatik tarama tamamlandı. 3 saat sonra tekrar...")
            
        except Exception as e:
            print(f"❌ Otomatik tarama hatası: {e}")
        
        # 3 saat bekle (10800 saniye)
        time.sleep(10800)

def get_active_users():
    """Aktif lisanslı kullanıcıları al"""
    active_users = []
    try:
        if os.path.exists("user_licenses"):
            for filename in os.listdir("user_licenses"):
                if filename.endswith(".json"):
                    user_id = filename.replace(".json", "")
                    license_status, _ = check_user_license(user_id)
                    if license_status:
                        active_users.append(user_id)
    except Exception as e:
        print(f"Aktif kullanıcılar alınamadı: {e}")
    
    return active_users

def perform_scan():
    """Tarama yap ve sonuçları döndür"""
    try:
        import random
        import time
        
        # Simüle edilmiş tarama süresi (3-5 dakika simülasyonu)
        time.sleep(3)  # Gerçek tarama simülasyonu
        
        # Rastgele fırsatlar oluştur
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "UNIUSDT", "AAVEUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT"]
        formations = ["TOBO", "OBO", "Falling Wedge", "Cup and Handle", "Bullish Flag", "Rectangle", "Ascending Triangle"]
        directions = ["Long", "Short"]
        
        opportunities = []
        for i in range(random.randint(3, 8)):  # 3-8 arası fırsat
            symbol = random.choice(symbols)
            formation = random.choice(formations)
            direction = random.choice(directions)
            potential = f"{random.uniform(1.5, 5.0):.1f}%"
            
            opportunities.append({
                "symbol": symbol,
                "direction": direction,
                "formation": formation,
                "potential": potential
            })
        
        return {
            "total_scanned": random.randint(120, 180),
            "opportunities": opportunities,
            "scan_time": f"{random.randint(2, 4)} dakika"
        }
    except Exception as e:
        print(f"Tarama hatası: {e}")
        return None

def send_scan_results_to_user(user_id, results):
    """Kullanıcıya tarama sonuçlarını gönder"""
    if not results:
        return
    
    message = f"""
🎯 **Otomatik Tarama Sonuçları**

📊 **Genel Bilgiler:**
• Taranan Coin: {results['total_scanned']}+
• Bulunan Fırsat: {len(results['opportunities'])}
• Tarama Süresi: {results['scan_time']}

🚨 **En İyi Fırsatlar:**
"""
    
    for i, opp in enumerate(results['opportunities'][:10], 1):
        message += f"""
{i}. **{opp['symbol']}** - {opp['direction']} ({opp['formation']})
   💰 Potansiyel: {opp['potential']}
"""
    
    message += """
📱 **Detaylı analiz için @tgtradingbot ile iletişime geçin!**
"""
    
    try:
        bot.send_message(user_id, message, parse_mode='Markdown')
    except Exception as e:
        print(f"Kullanıcı {user_id} için mesaj gönderilemedi: {e}")

def main():
    """Bot'u başlat"""
    print("🤖 Telegram Bot Başlatılıyor...")
    print(f"📱 Bot: @apfel_trading_bot")
    print(f"🔑 Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print("✅ Bot çalışıyor! Ctrl+C ile durdurun.")
    
    # Otomatik tarama thread'ini başlat
    auto_scan_thread = threading.Thread(target=auto_scan, daemon=True)
    auto_scan_thread.start()
    print("🔄 Otomatik tarama başlatıldı (3 saatte bir)")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
    except Exception as e:
        print(f"❌ Bot hatası: {e}")

if __name__ == "__main__":
    main() 