#!/usr/bin/env python3
"""
Test script for telegram_notifier.py
"""

import os
import time

print("🔍 Telegram Notifier Test Başlatılıyor...")

try:
    from telegram_notifier import send_telegram_message
    print("✅ telegram_notifier import başarılı")
except Exception as e:
    print(f"❌ telegram_notifier import hatası: {e}")
    exit(1)

# Test mesajı
test_message = """
🚨 **TEST SİNYALİ** 🚨

📊 **Sembol:** BTCUSDT
🔍 **Formasyon:** Test Formasyonu
💰 **Giriş Fiyatı:** 45000 USDT
🎯 **Hedef Seviyeler:**
• TP1: 47250 USDT (+5%)
• TP2: 49500 USDT (+10%)
• TP3: 51750 USDT (+15%)
• SL: 42750 USDT (-5%)

📈 **Risk/Ödül Oranı:** 1.50:1
🎯 **Kalite Skoru:** 85/100

⏰ **Sinyal Zamanı:** Test
⚠️ **Risk Uyarısı:** Bu bir test sinyalidir.
"""

print("📝 Test mesajı hazırlandı")
print(f"📊 Mesaj uzunluğu: {len(test_message)} karakter")

# Test 1: Sadece metin mesajı
print("\n🧪 TEST 1: Sadece metin mesajı")
try:
    result = send_telegram_message(test_message)
    if result:
        print("✅ Test 1 başarılı!")
    else:
        print("❌ Test 1 başarısız!")
except Exception as e:
    print(f"❌ Test 1 hatası: {e}")

# Test 2: Fotoğraflı mesaj (eğer test.png varsa)
print("\n🧪 TEST 2: Fotoğraflı mesaj")
test_image = "test.png"
if os.path.exists(test_image):
    try:
        result = send_telegram_message(test_message, test_image)
        if result:
            print("✅ Test 2 başarılı!")
        else:
            print("❌ Test 2 başarısız!")
    except Exception as e:
        print(f"❌ Test 2 hatası: {e}")
else:
    print(f"⚠️ Test resmi bulunamadı: {test_image}")

print("\n�� Test tamamlandı!") 