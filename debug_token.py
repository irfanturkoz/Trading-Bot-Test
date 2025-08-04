import os
import requests

print("🔍 Railway Token Debug")
print("=" * 40)

# Environment variable'ı kontrol et
token = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"📝 TELEGRAM_BOT_TOKEN: {token[:20] if token else 'None'}...")

if not token:
    print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
    print("🔧 Railway'de environment variable'ı kontrol edin:")
    print("   - TELEGRAM_BOT_TOKEN=8243806452:AAErJkMJ9yDEL3IDGFN_ayQHnXQhHkiA-YE")
    exit(1)

# Telegram API'ye test isteği gönder
url = f"https://api.telegram.org/bot{token}/getMe"

try:
    response = requests.get(url)
    print(f"📡 Status: {response.status_code}")
    print(f"📝 Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Token geçerli!")
        data = response.json()
        print(f"🤖 Bot: @{data['result']['username']}")
        print(f"📝 Name: {data['result']['first_name']}")
    else:
        print("❌ Token geçersiz!")
        
except Exception as e:
    print(f"❌ Hata: {e}")

print("\n🔧 Doğru token formatı:")
print("TELEGRAM_BOT_TOKEN=8243806452:AAErJkMJ9yDEL3IDGFN_ayQHnXQhHkiA-YE") 