import os
import requests

print("🔍 Railway Token Test")
print("=" * 30)

# Environment variable'dan token'ı al
token = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"📝 Token: {token[:20] if token else 'None'}...")

if not token:
    print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
    exit(1)

# Telegram API'ye test isteği gönder
url = f"https://api.telegram.org/bot{token}/getMe"

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