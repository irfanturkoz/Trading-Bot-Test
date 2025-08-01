#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from license_manager import LicenseManager

def test_license_validation():
    """Lisans doğrulama testi"""
    print("🧪 Lisans Doğrulama Testi")
    print("=" * 50)
    
    # LicenseManager'ı başlat
    lm = LicenseManager()
    
    # Mevcut lisansları listele
    print(f"📋 Toplam lisans sayısı: {len(lm.valid_licenses)}")
    print(f"🔑 Lisans anahtarları: {list(lm.valid_licenses.keys())}")
    
    # Test lisansları
    test_licenses = [
        "MONTHLY_2024_001",
        "QUARTERLY_2024_001", 
        "UNLIMITED_2024_001",
        "UNLIMITED_20250731_190345_ECJOW",
        "MONTHLY_20250731_200418_9CQH08",
        "Admin2933818234A",
        "INVALID_LICENSE"
    ]
    
    for license_key in test_licenses:
        print(f"\n🔍 Test edilen lisans: {license_key}")
        try:
            is_valid, result = lm.validate_license(license_key)
            if is_valid:
                print(f"✅ Geçerli: {result.get('type', 'unknown')} - ${result.get('price', 0)}")
            else:
                print(f"❌ Geçersiz: {result}")
        except Exception as e:
            print(f"❌ Hata: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test tamamlandı!")

if __name__ == "__main__":
    test_license_validation() 