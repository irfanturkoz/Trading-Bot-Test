import os
import requests
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Yeni bot token'ını test et
BOT_TOKEN = "8243806452:AAErJkMJ9yDEL3IDGFN_ayQHnXQhHkiA-YE"

print(f"🔍 Yeni Token kontrol ediliyor...")
print(f"📝 Token: {BOT_TOKEN[:20]}...")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
    exit(1)

# Telegram API'ye test isteği gönder
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

try:
    response = requests.get(url)
    print(f"📡 API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print(f"✅ Bot Token Geçerli!")
            print(f"🤖 Bot Username: @{bot_info.get('username', 'Unknown')}")
            print(f"📝 Bot Name: {bot_info.get('first_name', 'Unknown')}")
            print(f"🆔 Bot ID: {bot_info.get('id', 'Unknown')}")
        else:
            print(f"❌ Bot Token Geçersiz!")
            print(f"🔍 Error: {data}")
    else:
        print(f"❌ API Hatası: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
except Exception as e:
    print(f"❌ Test hatası: {e}")

print("\n🔧 Doğru token formatı:")
print("TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz") 