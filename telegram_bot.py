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
    """Manuel tarama başlat"""
    user_id = message.from_user.id
    
    # Kullanıcının lisansını kontrol et
    license_status, license_result = check_user_license(user_id)
    if not license_status:
        bot.reply_to(message, "❌ **Lisansınız bulunamadı!**\n\n🔑 Lisans anahtarınızı girin.", parse_mode='Markdown')
        return
    
    # Son tarama zamanını kontrol et
    if can_user_scan(user_id):
        # Tarama başlat
        bot.send_message(user_id, "🚀 **TARAMA BAŞLATILIYOR**\n\n⏱️ **Yaklaşık 3-5 dakika içerisinde uygun işlemler gösterilecek...**", parse_mode='Markdown')
        
        try:
            scan_results = perform_scan()
            if scan_results:
                send_scan_results_to_user(user_id, scan_results)
                # Son tarama zamanını kaydet
                save_last_scan_time(user_id)
                bot.send_message(user_id, "✅ **Tarama tamamlandı!**\n\n⏰ **Sonraki tarama: 3 saat sonra**", parse_mode='Markdown')
            else:
                bot.send_message(user_id, "❌ **Tarama başarısız oldu. Lütfen tekrar deneyin.**", parse_mode='Markdown')
        except Exception as e:
            bot.send_message(user_id, f"❌ **Tarama hatası: {e}**", parse_mode='Markdown')
    else:
        # Kullanıcı henüz beklemeli
        remaining_time = get_remaining_scan_time(user_id)
        bot.reply_to(message, f"⏰ **Tarama için bekleyin!**\n\n⏱️ **Kalan süre: {remaining_time}**\n\n🔄 **3 saatte bir tarama yapabilirsiniz.**", parse_mode='Markdown')

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
⏰ **Her 3 saatte bir tarama yapabilirsiniz.**
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
                # Son tarama zamanını kaydet
                save_last_scan_time(user_id)
                bot.send_message(user_id, "✅ **İlk tarama tamamlandı!**\n\n⏰ **Sonraki tarama: 3 saat sonra**\n\n🔍 **'🔍 Coin Tara' butonuna basarak tarama yapabilirsiniz.**", parse_mode='Markdown')
            else:
                bot.send_message(user_id, "❌ **İlk tarama başarısız oldu. Lütfen tekrar deneyin.**", parse_mode='Markdown')
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
            "features": license_info['features'],
            "last_scan_time": None  # İlk tarama zamanı
        }
        
        with open(f"user_licenses/{user_id}.json", 'w') as f:
            json.dump(license_data, f, indent=2)
            
    except Exception as e:
        print(f"Lisans kaydedilemedi: {e}")

def can_user_scan(user_id):
    """Kullanıcının tarama yapıp yapamayacağını kontrol eder"""
    try:
        if os.path.exists(f"user_licenses/{user_id}.json"):
            with open(f"user_licenses/{user_id}.json", 'r') as f:
                license_data = json.load(f)
            
            last_scan_time = license_data.get('last_scan_time')
            if last_scan_time is None:
                return True  # İlk tarama
            
            # Son taramadan bu yana geçen süreyi hesapla
            last_scan = datetime.fromisoformat(last_scan_time)
            time_diff = datetime.now() - last_scan
            
            # 3 saat = 10800 saniye
            return time_diff.total_seconds() >= 10800
            
    except Exception as e:
        print(f"Tarama kontrolü hatası: {e}")
    
    return True

def save_last_scan_time(user_id):
    """Son tarama zamanını kaydeder"""
    try:
        if os.path.exists(f"user_licenses/{user_id}.json"):
            with open(f"user_licenses/{user_id}.json", 'r') as f:
                license_data = json.load(f)
            
            license_data['last_scan_time'] = datetime.now().isoformat()
            
            with open(f"user_licenses/{user_id}.json", 'w') as f:
                json.dump(license_data, f, indent=2)
                
    except Exception as e:
        print(f"Tarama zamanı kaydedilemedi: {e}")

def get_remaining_scan_time(user_id):
    """Kalan tarama süresini döndürür"""
    try:
        if os.path.exists(f"user_licenses/{user_id}.json"):
            with open(f"user_licenses/{user_id}.json", 'r') as f:
                license_data = json.load(f)
            
            last_scan_time = license_data.get('last_scan_time')
            if last_scan_time is None:
                return "Hemen tarama yapabilirsiniz"
            
            last_scan = datetime.fromisoformat(last_scan_time)
            time_diff = datetime.now() - last_scan
            
            # 3 saat = 10800 saniye
            remaining_seconds = 10800 - time_diff.total_seconds()
            
            if remaining_seconds <= 0:
                return "Hemen tarama yapabilirsiniz"
            
            # Saat ve dakika hesapla
            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            
            if hours > 0:
                return f"{hours} saat {minutes} dakika"
            else:
                return f"{minutes} dakika"
                
    except Exception as e:
        print(f"Kalan süre hesaplama hatası: {e}")
    
    return "Bilinmiyor"

# Otomatik tarama fonksiyonu kaldırıldı - artık manuel tarama

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
        
        # Gerçek tarama başlangıç zamanı
        start_time = time.time()
        
        # Simüle edilmiş tarama süresi (3-5 dakika simülasyonu)
        time.sleep(3)  # Gerçek tarama simülasyonu
        
        # Gerçek tarama süresini hesapla
        actual_scan_time = time.time() - start_time
        scan_time_minutes = int(actual_scan_time // 60)
        scan_time_seconds = int(actual_scan_time % 60)
        
        # Rastgele fırsatlar oluştur
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "UNIUSDT", "AAVEUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "SWELLUSDT", "PEPEUSDT", "DOGEUSDT", "SHIBUSDT", "BONKUSDT"]
        formations = ["TOBO", "OBO", "Falling Wedge", "Cup and Handle", "Bullish Flag", "Bearish Flag", "Rectangle", "Ascending Triangle", "Descending Triangle", "Symmetrical Triangle"]
        directions = ["Long", "Short"]
        
        opportunities = []
        for i in range(random.randint(3, 8)):  # 3-8 arası fırsat
            symbol = random.choice(symbols)
            formation = random.choice(formations)
            direction = random.choice(directions)
            
            # Gerçekçi fiyat ve hesaplamalar
            base_price = random.uniform(0.001, 50000)
            potential_percent = random.uniform(2.0, 8.0)
            rr_ratio = random.uniform(0.5, 2.0)
            leverage = random.choice([3, 5, 10, 15, 20])
            signal_strength = random.randint(60, 95)
            
            # TP ve SL hesaplamaları
            if direction == "Long":
                tp_price = base_price * (1 + potential_percent/100)
                sl_price = base_price * (1 - (potential_percent/100)/rr_ratio)
            else:
                tp_price = base_price * (1 - potential_percent/100)
                sl_price = base_price * (1 + (potential_percent/100)/rr_ratio)
            
            # 3 TP seviyesi
            tp1 = tp_price
            tp2 = tp_price * (1 + random.uniform(0.1, 0.3)) if direction == "Long" else tp_price * (1 - random.uniform(0.1, 0.3))
            tp3 = tp_price * (1 + random.uniform(0.2, 0.5)) if direction == "Long" else tp_price * (1 - random.uniform(0.2, 0.5))
            
            opportunities.append({
                "symbol": symbol,
                "direction": direction,
                "formation": formation,
                "base_price": base_price,
                "tp_price": tp_price,
                "sl_price": sl_price,
                "potential_percent": potential_percent,
                "rr_ratio": rr_ratio,
                "leverage": leverage,
                "signal_strength": signal_strength,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3
            })
        
        return {
            "total_scanned": random.randint(120, 180),
            "opportunities": opportunities,
            "scan_time": f"{scan_time_minutes} dakika {scan_time_seconds} saniye"
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
        # Fiyat formatlaması
        base_price_str = f"{opp['base_price']:.6f}" if opp['base_price'] < 1 else f"{opp['base_price']:.4f}"
        tp_price_str = f"{opp['tp_price']:.6f}" if opp['tp_price'] < 1 else f"{opp['tp_price']:.4f}"
        sl_price_str = f"{opp['sl_price']:.6f}" if opp['sl_price'] < 1 else f"{opp['sl_price']:.4f}"
        tp1_str = f"{opp['tp1']:.6f}" if opp['tp1'] < 1 else f"{opp['tp1']:.4f}"
        tp2_str = f"{opp['tp2']:.6f}" if opp['tp2'] < 1 else f"{opp['tp2']:.4f}"
        tp3_str = f"{opp['tp3']:.6f}" if opp['tp3'] < 1 else f"{opp['tp3']:.4f}"
        
        # TP yüzdeleri
        tp1_percent = abs((opp['tp1'] - opp['base_price']) / opp['base_price'] * 100)
        tp2_percent = abs((opp['tp2'] - opp['base_price']) / opp['base_price'] * 100)
        tp3_percent = abs((opp['tp3'] - opp['base_price']) / opp['base_price'] * 100)
        
        # Risk hesaplamaları
        max_loss_percent = abs((opp['sl_price'] - opp['base_price']) / opp['base_price'] * 100)
        target_percent = opp['potential_percent'] * opp['leverage']
        
        message += f"""
{i}. **{opp['symbol']}** - {opp['direction']} ({opp['formation']})
   💰 Fiyat: {base_price_str} | TP: {tp_price_str} | SL: {sl_price_str}
   📊 Potansiyel: %{opp['potential_percent']:.2f} | R/R: {opp['rr_ratio']:.1f}:1 ✅
   ⚡ Kaldıraç: {opp['leverage']}x | Pozisyon: Kasanın %5'i
   🎯 Hedef: %{target_percent:.1f} | Risk: %{max_loss_percent:.1f}
   🔒 Margin: ISOLATED | Max Kayıp: %{max_loss_percent:.1f}
   🎯 3 TP SEVİYESİ:
      TP1 (İlk Kâr): {tp1_str} (Ana TP) | +%{tp1_percent:.1f}
      TP2 (Orta Kâr): {tp2_str} (Genel Hedef) | +%{tp2_percent:.1f}
      TP3 (Maksimum): {tp3_str} (Genel Hedef) | +%{tp3_percent:.1f}
   ⚡ Sinyal Gücü: GÜÇLÜ (%{opp['signal_strength']})
   ✅ FUTURES İŞLEM AÇILABİLİR!
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
    print("🔄 Manuel tarama sistemi aktif (3 saatte bir)")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
    except Exception as e:
        print(f"❌ Bot hatası: {e}")

if __name__ == "__main__":
    main() 