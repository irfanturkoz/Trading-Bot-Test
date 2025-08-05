# telegram_notifier.py
import os
import requests
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Bot token'ını environment variable'dan al
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Environment variable varsa kontrol et, yoksa veya yanlışsa hardcoded kullan
if not TELEGRAM_BOT_TOKEN or "AAGSkI5VI" in TELEGRAM_BOT_TOKEN:
    # Hardcoded token kullan (start.py ile aynı)
    TELEGRAM_BOT_TOKEN = "8259350638:AAEvnwmHddZ2raKa8bXYYxRG4U3kD0tdjZY"
    print("⚠️ Environment variable bulunamadı veya yanlış, hardcoded token kullanılıyor")
else:
    print("✅ Bot token environment variable'dan yüklendi")

print(f"🔍 Kullanılan Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")

print("✅ Notifier: Bot token environment variable'dan yüklendi")

ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

# ADMIN_CHAT_ID kontrolü
if not ADMIN_CHAT_ID:
    print("⚠️ ADMIN_CHAT_ID environment variable bulunamadı!")
    print("💡 .env dosyasına ADMIN_CHAT_ID ekleyin")
    ADMIN_CHAT_ID = "123456789"  # Varsayılan değer
    print(f"🔧 Varsayılan ADMIN_CHAT_ID kullanılıyor: {ADMIN_CHAT_ID}")
else:
    print(f"✅ ADMIN_CHAT_ID yüklendi: {ADMIN_CHAT_ID}")

def send_telegram_message(message, image_path=None, chat_id=None):
    """
    Telegram üzerinden mesaj gönderir.
    
    Args:
        message (str): Gönderilecek mesaj
        image_path (str, optional): Fotoğraf dosya yolu
        chat_id (str, optional): Chat ID (None ise ADMIN_CHAT_ID kullanılır)
    """
    if chat_id is None:
        chat_id = ADMIN_CHAT_ID
    
    print(f"🔍 Telegram gönderimi başlatılıyor...")
    print(f"📝 Mesaj uzunluğu: {len(message)} karakter")
    print(f"📁 Image path: {image_path}")
    print(f"📁 Dosya var mı: {os.path.exists(image_path) if image_path else 'None'}")
    print(f"💬 Chat ID: {chat_id}")
    print(f"🤖 Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    try:
        if image_path and os.path.exists(image_path):
            # Fotoğraflı mesaj gönder
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            print(f"📤 Fotoğraflı mesaj gönderiliyor: {url}")
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': message,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(url, data=data, files=files)
                
                print(f"📡 Response status: {response.status_code}")
                print(f"📡 Response: {response.text}")
                
                if response.status_code == 200:
                    print(f"✅ Fotoğraflı mesaj gönderildi: {image_path}")
                    return response.json()
                else:
                    print(f"❌ Fotoğraflı mesaj gönderilemedi: {response.status_code}")
                    return None
        else:
            # Sadece metin mesajı gönder
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            print(f"📤 Metin mesajı gönderiliyor: {url}")
            
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data)
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ Metin mesajı gönderildi")
                return response.json()
            else:
                print(f"❌ Metin mesajı gönderilemedi: {response.status_code}")
                return None
            
    except Exception as e:
        print(f"❌ Telegram mesajı gönderilemedi: {e}")
        import traceback
        print(f"🔍 Detaylı hata: {traceback.format_exc()}")
        return None 