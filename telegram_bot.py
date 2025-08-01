import telebot
from telebot import types
import json
import os
from datetime import datetime
import threading
import time
import concurrent.futures
from license_manager import LicenseManager

# Environment variables'dan direkt al
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

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
    license_data = check_user_license(user_id)
    
    if license_data:
        # Kullanıcının lisansı var
        license_info = license_data
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
    license_data = check_user_license(user_id)
    
    if license_data:
        license_info = license_data
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
@ApfelTradingAdmin ile iletişime geçin.
"""
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['scan'])
def start_scan(message):
    """Manuel tarama başlat"""
    user_id = message.from_user.id
    
    # Kullanıcının lisansını kontrol et
    license_data = check_user_license(user_id)
    if not license_data:
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
        print(f"🔍 Tarama başlatılıyor - Kullanıcı: {user_id}")
        
        # Tarama yap
        scan_results = perform_scan()
        print(f"📊 Tarama sonucu: {scan_results}")
        
        if scan_results and len(scan_results) > 0:
            print(f"✅ {len(scan_results)} fırsat bulundu")
            send_scan_results_to_user(user_id, scan_results)
            # Son tarama zamanını kaydet
            save_last_scan_time(user_id)
            bot.send_message(user_id, "✅ **Tarama tamamlandı!**\n\n⏰ **Sonraki tarama: 3 saat sonra**", parse_mode='Markdown')
        else:
            print("❌ Tarama sonucu boş")
            bot.send_message(user_id, "❌ **Tarama başarısız oldu. Lütfen tekrar deneyin.**", parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Tarama hatası: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
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
@ApfelTradingAdmin ile iletişime geçin.

📦 Paketler:
• 1 Aylık: $100
• 3 Aylık: $200
• Sınırsız: $500

🔑 Tekrar denemek için lisans anahtarınızı gönderin:
"""
        
        # Lisans giriş durumunu koru
        user_states[user_id] = "waiting_license"
        
        # Lisans giriş butonu
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🔑 Lisans Anahtarı Gir"))
        markup.row(types.KeyboardButton("💬 Lisans Satın Al"))
        
        bot.reply_to(message, error_text, reply_markup=markup)
    
    # Kullanıcı durumunu temizle - sadece başarılı lisans girişinde
    if is_valid:
        user_states.pop(user_id, None)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Diğer tüm mesajlar"""
    user_id = message.from_user.id
    license_data = check_user_license(user_id)
    
    if not license_data:
        # Lisans yoksa lisans anahtarı iste
        bot.reply_to(message, "🔑 **Lisans Anahtarınızı Gönderin:**\n\nLisans anahtarınızı buraya yazın.\n\n💬 **Lisans Satın Almak İçin:** @ApfelTradingAdmin")
    else:
        # Lisans varsa yardım mesajı
        bot.reply_to(message, "❓ Yardım için /help yazın.\n🔍 Coin taraması için '🔍 Coin Tara' butonuna basın.")

def save_user_license(user_id, license_info):
    """Kullanıcı lisansını persistent storage'a kaydeder"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        os.makedirs(storage_dir, exist_ok=True)
        
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
        
        # Persistent storage'a kaydet
        with open(f"{storage_dir}/user_{user_id}.json", 'w') as f:
            json.dump(license_data, f, indent=2)
            
        print(f"✅ Lisans kaydedildi: user_{user_id}.json")
            
    except Exception as e:
        print(f"Lisans kaydedilemedi: {e}")

def check_user_license(user_id):
    """Kullanıcının lisans durumunu kontrol eder"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        license_file = f"{storage_dir}/user_{user_id}.json"
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                user_license = json.load(f)
            
            # Lisans süresini kontrol et
            expiry_date = user_license.get('expiry_date')
            if expiry_date:
                expiry = datetime.fromisoformat(expiry_date)
                if datetime.now() > expiry:
                    return None  # Süresi dolmuş
            
            return user_license
        
        return None
        
    except Exception as e:
        print(f"Lisans kontrolü hatası: {e}")
        return None

def can_user_scan(user_id):
    """Kullanıcının tarama yapıp yapamayacağını kontrol eder"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        license_file = f"{storage_dir}/user_{user_id}.json"
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                user_license = json.load(f)
            
            last_scan_time = user_license.get('last_scan_time')
            if last_scan_time is None:
                return True  # İlk tarama
            
            # Son taramadan bu yana geçen süreyi hesapla
            last_scan = datetime.fromisoformat(last_scan_time)
            time_diff = datetime.now() - last_scan
            
            # 3 saat = 10800 saniye
            return time_diff.total_seconds() >= 10800
        
        return False
        
    except Exception as e:
        print(f"Tarama kontrolü hatası: {e}")
    
    return False

def save_last_scan_time(user_id):
    """Son tarama zamanını persistent storage'a kaydeder"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        license_file = f"{storage_dir}/user_{user_id}.json"
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                user_license = json.load(f)
            
            user_license['last_scan_time'] = datetime.now().isoformat()
            
            with open(license_file, 'w') as f:
                json.dump(user_license, f, indent=2)
                
    except Exception as e:
        print(f"Tarama zamanı kaydedilemedi: {e}")

def get_remaining_scan_time(user_id):
    """Kalan tarama süresini döndürür"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        license_file = f"{storage_dir}/user_{user_id}.json"
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                user_license = json.load(f)
            
            last_scan_time = user_license.get('last_scan_time')
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
        
        return "Lisans bulunamadı"
            
    except Exception as e:
        print(f"Kalan süre hesaplama hatası: {e}")
    
    return "Bilinmiyor"

# Otomatik tarama fonksiyonu kaldırıldı - artık manuel tarama

def get_active_users():
    """Aktif kullanıcıları döndürür"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        
        if not os.path.exists(storage_dir):
            return []
        
        active_users = []
        for filename in os.listdir(storage_dir):
            if filename.startswith("user_") and filename.endswith(".json"):
                try:
                    with open(f"{storage_dir}/{filename}", 'r') as f:
                        user_license = json.load(f)
                    
                    expiry_date = user_license.get('expiry_date')
                    if expiry_date:
                        expiry = datetime.fromisoformat(expiry_date)
                        if datetime.now() <= expiry:
                            active_users.append({
                                'user_id': user_license.get('user_id'),
                                'type': user_license.get('type'),
                                'activated_date': user_license.get('activated_date'),
                                'expiry_date': expiry_date
                            })
                except:
                    continue
        
        return active_users
        
    except Exception as e:
        print(f"Aktif kullanıcı listesi hatası: {e}")
        return []

def is_license_already_used(license_key, current_user_id):
    """Lisansın başka bir kullanıcı tarafından kullanılıp kullanılmadığını kontrol et"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        
        if not os.path.exists(storage_dir):
            return False
        
        for filename in os.listdir(storage_dir):
            if filename.startswith("user_") and filename.endswith(".json"):
                try:
                    with open(f"{storage_dir}/{filename}", 'r') as f:
                        user_license = json.load(f)
                    
                    user_id = user_license.get('user_id')
                    if str(user_id) != str(current_user_id):  # Kendisi değilse
                        if 'license_key' in user_license and user_license['license_key'] == license_key:
                            return True  # Lisans başka bir kullanıcı tarafından kullanılıyor
                except:
                    continue
        
        return False  # Lisans kullanılmıyor
        
    except Exception as e:
        print(f"Lisans kullanım kontrolü hatası: {e}")
        return False

def perform_simple_test():
    """Basit test fonksiyonu"""
    try:
        print("🧪 Basit test başlatılıyor...")
        
        # Test verileri
        test_results = [
            {
                'symbol': 'BTCUSDT',
                'yön': 'Long',
                'formasyon': 'TOBO',
                'price': 50000,
                'tp': 52000,
                'sl': 48000,
                'tpfark': 0.04,
                'risk_analysis': {
                    'leverage': '5x',
                    'position_size': 'Kasanın %5\'i',
                    'potential_gain': '%4.0',
                    'risk_amount': '%1.0',
                    'max_loss': '%1.0'
                },
                'signal_strength': 85,
                'rr_ratio': 4.0
            },
            {
                'symbol': 'ETHUSDT',
                'yön': 'Short',
                'formasyon': 'OBO',
                'price': 3000,
                'tp': 2850,
                'sl': 3150,
                'tpfark': 0.05,
                'risk_analysis': {
                    'leverage': '3x',
                    'position_size': 'Kasanın %3\'ü',
                    'potential_gain': '%5.0',
                    'risk_amount': '%1.5',
                    'max_loss': '%1.5'
                },
                'signal_strength': 78,
                'rr_ratio': 3.3
            }
        ]
        
        print(f"✅ Test sonucu: {len(test_results)} fırsat")
        return {
            "total_scanned": 2,
            "opportunities": test_results,
            "scan_time": "0 dakika 5 saniye"
        }
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        return None

def perform_scan():
    """botanlik.py ile gerçek analiz"""
    try:
        import time
        import traceback
        
        # Tarama başlangıç zamanı
        start_time = time.time()
        
        print("🔍 botanlik.py ile gerçek analiz başlatılıyor...")
        
        try:
            # botanlik.py'den get_scan_results fonksiyonunu import et
            from botanlik import get_scan_results
            print("✅ botanlik.py import başarılı")
        except Exception as import_error:
            print(f"❌ Import hatası: {import_error}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return None
        
        # botanlik.py'nin get_scan_results fonksiyonunu çağır
        scan_results = get_scan_results()
        
        if scan_results:
            # Tarama süresini hesapla
            scan_time = time.time() - start_time
            scan_time_minutes = int(scan_time // 60)
            scan_time_seconds = int(scan_time % 60)
            
            # Sonuçları formatla
            return {
                "total_scanned": scan_results.get("total_scanned", 0),
                "opportunities": scan_results.get("opportunities", []),
                "scan_time": f"{scan_time_minutes} dakika {scan_time_seconds} saniye"
            }
        else:
            print("❌ botanlik.py'den sonuç alınamadı")
            return None
            
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
        
        # Risk analizi - Sabit 5x kaldıraç
        leverage = '5x'  # Sabit 5x kaldıraç
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