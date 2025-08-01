import json
import random
import string
import hashlib
import time

def generate_hash_like_key():
    """BTC cüzdan adresine benzer hash-like lisans anahtarı oluştur"""
    # Rastgele veri oluştur
    random_data = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    timestamp = str(int(time.time()))
    
    # Hash oluştur
    combined = random_data + timestamp
    hash_object = hashlib.sha256(combined.encode())
    hash_hex = hash_object.hexdigest()
    
    # İlk 16 karakteri al ve büyük harfe çevir
    key = hash_hex[:16].upper()
    
    # Her 4 karakterde bir tire ekle (BTC adresine benzer format)
    formatted_key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])
    
    return formatted_key

def create_licenses():
    """300 lisans oluştur (hash-like format)"""
    licenses = {}
    
    # 100 Unlimited lisans
    for i in range(100):
        key = generate_hash_like_key()
        licenses[key] = {
            "type": "unlimited",
            "duration": -1,
            "price": 500,
            "features": [
                "Temel Tarama",
                "Telegram Bildirimleri",
                "Formasyon Analizi",
                "Öncelikli Destek",
                "Özel Formasyonlar",
                "7/24 Destek"
            ]
        }
    
    # 100 Monthly lisans
    for i in range(100):
        key = generate_hash_like_key()
        licenses[key] = {
            "type": "monthly",
            "duration": 30,
            "price": 100,
            "features": [
                "Temel Tarama",
                "Telegram Bildirimleri",
                "Formasyon Analizi"
            ]
        }
    
    # 100 Quarterly lisans
    for i in range(100):
        key = generate_hash_like_key()
        licenses[key] = {
            "type": "quarterly",
            "duration": 90,
            "price": 200,
            "features": [
                "Temel Tarama",
                "Telegram Bildirimleri",
                "Formasyon Analizi",
                "Öncelikli Destek"
            ]
        }
    
    return licenses

# Mevcut licenses.json dosyasını oku
with open('licenses.json', 'r', encoding='utf-8') as f:
    existing_licenses = json.load(f)

# Yeni lisansları ekle
new_licenses = create_licenses()
existing_licenses.update(new_licenses)

# Dosyayı güncelle
with open('licenses.json', 'w', encoding='utf-8') as f:
    json.dump(existing_licenses, f, indent=2, ensure_ascii=False)

print(f"✅ {len(new_licenses)} yeni hash-like lisans eklendi!")
print(f"📊 Toplam lisans sayısı: {len(existing_licenses)}")

# Örnek lisansları göster
print("\n📋 Örnek Hash-Like Lisanslar:")
unlimited_keys = [k for k, v in new_licenses.items() if v['type'] == 'unlimited'][:3]
monthly_keys = [k for k, v in new_licenses.items() if v['type'] == 'monthly'][:3]
quarterly_keys = [k for k, v in new_licenses.items() if v['type'] == 'quarterly'][:3]

print(f"Unlimited: {unlimited_keys[0]}, {unlimited_keys[1]}, {unlimited_keys[2]}")
print(f"Monthly: {monthly_keys[0]}, {monthly_keys[1]}, {monthly_keys[2]}")
print(f"Quarterly: {quarterly_keys[0]}, {quarterly_keys[1]}, {quarterly_keys[2]}") 