import requests

# Yeni bot token'ını test et
BOT_TOKEN = "8259350638:AAEvnwmHddZ2raKa8bXYYxRG4U3kD0tdjZY"

def test_bot_token():
    """Bot token'ını test et"""
    print("🔍 Yeni Bot Token Testi")
    print(f"📝 Token: {BOT_TOKEN[:20]}...")
    
    # Bot bilgilerini al
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        print(f"📡 Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Token geçerli!")
                print(f"🤖 Bot: @{bot_info['username']}")
                print(f"📝 Name: {bot_info['first_name']}")
                return True
            else:
                print(f"❌ Token geçersiz: {data.get('description', 'Bilinmeyen hata')}")
                return False
        else:
            print(f"❌ HTTP Hatası: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return False

if __name__ == "__main__":
    test_bot_token() 