# telegram_notifier.py
import os
import requests

# YENİ GÜVENLİ TOKEN - Doğrudan ayarla
TELEGRAM_BOT_TOKEN = "8243806452:AAFH_i_CcyU0p_9lF9_9yg73OAL59tn6ab8"
os.environ['TELEGRAM_BOT_TOKEN'] = TELEGRAM_BOT_TOKEN
print("Notifier: Güvenli token yüklendi!")

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