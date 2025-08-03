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

def get_webhook_info():
    """Mevcut webhook bilgilerini al"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return None
    
    try:
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook_info = result['result']
                print("🔍 Webhook Bilgileri:")
                print(f"   URL: {webhook_info.get('url', 'Yok')}")
                print(f"   Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
                print(f"   Pending update count: {webhook_info.get('pending_update_count', 0)}")
                print(f"   Last error date: {webhook_info.get('last_error_date', 'Yok')}")
                print(f"   Last error message: {webhook_info.get('last_error_message', 'Yok')}")
                return webhook_info
            else:
                print(f"❌ Webhook bilgisi alınamadı: {result}")
                return None
        else:
            print(f"❌ Webhook bilgisi hatası: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Webhook bilgisi hatası: {e}")
        return None

def check_railway_url():
    """Railway URL'ini kontrol et"""
    try:
        # Railway environment variables'ından URL'leri al
        public_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
        static_url = os.getenv('RAILWAY_STATIC_URL')
        
        if public_domain:
            print(f"🌐 Railway Public Domain: https://{public_domain}")
            print(f"   Admin Panel: https://{public_domain}/admin")
        
        if static_url:
            print(f"🌐 Railway Static URL: https://{static_url}")
            print(f"   Admin Panel: https://{static_url}/admin")
        
        # PORT environment variable'ını kontrol et
        port = os.getenv('PORT', '8080')
        print(f"🔌 Port: {port}")
        
        return public_domain or static_url
        
    except Exception as e:
        print(f"❌ Railway URL kontrolü hatası: {e}")
        return None

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
    
    # Railway URL'lerini kontrol et
    print("🌐 Railway URL'leri kontrol ediliyor...")
    railway_url = check_railway_url()
    
    print("=" * 50)
    
    # Mevcut webhook bilgilerini al
    print("🔍 Mevcut webhook bilgileri alınıyor...")
    webhook_info = get_webhook_info()
    
    print("=" * 50)
    
    # Webhook'u temizle
    print("🧹 Webhook temizleniyor...")
    if clear_webhook():
        print("⏳ 15 saniye bekleniyor...")
        time.sleep(15)
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
    
    if railway_url:
        print(f"🌐 Admin Panel: https://{railway_url}/admin")
        print("🔐 Şifre: admin123")

if __name__ == "__main__":
    main() 