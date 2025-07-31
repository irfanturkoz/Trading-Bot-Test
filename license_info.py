#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from license_manager import LicenseManager
from datetime import datetime

def show_license_info():
    """Lisans bilgilerini gösterir"""
    license_manager = LicenseManager()
    
    print("\n" + "="*60)
    print("🎯 TRADING BOT - LİSANS BİLGİLERİ")
    print("="*60)
    
    # Lisans durumunu kontrol et
    license_status, license_result = license_manager.check_license_status()
    
    if license_status:
        license_info = license_result
        print("✅ LİSANS AKTİF")
        print(f"🔑 Anahtar: {license_info['key']}")
        print(f"📦 Paket: {license_info['type'].upper()}")
        print(f"💰 Fiyat: ${license_info['price']}")
        print(f"📅 Aktifleştirme: {license_info['activated_date'][:10]}")
        
        if license_info['expiry_date']:
            expiry_date = datetime.fromisoformat(license_info['expiry_date'])
            remaining_days = (expiry_date - datetime.now()).days
            print(f"⏰ Bitiş: {license_info['expiry_date'][:10]}")
            print(f"📊 Kalan süre: {max(0, remaining_days)} gün")
        else:
            print("⏰ Bitiş: Sınırsız")
            print("📊 Kalan süre: Sınırsız")
        
        print("\n✅ ÖZELLİKLER:")
        for feature in license_info['features']:
            print(f"   • {feature}")
            
    else:
        print("❌ LİSANS BULUNAMADI VEYA SÜRESİ DOLMUŞ")
        print(f"💬 İletişim: {license_manager.contact_telegram}")
        
        # Fiyatlandırma bilgilerini göster
        license_manager.show_pricing_info()
    
    print("="*60)

if __name__ == "__main__":
    show_license_info() 