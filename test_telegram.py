import requests
import json

def test_telegram_bot():
    """Telegram bot'unu test eder"""
    
    bot_token = "8243806452:AAHzrY3CYZFhX64FKd9wFCY-JwBUnoV8KQA"
    
    print("🤖 Telegram Bot Test")
    print("=" * 40)
    
    # 1. Bot bilgilerini kontrol et
    print("1. Bot bilgileri kontrol ediliyor...")
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url)
    
    if response.status_code == 200:
        bot_info = response.json()
        if bot_info.get('ok'):
            print(f"✅ Bot aktif: {bot_info['result']['first_name']}")
            print(f"📱 Username: @{bot_info['result']['username']}")
        else:
            print(f"❌ Bot hatası: {bot_info}")
            return
    else:
        print(f"❌ Bağlantı hatası: {response.status_code}")
        return
    
    # 2. Mesajları kontrol et
    print("\n2. Mesajlar kontrol ediliyor...")
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    
    if response.status_code == 200:
        updates = response.json()
        if updates.get('ok'):
            if updates['result']:
                print(f"✅ {len(updates['result'])} mesaj bulundu")
                for update in updates['result']:
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', 'No text')
                        print(f"   📱 Chat ID: {chat_id}")
                        print(f"   💬 Mesaj: {text}")
                        print(f"   👤 Kullanıcı: {message['from'].get('first_name', 'Unknown')}")
                        print()
            else:
                print("📭 Henüz mesaj yok")
                print("💡 Telegram'da bot'a /start gönderin")
        else:
            print(f"❌ Mesaj hatası: {updates}")
    else:
        print(f"❌ Bağlantı hatası: {response.status_code}")
    
    # 3. Test mesajı gönder
    print("\n3. Test mesajı gönderiliyor...")
    chat_id = input("Chat ID'nizi girin (mesajlardan bulduysanız): ").strip()
    
    if chat_id and chat_id.isdigit():
        test_message = "🤖 Bot test mesajı! Bot çalışıyor!"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': test_message
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Test mesajı gönderildi!")
                print("📱 Telegram'da mesajı kontrol edin")
            else:
                print(f"❌ Mesaj gönderilemedi: {result}")
        else:
            print(f"❌ Bağlantı hatası: {response.status_code}")
    else:
        print("⚠️ Chat ID girilmedi, test mesajı gönderilmedi")

if __name__ == "__main__":
    test_telegram_bot() 