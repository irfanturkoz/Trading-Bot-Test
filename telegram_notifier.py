# telegram_notifier.py
import os
import requests
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Bot token'ını environment variable'dan al
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN environment variable bulunamadı!")
    print("💡 .env dosyası oluşturun ve TELEGRAM_BOT_TOKEN ekleyin")
    raise ValueError("Bot token bulunamadı!")

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
    
    try:
        if image_path and os.path.exists(image_path):
            # Fotoğraflı mesaj gönder
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': message,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(url, data=data, files=files)
                print(f"✅ Fotoğraflı mesaj gönderildi: {image_path}")
                return response.json()
        else:
            # Sadece metin mesajı gönder
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data)
            print(f"✅ Metin mesajı gönderildi")
            return response.json()
            
    except Exception as e:
        print(f"❌ Telegram mesajı gönderilemedi: {e}")
        return None 