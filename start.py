import threading
import time
import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
import telebot
from dotenv import load_dotenv
from license_manager import LicenseManager

# .env dosyasını yükle
load_dotenv()

# Flask app
app = Flask(__name__)

# Bot token'ını al
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
    exit(1)

# Bot'u oluştur
bot = telebot.TeleBot(BOT_TOKEN)

# Lisans yöneticisi
license_manager = LicenseManager()

# Bot durumu
bot_status = {
    "running": False,
    "last_run": None,
    "message": "Bot başlatılmadı"
}

# Kullanıcı durumları
user_states = {}

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
    
    # Lisans kontrolü
    license_data = check_user_license(user_id)
    
    if license_data:
        # Kullanıcının lisansı var
        license_info = license_data
        welcome_text = f"""
🤖 **Hoş Geldiniz {message.from_user.first_name}!**

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
        
    else:
        # Kullanıcının lisansı yok
        welcome_text = f"""
🤖 **Hoş Geldiniz {message.from_user.first_name}!**

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
    
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status_command(message):
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
            from datetime import datetime
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
def scan_command(message):
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

@bot.message_handler(commands=['help'])
def help_command(message):
    """Yardım mesajı"""
    help_text = """
❓ **Yardım**

🔍 **/scan:** Otomatik coin taraması başlatır
📊 **/status:** Mevcut lisans bilgilerini gösterir
🔑 **Lisans Anahtarı Gir:** Yeni lisans anahtarı girmenizi sağlar
🧪 **/test:** Bot test komutu

💬 **Destek:** @ApfelTradingAdmin
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def test_command(message):
    """Test komutu"""
    bot.reply_to(message, "✅ Bot çalışıyor! Test başarılı!")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_license")
def handle_license_input(message):
    """Lisans anahtarı girişi"""
    user_id = message.from_user.id
    license_key = message.text.strip()
    
    # Lisans anahtarını doğrula
    try:
        is_valid, result = license_manager.validate_license(license_key)
    except Exception as e:
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

🔍 **/scan** komutu ile tarama başlatabilirsiniz.
⏰ **Her 3 saatte bir tarama yapabilirsiniz.**

📱 **Destek:** @ApfelTradingAdmin
"""
        
        bot.reply_to(message, success_text, parse_mode='Markdown')
        
        # İlk taramayı hemen başlat
        bot.send_message(user_id, "🚀 **TARAMA BAŞLATILIYOR**\n\n⏱️ **Yaklaşık 3-5 dakika içerisinde uygun işlemler gösterilecek...**", parse_mode='Markdown')
        
        try:
            # İlk tarama yap
            scan_results = perform_scan()
            if scan_results:
                send_scan_results_to_user(user_id, scan_results)
                # Son tarama zamanını kaydet
                save_last_scan_time(user_id)
                bot.send_message(user_id, "✅ **İlk tarama tamamlandı!**\n\n⏰ **Sonraki tarama: 3 saat sonra**\n\n🔍 **'/scan' komutu ile tarama yapabilirsiniz.**", parse_mode='Markdown')
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
        
        bot.reply_to(message, error_text, parse_mode='Markdown')
    
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
        bot.reply_to(message, "❓ Yardım için /help yazın.\n🔍 Coin taraması için /scan komutunu kullanın.")

# Lisans yönetimi fonksiyonları
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
            
        # Log'u azalt - sadece hata durumunda
        # print(f"✅ Lisans kaydedildi: user_{user_id}.json")
            
    except Exception as e:
        print(f"❌ Lisans kaydedilemedi: {e}")

def check_user_license(user_id):
    """Kullanıcının lisans durumunu kontrol eder"""
    try:
        # Railway persistent storage dizini
        storage_dir = "/tmp/persistent_storage"
        license_file = f"{storage_dir}/user_{user_id}.json"
        
        if os.path.exists(license_file):
            with open(license_file, 'r') as f:
                user_license = json.load(f)
            
            # Lisans anahtarını kontrol et
            license_key = user_license.get('license_key')
            if license_key:
                # Lisans dosyasını yeniden yükle ve kontrol et
                try:
                    with open('licenses.json', 'r', encoding='utf-8') as f:
                        licenses = json.load(f)
                    
                    # Lisans hala mevcut ve aktif mi?
                    if license_key not in licenses or not licenses[license_key].get('active', True):
                        # Lisans silinmiş veya pasif yapılmış
                        # print(f"❌ Lisans {license_key} silinmiş veya pasif: {user_id}")
                        # Kullanıcı dosyasını sil
                        os.remove(license_file)
                        return None
                except Exception as e:
                    # print(f"Lisans dosyası kontrol hatası: {e}")
                    pass
            
            # Lisans süresini kontrol et
            expiry_date = user_license.get('expiry_date')
            if expiry_date:
                from datetime import datetime
                expiry = datetime.fromisoformat(expiry_date)
                if datetime.now() > expiry:
                    # print(f"❌ Lisans süresi dolmuş: {user_id}")
                    # Kullanıcı dosyasını sil
                    os.remove(license_file)
                    return None
            
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
            from datetime import datetime
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
            
            from datetime import datetime
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

def perform_scan():
    """botanlik.py ile gerçek analiz"""
    try:
        import time
        import traceback
        
        # Tarama başlangıç zamanı
        start_time = time.time()
        
        # print("🔍 botanlik.py ile gerçek analiz başlatılıyor...")
        
        try:
            # botanlik.py'den get_scan_results fonksiyonunu import et
            from botanlik import get_scan_results
            # print("✅ botanlik.py import başarılı")
        except Exception as import_error:
            print(f"❌ Import hatası: {import_error}")
            return None
        
        # print("🚀 get_scan_results() fonksiyonu çağrılıyor...")
        
        # botanlik.py'nin get_scan_results fonksiyonunu çağır
        scan_results = get_scan_results()
        
        print(f"📊 get_scan_results() sonucu: {scan_results}")
        print(f"📊 Opportunities sayısı: {len(scan_results.get('opportunities', [])) if scan_results else 0}")
        
        if scan_results:
            # Tarama süresini hesapla
            scan_time = time.time() - start_time
            scan_time_minutes = int(scan_time // 60)
            scan_time_seconds = int(scan_time % 60)
            
            print(f"⏱️ Tarama tamamlandı: {scan_time_minutes}dk {scan_time_seconds}s - {len(scan_results.get('opportunities', []))} fırsat")
            
            # Sonuçları formatla
            return {
                "total_scanned": scan_results.get("total_scanned", 0),
                "opportunities": scan_results.get("opportunities", []),
                "scan_time": f"{scan_time_minutes} dakika {scan_time_seconds} saniye"
            }
        else:
            print("❌ Tarama sonucu alınamadı")
            return None
            
    except Exception as e:
        print(f"❌ Tarama hatası: {e}")
        return None

def send_scan_results_to_user(user_id, results):
    """Kullanıcıya tarama sonuçlarını gönder"""
    print(f"📤 send_scan_results_to_user çağrıldı: user_id={user_id}")
    print(f"📊 Results: {results}")
    
    if not results:
        print("❌ Results boş, mesaj gönderilmeyecek")
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
        
        # Fiyat formatlaması
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
        print(f"📤 Mesaj gönderiliyor...")
        print(f"📝 Mesaj uzunluğu: {len(message)} karakter")
        
        # Mesajı parçalara böl (Telegram 4096 karakter limiti)
        if len(message) > 4000:
            print(f"⚠️ Mesaj çok uzun, parçalara bölünüyor...")
            parts = []
            current_part = ""
            
            for line in message.split('\n'):
                if len(current_part + line + '\n') > 4000:
                    if current_part:
                        parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            for i, part in enumerate(parts, 1):
                print(f"📤 Parça {i}/{len(parts)} gönderiliyor...")
                bot.send_message(user_id, part, parse_mode='Markdown')
        else:
            bot.send_message(user_id, message, parse_mode='Markdown')
            
        print(f"✅ Mesaj başarıyla gönderildi!")
        
    except Exception as e:
        print(f"❌ Kullanıcı {user_id} için mesaj gönderilemedi: {e}")
        print(f"🔍 Hata detayı: {type(e).__name__}")
        
        # Markdown hatası varsa düz metin olarak gönder
        try:
            print(f"🔄 Markdown olmadan tekrar deneniyor...")
            bot.send_message(user_id, message)
            print(f"✅ Düz metin olarak gönderildi!")
        except Exception as e2:
            print(f"❌ Düz metin de gönderilemedi: {e2}")

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
            "/health": "Sağlık kontrolü",
            "/admin": "Admin panel"
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

@app.route('/admin')
def admin_panel():
    """Admin panel HTML"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Botanlik Bot Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .header { text-align: center; margin-bottom: 30px; }
            .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .license-form { display: flex; gap: 10px; margin: 10px 0; }
            .license-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .license-list { max-height: 400px; overflow-y: auto; }
            .license-item { padding: 10px; margin: 5px 0; border: 1px solid #eee; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Botanlik Bot Admin Panel</h1>
                <p>Bot durumu ve lisans yönetimi</p>
            </div>
            
            <div class="section">
                <h2>📊 Bot Durumu</h2>
                <div id="bot-status">Yükleniyor...</div>
                <button class="btn btn-primary" onclick="refreshStatus()">🔄 Yenile</button>
            </div>
            
            <div class="section">
                <h2>🔑 Lisans Yönetimi</h2>
                <div class="license-form">
                    <input type="text" id="license-key" class="license-input" placeholder="Lisans anahtarı">
                    <select id="license-type" class="license-input">
                        <option value="monthly">1 Aylık ($100)</option>
                        <option value="quarterly">3 Aylık ($200)</option>
                        <option value="unlimited">Sınırsız ($500)</option>
                    </select>
                    <button class="btn btn-success" onclick="addLicense()">➕ Lisans Ekle</button>
                </div>
                <div class="license-list" id="license-list">Yükleniyor...</div>
            </div>
            
            <div class="section">
                <h2>👥 Kullanıcı Yönetimi</h2>
                <div id="user-list">Yükleniyor...</div>
            </div>
        </div>
        
        <script>
            function refreshStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('bot-status').innerHTML = `
                            <p><strong>Durum:</strong> ${data.running ? '✅ Çalışıyor' : '❌ Durdu'}</p>
                            <p><strong>Son Çalışma:</strong> ${data.last_run || 'Henüz çalışmadı'}</p>
                            <p><strong>Mesaj:</strong> ${data.message}</p>
                        `;
                    });
            }
            
            function addLicense() {
                const key = document.getElementById('license-key').value;
                const type = document.getElementById('license-type').value;
                
                if (!key) {
                    alert('Lisans anahtarı gerekli!');
                    return;
                }
                
                fetch('/admin/add-license', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key, type})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Lisans eklendi!');
                        loadLicenses();
                    } else {
                        alert('Hata: ' + data.message);
                    }
                });
            }
            
            function loadLicenses() {
                fetch('/admin/licenses')
                    .then(response => response.json())
                    .then(data => {
                        const list = document.getElementById('license-list');
                        list.innerHTML = data.licenses.map(license => `
                            <div class="license-item">
                                <strong>${license.key}</strong> - ${license.type} ($${license.price})
                                <button class="btn btn-danger" onclick="deleteLicense('${license.key}')">🗑️ Sil</button>
                            </div>
                        `).join('');
                    });
            }
            
            function deleteLicense(key) {
                if (confirm('Bu lisansı silmek istediğinizden emin misiniz?')) {
                    fetch('/admin/delete-license', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({key})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Lisans silindi!');
                            loadLicenses();
                        } else {
                            alert('Hata: ' + data.message);
                        }
                    });
                }
            }
            
            // Sayfa yüklendiğinde
            refreshStatus();
            loadLicenses();
        </script>
    </body>
    </html>
    """
    return html

@app.route('/admin/licenses')
def get_licenses():
    """Lisansları listele"""
    try:
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        license_list = []
        for key, info in licenses.items():
            license_list.append({
                'key': key,
                'type': info.get('type', 'unknown'),
                'price': info.get('price', 0)
            })
        
        return jsonify({'licenses': license_list})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/admin/add-license', methods=['POST'])
def add_license():
    """Lisans ekle"""
    try:
        data = request.json
        key = data.get('key')
        license_type = data.get('type')
        
        if not key or not license_type:
            return jsonify({'success': False, 'message': 'Eksik parametreler'})
        
        # Lisans bilgilerini oluştur
        license_info = {
            'type': license_type,
            'duration': 30 if license_type == 'monthly' else (90 if license_type == 'quarterly' else -1),
            'price': 100 if license_type == 'monthly' else (200 if license_type == 'quarterly' else 500),
            'features': [
                'Temel Tarama',
                'Telegram Bildirimleri',
                'Formasyon Analizi'
            ]
        }
        
        if license_type == 'quarterly':
            license_info['features'].append('Öncelikli Destek')
        elif license_type == 'unlimited':
            license_info['features'].extend(['Öncelikli Destek', 'Özel Formasyonlar', '7/24 Destek'])
        
        # Lisansı kaydet
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        licenses[key] = license_info
        
        with open('licenses.json', 'w') as f:
            json.dump(licenses, f, indent=2)
        
        # Log'u azalt - sadece başarılı olduğunda kısa mesaj
        print(f"✅ Lisans eklendi: {key}")
        
        return jsonify({'success': True, 'message': 'Lisans eklendi'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete-license', methods=['POST'])
def delete_license():
    """Lisans sil"""
    try:
        data = request.json
        key = data.get('key')
        
        if not key:
            return jsonify({'success': False, 'message': 'Lisans anahtarı gerekli'})
        
        # Lisansı sil
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        if key in licenses:
            del licenses[key]
            
            with open('licenses.json', 'w') as f:
                json.dump(licenses, f, indent=2)
            
            return jsonify({'success': True, 'message': 'Lisans silindi'})
        else:
            return jsonify({'success': False, 'message': 'Lisans bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def run_flask():
    """Flask uygulamasını çalıştır"""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram_bot():
    """Telegram botunu çalıştır"""
    print("🚀 Telegram Bot başlatılıyor...")
    print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
    
    try:
        print("📱 Bot polling başlatılıyor...")
        # Daha basit polling ayarları
        bot.polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"❌ Bot hatası: {e}")
        import traceback
        print(f"🔍 Detaylı hata: {traceback.format_exc()}")
        
        # Hata durumunda tekrar dene
        import time
        time.sleep(3)
        try:
            print("🔄 Bot polling tekrar deneniyor...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e2:
            print(f"❌ İkinci deneme de başarısız: {e2}")
            print(f"🔍 İkinci hata detayı: {traceback.format_exc()}")

def main():
    """Ana fonksiyon - hem Flask hem Telegram botu çalıştır"""
    print("🚀 Botanlik Bot başlatılıyor...")
    print("📱 Telegram Bot + 🌐 Admin Panel aktif")
    
    # Flask'i ayrı thread'de başlat
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Telegram botunu ana thread'de çalıştır
    run_telegram_bot()

if __name__ == "__main__":
    main() 