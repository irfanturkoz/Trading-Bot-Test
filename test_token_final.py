import requests

print("🔍 Final Token Test")
print("=" * 30)

# Yeni token'ı test et
TOKEN = "8243806452:AAErJkMJ9yDEL3IDGFN_ayQHnXQhHkiA-YE"

print(f"📝 Token: {TOKEN[:20]}...")

# Telegram API'ye test isteği gönder
url = f"https://api.telegram.org/bot{TOKEN}/getMe"

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

print("✅ Test tamamlandı!") 