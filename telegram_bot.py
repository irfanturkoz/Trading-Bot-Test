import telebot
from telebot import types
import json
import os
from datetime import datetime
import threading
import time
import concurrent.futures
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
@ApfelTradingAdmin ile iletişime geçin.

📦 **Paketler:**
• 1 Aylık: $100
• 3 Aylık: $200
• Sınırsız: $500
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

💬 **Destek:** @ApfelTradingAdmin
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
    # Asenkron tarama başlat
    scan_thread = threading.Thread(target=start_scan_async, args=(message,))
    scan_thread.daemon = True
    scan_thread.start()

def start_scan_async(message):
    """Asenkron tarama işlemi"""
    user_id = message.from_user.id
    
    # Tarama başladı mesajı
    bot.reply_to(message, "🚀 **TARAMA BAŞLATILIYOR**\n\n⏱️ **Yaklaşık 2-3 dakika içerisinde uygun işlemler gösterilecek...**", parse_mode='Markdown')
    
    try:
        # Tarama yap
        scan_results = perform_scan()
        if scan_results:
            send_scan_results_to_user(user_id, scan_results)
            # Son tarama zamanını kaydet
            save_last_scan_time(user_id)
            bot.send_message(user_id, "✅ **Tarama tamamlandı!**\n\n⏰ **Sonraki tarama: 3 saat sonra**", parse_mode='Markdown')
        else:
            bot.send_message(user_id, "❌ **Tarama başarısız oldu. Lütfen tekrar deneyin.**", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(user_id, f"❌ **Tarama hatası:** {e}", parse_mode='Markdown')

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
• 1 Aylık: $100
• 3 Aylık: $200 (İndirimli)
• Sınırsız: $500

✅ **Özellikler:**
• Otomatik coin tarama
• Telegram bildirimleri
• Formasyon analizi
• Risk/ödül hesaplama
• 3 TP seviyesi

🔗 **İletişim:** @ApfelTradingAdmin
"""
    bot.reply_to(message, buy_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_license")
def handle_license_input(message):
    """Lisans anahtarı girişi"""
    user_id = message.from_user.id
    license_key = message.text.strip()
    
    # Debug mesajı
    print(f"🔍 Lisans kontrolü: {license_key}")
    
    # Lisans anahtarını doğrula
    try:
        is_valid, result = license_manager.validate_license(license_key)
        print(f"✅ Lisans sonucu: {is_valid}, {result}")
    except Exception as e:
        print(f"❌ Lisans kontrol hatası: {e}")
        bot.reply_to(message, f"❌ **Lisans kontrol hatası:** {e}", parse_mode='Markdown')
        return
    
    if is_valid:
        # Lisans geçerli
        license_info = result
        
        # Lisansın başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et
        if is_license_already_used(license_key, user_id):
            bot.reply_to(message, "❌ **Bu lisans anahtarı başka bir kullanıcı tarafından kullanılıyor!**\n\n🔑 Farklı bir lisans anahtarı deneyin veya @ApfelTradingAdmin ile iletişime geçin.", parse_mode='Markdown')
            return
        
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

📱 **Destek:** @ApfelTradingAdmin
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


def is_license_already_used(license_key, current_user_id):
    """Lisansın başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et"""
    try:
        if os.path.exists("user_licenses"):
            for filename in os.listdir("user_licenses"):
                if filename.endswith(".json"):
                    user_id = filename.replace(".json", "")
                    if str(user_id) != str(current_user_id):  # Kendisi değilse
                        try:
                            with open(f"user_licenses/{filename}", 'r') as f:
                                user_data = json.load(f)
                                if 'license_key' in user_data and user_data['license_key'] == license_key:
                                    return True  # Lisans başka bir kullanıcı tarafından kullanılıyor
                        except:
                            continue
        
        return False  # Lisans kullanılmıyor
    except Exception as e:
        print(f"Lisans kontrol hatası: {e}")
        return False  # Hata varsa kullanılabilir

def perform_scan():
    """botanlik2.py ile gerçek analiz"""
    try:
        import time
        import random
        import traceback
        
        # Tarama başlangıç zamanı
        start_time = time.time()
        
        print("🔍 Import işlemleri başlatılıyor...")
        
        try:
            # botanlik2.py'den gerekli fonksiyonları import et
            from botanlik2 import get_usdt_symbols, get_current_price, calculate_optimal_risk
            from botanlik2 import find_all_tobo, find_all_obo, detect_falling_wedge
            from botanlik2 import find_rectangle, find_ascending_triangle, find_descending_triangle
            from botanlik2 import find_symmetrical_triangle, find_broadening_formation
            from botanlik2 import calculate_fibonacci_levels, calculate_macd, calculate_bollinger_bands
            from botanlik2 import calculate_stochastic, calculate_adx, format_price
            from data_fetcher import fetch_ohlcv
            print("✅ Import işlemleri başarılı")
        except Exception as import_error:
            print(f"❌ Import hatası: {import_error}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            print("🔄 Basit analiz moduna geçiliyor...")
            
            # Basit analiz modu
            return perform_simple_scan()
        
        print("🔍 botanlik2.py ile gerçek analiz başlatılıyor...")
        
        try:
            # Tüm USDT sembollerini al
            symbols = get_usdt_symbols()
            print(f"📊 {len(symbols)} coin paralel analiz ediliyor...")
        except Exception as symbols_error:
            print(f"❌ Sembol alma hatası: {symbols_error}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return None
        
        firsatlar = []
        
        # Paralel analiz ile tüm coinleri işle
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Tüm sembolleri paralel olarak analiz et
            future_to_symbol = {executor.submit(analyze_symbol, symbol): symbol for symbol in symbols}
            
            # Sonuçları topla
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result:
                        firsatlar.append(result)
                        print(f"✅ {symbol} analiz edildi - {len(firsatlar)} fırsat bulundu")
                except Exception as e:
                    print(f"❌ {symbol} analiz hatası: {e}")
                    continue
        
        def analyze_symbol(symbol, interval='4h'):
            try:
                current_price = get_current_price(symbol)
                if not current_price:
                    return None
                
                df = fetch_ohlcv(symbol, interval)
                if df is None or df.empty:
                    return None
                
                # MA hesaplamaları
                df['MA7'] = df['close'].rolling(window=7).mean()
                df['MA25'] = df['close'].rolling(window=25).mean()
                df['MA50'] = df['close'].rolling(window=50).mean()
                df['MA99'] = df['close'].rolling(window=99).mean()
                
                ma_trend = None
                if df['MA7'].iloc[-1] > df['MA25'].iloc[-1] > df['MA50'].iloc[-1] > df['MA99'].iloc[-1]:
                    ma_trend = 'Güçlü Yükseliş'
                elif df['MA7'].iloc[-1] < df['MA25'].iloc[-1] < df['MA50'].iloc[-1] < df['MA99'].iloc[-1]:
                    ma_trend = 'Güçlü Düşüş'
                else:
                    ma_trend = 'Kararsız'
                
                fibo_levels, fibo_high, fibo_low = calculate_fibonacci_levels(df)
                
                # Tüm formasyonları analiz et
                all_tobo = find_all_tobo(df)
                all_obo = find_all_obo(df)
                falling_wedge = detect_falling_wedge(df)
                rectangle = find_rectangle(df)
                ascending_triangle = find_ascending_triangle(df)
                descending_triangle = find_descending_triangle(df)
                symmetrical_triangle = find_symmetrical_triangle(df)
                broadening = find_broadening_formation(df)
                
                # En güçlü formasyonu belirle
                formations = []
                
                if all_tobo:
                    tobo = all_tobo[-1]
                    formations.append({
                        'type': 'TOBO',
                        'data': tobo,
                        'direction': 'Long',
                        'tp': fibo_levels.get('0.382', current_price * 1.05),
                        'sl': tobo['neckline']
                    })
                
                if all_obo:
                    obo = all_obo[-1]
                    formations.append({
                        'type': 'OBO',
                        'data': obo,
                        'direction': 'Short',
                        'tp': fibo_levels.get('0.618', current_price * 0.95),
                        'sl': obo['neckline']
                    })
                
                if falling_wedge:
                    formations.append({
                        'type': 'Falling Wedge',
                        'data': falling_wedge,
                        'direction': 'Long',
                        'tp': falling_wedge.get('tp', current_price * 1.05),
                        'sl': falling_wedge.get('sl', current_price * 0.95)
                    })
                
                if rectangle and 'resistance' in rectangle and 'support' in rectangle:
                    formations.append({
                        'type': 'Rectangle',
                        'data': rectangle,
                        'direction': 'Long' if current_price > rectangle['resistance'] else 'Short',
                        'tp': rectangle['resistance'] if current_price > rectangle['resistance'] else rectangle['support'],
                        'sl': rectangle['support'] if current_price > rectangle['resistance'] else rectangle['resistance']
                    })
                
                if ascending_triangle and 'resistance' in ascending_triangle and 'support' in ascending_triangle:
                    formations.append({
                        'type': 'Ascending Triangle',
                        'data': ascending_triangle,
                        'direction': 'Long',
                        'tp': ascending_triangle['resistance'],
                        'sl': ascending_triangle['support']
                    })
                
                if descending_triangle and 'support' in descending_triangle and 'resistance' in descending_triangle:
                    formations.append({
                        'type': 'Descending Triangle',
                        'data': descending_triangle,
                        'direction': 'Short',
                        'tp': descending_triangle['support'],
                        'sl': descending_triangle['resistance']
                    })
                
                if symmetrical_triangle and 'upper' in symmetrical_triangle and 'lower' in symmetrical_triangle:
                    formations.append({
                        'type': 'Symmetrical Triangle',
                        'data': symmetrical_triangle,
                        'direction': 'Long' if ma_trend == 'Güçlü Yükseliş' else 'Short',
                        'tp': symmetrical_triangle['upper'],
                        'sl': symmetrical_triangle['lower']
                    })
                
                if broadening and 'current_resistance' in broadening and 'current_support' in broadening:
                    formations.append({
                        'type': 'Broadening Formation',
                        'data': broadening,
                        'direction': 'Long' if broadening['breakout_up'] else 'Short',
                        'tp': broadening['current_resistance'] if broadening['breakout_up'] else broadening['current_support'],
                        'sl': broadening['current_support'] if broadening['breakout_up'] else broadening['current_resistance']
                    })
                
                # En iyi formasyonu seç
                if not formations:
                    return None
                
                # R/R oranına göre sırala
                best_formation = None
                best_rr = 0
                
                for formation in formations:
                    tp = formation['tp']
                    sl = formation['sl']
                    
                    if formation['direction'] == 'Long':
                        if tp > current_price > sl:
                            rr = (tp - current_price) / (current_price - sl)
                        else:
                            continue
                    else:
                        if sl > current_price > tp:
                            rr = (current_price - tp) / (sl - current_price)
                        else:
                            continue
                    
                    if rr > best_rr and rr >= 0.5 and rr <= 3.0:  # Minimum 0.5:1, Maksimum 3:1 R/R
                        best_rr = rr
                        best_formation = formation
                
                if not best_formation:
                    return None
                
                # Risk analizi
                risk_analysis = calculate_optimal_risk(
                    symbol, current_price, best_formation['tp'], 
                    best_formation['sl'], best_formation['direction']
                )
                
                # Sinyal gücü hesapla
                macd_data = calculate_macd(df)
                bb_data = calculate_bollinger_bands(df)
                stoch_data = calculate_stochastic(df)
                adx_data = calculate_adx(df)
                
                signal_strength = 70  # Varsayılan
                if macd_data and 'Yükseliş' in ma_trend and best_formation['direction'] == 'Long':
                    signal_strength += 10
                if adx_data and adx_data.get('trend_direction') == 'Bullish' and best_formation['direction'] == 'Long':
                    signal_strength += 10
                
                return {
                    'symbol': symbol,
                    'yön': best_formation['direction'],
                    'formasyon': best_formation['type'],
                    'price': current_price,
                    'tp': best_formation['tp'],
                    'sl': best_formation['sl'],
                    'tpfark': abs(best_formation['tp'] - current_price) / current_price,
                    'risk_analysis': risk_analysis,
                    'signal_strength': min(95, signal_strength),
                    'rr_ratio': best_rr,
                    'tp_levels': None  # botanlik2.py'den gelecek
                }
                
            except Exception as e:
                print(f"Hata {symbol}: {e}")
                return None
        
        # Sıralı analiz - düzgün ve sağlıklı
        print("🔍 Sıralı analiz başlatılıyor... (3-4 dakika sürecek)")
        
        completed = 0
        for symbol in symbols:
            try:
                result = analyze_symbol(symbol)
                completed += 1
                
                # İlerleme göster
                if completed % 20 == 0:
                    progress = (completed / len(symbols)) * 100
                    print(f"📊 İlerleme: %{progress:.1f} ({completed}/{len(symbols)})")
                
                if result:
                    firsatlar.append(result)
                    print(f"✅ {symbol}: {result['formasyon']} - R/R: {result['rr_ratio']:.2f}")
                
                # Her 10 coin'de bir kısa bekleme (API limitlerini aşmamak için)
                if completed % 10 == 0:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ {symbol} analiz hatası: {e}")
                completed += 1
                continue
        
        # En iyi 10 fırsatı sırala
        firsatlar = sorted(firsatlar, key=lambda x: x['rr_ratio'], reverse=True)[:10]
        
        # Tarama süresini hesapla
        scan_time = time.time() - start_time
        scan_time_minutes = int(scan_time // 60)
        scan_time_seconds = int(scan_time % 60)
        
        return {
            "total_scanned": len(symbols),
            "opportunities": firsatlar,
            "scan_time": f"{scan_time_minutes} dakika {scan_time_seconds} saniye"
        }
        
    except Exception as e:
        print(f"❌ Tarama hatası: {e}")
        print(f"🔍 Detaylı hata: {traceback.format_exc()}")
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
        # botanlik2.py formatından veri al
        symbol = opp.get('symbol', 'UNKNOWN')
        direction = opp.get('yön', 'Unknown')
        formation = opp.get('formasyon', 'Unknown')
        price = opp.get('price', 0)
        tp = opp.get('tp', 0)
        sl = opp.get('sl', 0)
        tpfark = opp.get('tpfark', 0)
        risk_analysis = opp.get('risk_analysis', {})
        signal_strength = opp.get('signal_strength', 50)
        rr_ratio = opp.get('rr_ratio', 0)
        
        # Fiyat formatlaması (botanlik2.py format_price fonksiyonu gibi)
        def format_price_display(price):
            if price == 0:
                return '0'
            elif price < 0.0001:
                return f"{price:.8f}"
            elif price < 1:
                return f"{price:.6f}"
            elif price < 10:
                return f"{price:.4f}"
            elif price < 100:
                return f"{price:.3f}"
            else:
                return f"{price:.2f}"
        
        price_str = format_price_display(price)
        tp_str = format_price_display(tp)
        sl_str = format_price_display(sl)
        
        # Risk analizi - botanlik2.py'den gelen veriyi doğru kullan
        leverage = risk_analysis.get('leverage', '5x')
        position_size = risk_analysis.get('position_size', 'Kasanın %5\'i')
        potential_gain = risk_analysis.get('potential_gain', '%0.0')
        risk_amount = risk_analysis.get('risk_amount', '%0.0')
        max_loss = risk_analysis.get('max_loss', '%0.0')
        
        # R/R oranını botanlik2.py'den al, yoksa hesapla
        if 'rr_ratio' in opp:
            rr_ratio = opp['rr_ratio']
            risk_reward = f"{rr_ratio:.1f}:1"
        else:
            risk_reward = risk_analysis.get('risk_reward', '0.0:1')
        
        # Sinyal gücü emoji
        if signal_strength >= 80:
            strength_emoji = "🔥"
            strength_text = "ÇOK GÜÇLÜ"
        elif signal_strength >= 70:
            strength_emoji = "⚡"
            strength_text = "GÜÇLÜ"
        elif signal_strength >= 60:
            strength_emoji = "📊"
            strength_text = "ORTA"
        else:
            strength_emoji = "📈"
            strength_text = "ZAYIF"
        
        # TP seviyeleri varsa göster
        tp_levels_text = ""
        if 'tp_levels' in opp and opp['tp_levels']:
            tp_levels = opp['tp_levels']
            tp_levels_text = f"""
   🎯 3 TP SEVİYESİ:
      TP1 (İlk Kâr): {format_price_display(tp_levels.get('tp1', tp))} | +%{tpfark*100:.1f}
      TP2 (Orta Kâr): {format_price_display(tp_levels.get('tp2', tp))} | +%{(tp_levels.get('tp2', tp)/price-1)*100:.1f}
      TP3 (Maksimum): {format_price_display(tp_levels.get('tp3', tp))} | +%{(tp_levels.get('tp3', tp)/price-1)*100:.1f}"""
        
        message += f"""
{i}. **{symbol}** - {direction} ({formation})
   💰 Fiyat: {price_str} | TP: {tp_str} | SL: {sl_str}
   📊 Potansiyel: %{tpfark*100:.2f} | R/R: {risk_reward} ✅
   ⚡ Kaldıraç: {leverage} | Pozisyon: {position_size}
   🎯 Hedef: {potential_gain} | Risk: {risk_amount}
   🔒 Margin: ISOLATED | Max Kayıp: {max_loss}{tp_levels_text}
   {strength_emoji} Sinyal Gücü: {strength_text} (%{signal_strength})
   ✅ FUTURES İŞLEM AÇILABİLİR!
"""
    
    message += """
📱 **Detaylı analiz için @ApfelTradingAdmin ile iletişime geçin!**
"""
    
    try:
        bot.send_message(user_id, message, parse_mode='Markdown')
    except Exception as e:
        print(f"Kullanıcı {user_id} için mesaj gönderilemedi: {e}")

def main():
    """Bot'u başlat"""
    print("🤖 Telegram Bot Başlatılıyor...")
    print(f"📱 Bot: @apfel_trading3_bot")
    print(f"🔑 Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print("✅ Bot çalışıyor! Ctrl+C ile durdurun.")
    print("🔄 Manuel tarama sistemi aktif (3 saatte bir)")
    
    try:
        # Webhook'u temizle
        try:
            bot.remove_webhook()
            print("✅ Webhook temizlendi")
        except:
            pass
        
        # Bot'u başlat
        bot.polling(none_stop=True, timeout=60)
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
    except Exception as e:
        print(f"❌ Bot hatası: {e}")
        if "Conflict" in str(e):
            print("⚠️ Conflict hatası! 10 saniye bekleniyor...")
            time.sleep(10)
            main()  # Tekrar dene

# Bot'u başlat
if __name__ == "__main__":
    main() 