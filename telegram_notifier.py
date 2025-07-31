# telegram_notifier.py
import requests
from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID

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