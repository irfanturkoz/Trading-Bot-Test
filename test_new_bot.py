import os
import requests

print("🔍 Yeni Bot Test")
print("=" * 30)

# Yeni bot token'ı (geçici)
NEW_BOT_TOKEN = "8243806452:AAErJkMJ9yDEL3IDGFN_ayQHnXQhHkiA-YE"

print(f"📝 Token: {NEW_BOT_TOKEN[:20]}...")

# Telegram API'ye test isteği gönder
url = f"https://api.telegram.org/bot{NEW_BOT_TOKEN}/getMe"

try:
    response = requests.get(url)
    print(f"📡 Status: {response.status_code}")
    print(f"📝 Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Token geçerli!")
    else:
        print("❌ Token geçersiz!")
        
except Exception as e:
    print(f"❌ Hata: {e}")

print("✅ Test tamamlandı!") 