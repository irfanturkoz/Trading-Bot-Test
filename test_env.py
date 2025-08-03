#!/usr/bin/env python3
"""
Railway Environment Variables Test Script
Bu script Railway'de environment variables'ların doğru yüklenip yüklenmediğini test eder.
"""

import os
import sys
from dotenv import load_dotenv

def test_environment_variables():
    """Environment variables'ları test et"""
    print("🔍 Railway Environment Variables Test")
    print("=" * 50)
    
    # .env dosyasını yükle (eğer varsa)
    print("📁 .env dosyası yükleniyor...")
    load_dotenv()
    print("✅ .env dosyası yüklendi (eğer varsa)")
    
    # Tüm environment variables'ları listele
    print("\n🔍 Tüm Environment Variables:")
    print("-" * 30)
    
    all_env_vars = dict(os.environ)
    telegram_vars = []
    railway_vars = []
    other_vars = []
    
    for key, value in all_env_vars.items():
        if 'TELEGRAM' in key or 'BOT' in key:
            telegram_vars.append((key, value))
        elif 'RAILWAY' in key:
            railway_vars.append((key, value))
        else:
            other_vars.append((key, value))
    
    print("📱 TELEGRAM/BOT Variables:")
    for key, value in telegram_vars:
        print(f"  {key}: {value}")
    
    print("\n🚂 RAILWAY Variables:")
    for key, value in railway_vars[:10]:  # İlk 10 tanesini göster
        print(f"  {key}: {value}")
    
    print(f"\n📊 Diğer Variables (toplam {len(other_vars)}):")
    for key, value in other_vars[:5]:  # İlk 5 tanesini göster
        print(f"  {key}: {value}")
    
    # Özel testler
    print("\n🧪 Özel Testler:")
    print("-" * 20)
    
    # TELEGRAM_BOT_TOKEN test
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if bot_token:
        print(f"✅ TELEGRAM_BOT_TOKEN bulundu: {bot_token[:20]}...")
        print(f"   Uzunluk: {len(bot_token)}")
        print(f"   Son 10 karakter: ...{bot_token[-10:]}")
    else:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
    
    # TELEGRAM_BOT_KEY test (eski isim)
    bot_key = os.getenv('TELEGRAM_BOT_KEY')
    if bot_key:
        print(f"⚠️ TELEGRAM_BOT_KEY bulundu (eski isim): {bot_key[:20]}...")
    else:
        print("✅ TELEGRAM_BOT_KEY yok (normal)")
    
    # ADMIN_CHAT_ID test
    admin_id = os.getenv('ADMIN_CHAT_ID')
    if admin_id:
        print(f"✅ ADMIN_CHAT_ID bulundu: {admin_id}")
    else:
        print("❌ ADMIN_CHAT_ID bulunamadı!")
    
    print("\n" + "=" * 50)
    print("🏁 Test tamamlandı!")
    
    return bot_token is not None

if __name__ == "__main__":
    success = test_environment_variables()
    sys.exit(0 if success else 1) 