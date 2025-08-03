#!/usr/bin/env python3
"""
Bot Restart Script - Conflict çözümü için
"""

import os
import time
import requests
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

def clear_webhook():
    """Telegram webhook'unu temizle"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return False
    
    try:
        # Webhook'u temizle
        url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook başarıyla temizlendi")
                return True
            else:
                print(f"⚠️ Webhook temizleme hatası: {result}")
                return False
        else:
            print(f"❌ Webhook temizleme hatası: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook temizleme hatası: {e}")
        return False

def test_bot_connection():
    """Bot bağlantısını test et"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result['result']
                print(f"✅ Bot bağlantısı başarılı: @{bot_info['username']}")
                print(f"✅ Bot ID: {bot_info['id']}")
                print(f"✅ Bot adı: {bot_info['first_name']}")
                return True
            else:
                print(f"❌ Bot bağlantı hatası: {result}")
                return False
        else:
            print(f"❌ Bot bağlantı hatası: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Bot bağlantı hatası: {e}")
        return False

def main():
    """Ana fonksiyon"""
    print("🔄 Bot Restart Script Başlatılıyor...")
    print("=" * 50)
    
    # Environment variables kontrolü
    print("🔍 Environment variables kontrol ediliyor...")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_id = os.getenv('ADMIN_CHAT_ID')
    
    if token:
        print(f"✅ TELEGRAM_BOT_TOKEN: {token[:20]}...")
    else:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return
    
    if admin_id:
        print(f"✅ ADMIN_CHAT_ID: {admin_id}")
    else:
        print("⚠️ ADMIN_CHAT_ID bulunamadı!")
    
    print("=" * 50)
    
    # Webhook'u temizle
    print("🧹 Webhook temizleniyor...")
    if clear_webhook():
        print("⏳ 10 saniye bekleniyor...")
        time.sleep(10)
    else:
        print("⚠️ Webhook temizlenemedi, devam ediliyor...")
    
    # Bot bağlantısını test et
    print("🔗 Bot bağlantısı test ediliyor...")
    if test_bot_connection():
        print("✅ Bot hazır!")
    else:
        print("❌ Bot bağlantısı başarısız!")
        return
    
    print("=" * 50)
    print("🚀 Bot restart tamamlandı!")
    print("💡 Şimdi ana uygulamayı başlatabilirsiniz.")

if __name__ == "__main__":
    main() 