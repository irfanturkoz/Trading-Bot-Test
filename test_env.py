#!/usr/bin/env python3
"""
Railway Environment Variables Test Script
Bu script Railway'de environment variable'ların doğru yüklenip yüklenmediğini test eder.
"""

import os
from dotenv import load_dotenv

def test_environment_variables():
    print("🔍 Environment Variables Test Başlıyor...")
    print("=" * 50)
    
    # .env dosyasını yükle (eğer varsa)
    load_dotenv()
    
    # Tüm environment variables'ları listele
    print("📋 Tüm Environment Variables:")
    for key, value in os.environ.items():
        if 'TELEGRAM' in key or 'ADMIN' in key or 'BOT' in key:
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: [gizli]")
    
    print("\n" + "=" * 50)
    
    # Özel testler
    bot_key = os.getenv('TELEGRAM_BOT_KEY')
    admin_id = os.getenv('ADMIN_CHAT_ID')
    
    print(f"🔍 TELEGRAM_BOT_KEY: {bot_key}")
    print(f"🔍 ADMIN_CHAT_ID: {admin_id}")
    
    if bot_key:
        print("✅ TELEGRAM_BOT_KEY bulundu!")
        print(f"   Token uzunluğu: {len(bot_key)}")
        print(f"   Token başlangıcı: {bot_key[:20]}...")
    else:
        print("❌ TELEGRAM_BOT_KEY bulunamadı!")
    
    if admin_id:
        print("✅ ADMIN_CHAT_ID bulundu!")
        print(f"   Admin ID: {admin_id}")
    else:
        print("❌ ADMIN_CHAT_ID bulunamadı!")
    
    print("\n" + "=" * 50)
    print("🏁 Test tamamlandı!")

if __name__ == "__main__":
    test_environment_variables() 