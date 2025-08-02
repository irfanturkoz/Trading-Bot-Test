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

def send_telegram_message(message, chat_id=None):
    """
    Telegram üzerinden mesaj gönderir.
    """
    if chat_id is None:
        chat_id = ADMIN_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")
        return None 