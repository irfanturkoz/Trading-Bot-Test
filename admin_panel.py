#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime, timedelta
from license_manager import LicenseManager

class AdminPanel:
    def __init__(self):
        self.license_manager = LicenseManager()
        self.admin_password = "admin123"  # Gerçek uygulamada güvenli şekilde saklanmalı
    
    def generate_license_key(self, license_type, price):
        """Yeni lisans anahtarı oluşturur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if license_type == "monthly":
            prefix = "MONTHLY"
            duration = 30
        elif license_type == "quarterly":
            prefix = "QUARTERLY"
            duration = 90
        elif license_type == "unlimited":
            prefix = "UNLIMITED"
            duration = -1
        else:
            return None, "Geçersiz lisans tipi!"
        
        # Benzersiz anahtar oluştur
        import random
        import string
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        license_key = f"{prefix}_{timestamp}_{random_suffix}"
        
        # Lisans bilgilerini oluştur
        license_info = {
            "type": license_type,
            "duration": duration,
            "price": price,
            "features": self.get_features_by_type(license_type)
        }
        
        # Mevcut lisanslara ekle
        self.license_manager.valid_licenses[license_key] = license_info
        
        return license_key, license_info
    
    def get_features_by_type(self, license_type):
        """Lisans tipine göre özellikleri döndürür"""
        if license_type == "monthly":
            return ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi"]
        elif license_type == "quarterly":
            return ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek"]
        elif license_type == "unlimited":
            return ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek", "Özel Formasyonlar", "7/24 Destek"]
        return []
    
    def show_all_licenses(self):
        """Tüm lisansları gösterir"""
        print("\n" + "="*80)
        print("🔑 MEVCUT LİSANS ANAHTARLARI")
        print("="*80)
        
        for key, info in self.license_manager.valid_licenses.items():
            print(f"\n🔑 Anahtar: {key}")
            print(f"📦 Tip: {info['type'].upper()}")
            print(f"💰 Fiyat: ${info['price']}")
            print(f"⏰ Süre: {info['duration']} gün" if info['duration'] != -1 else "⏰ Süre: Sınırsız")
            print("✅ Özellikler:")
            for feature in info['features']:
                print(f"   • {feature}")
            print("-" * 50)
    
    def add_new_license(self):
        """Yeni lisans ekler"""
        print("\n" + "="*50)
        print("➕ YENİ LİSANS EKLE")
        print("="*50)
        
        print("📦 Lisans Tipleri:")
        print("1. Monthly (1 Aylık) - $200")
        print("2. Quarterly (3 Aylık) - $500")
        print("3. Unlimited (Sınırsız) - $1500")
        
        choice = input("\nSeçiminiz (1-3): ").strip()
        
        if choice == "1":
            license_type = "monthly"
            price = 200
        elif choice == "2":
            license_type = "quarterly"
            price = 500
        elif choice == "3":
            license_type = "unlimited"
            price = 1500
        else:
            print("❌ Geçersiz seçim!")
            return
        
        # Lisans anahtarı oluştur
        license_key, license_info = self.generate_license_key(license_type, price)
        
        if license_key:
            print(f"\n✅ Yeni lisans oluşturuldu!")
            print(f"🔑 Anahtar: {license_key}")
            print(f"📦 Tip: {license_info['type'].upper()}")
            print(f"💰 Fiyat: ${license_info['price']}")
            print(f"⏰ Süre: {license_info['duration']} gün" if license_info['duration'] != -1 else "⏰ Süre: Sınırsız")
            
            # Lisansları dosyaya kaydet
            self.save_licenses_to_file()
        else:
            print(f"❌ Hata: {license_info}")
    
    def save_licenses_to_file(self):
        """Lisansları dosyaya kaydeder"""
        try:
            with open("licenses.json", "w") as f:
                json.dump(self.license_manager.valid_licenses, f, indent=2)
            print("💾 Lisanslar kaydedildi.")
        except Exception as e:
            print(f"❌ Lisanslar kaydedilemedi: {e}")
    
    def load_licenses_from_file(self):
        """Lisansları dosyadan yükler"""
        try:
            if os.path.exists("licenses.json"):
                with open("licenses.json", "r") as f:
                    self.license_manager.valid_licenses = json.load(f)
                print("📂 Lisanslar yüklendi.")
        except Exception as e:
            print(f"❌ Lisanslar yüklenemedi: {e}")
    
    def show_menu(self):
        """Ana menüyü gösterir"""
        while True:
            print("\n" + "="*50)
            print("🔧 ADMIN PANELİ")
            print("="*50)
            print("1. 📋 Tüm Lisansları Göster")
            print("2. ➕ Yeni Lisans Ekle")
            print("3. 📊 Lisans İstatistikleri")
            print("4. 💾 Lisansları Kaydet")
            print("5. 📂 Lisansları Yükle")
            print("6. ❌ Çıkış")
            
            choice = input("\nSeçiminiz (1-6): ").strip()
            
            if choice == "1":
                self.show_all_licenses()
            elif choice == "2":
                self.add_new_license()
            elif choice == "3":
                self.show_statistics()
            elif choice == "4":
                self.save_licenses_to_file()
            elif choice == "5":
                self.load_licenses_from_file()
            elif choice == "6":
                print("👋 Çıkılıyor...")
                break
            else:
                print("❌ Geçersiz seçim!")
    
    def show_statistics(self):
        """Lisans istatistiklerini gösterir"""
        print("\n" + "="*50)
        print("📊 LİSANS İSTATİSTİKLERİ")
        print("="*50)
        
        total_licenses = len(self.license_manager.valid_licenses)
        monthly_count = sum(1 for info in self.license_manager.valid_licenses.values() if info['type'] == 'monthly')
        quarterly_count = sum(1 for info in self.license_manager.valid_licenses.values() if info['type'] == 'quarterly')
        unlimited_count = sum(1 for info in self.license_manager.valid_licenses.values() if info['type'] == 'unlimited')
        
        total_revenue = sum(info['price'] for info in self.license_manager.valid_licenses.values())
        
        print(f"📦 Toplam Lisans: {total_licenses}")
        print(f"📅 1 Aylık: {monthly_count}")
        print(f"📅 3 Aylık: {quarterly_count}")
        print(f"♾️ Sınırsız: {unlimited_count}")
        print(f"💰 Toplam Gelir: ${total_revenue}")
        print("="*50)

def main():
    print("🔐 Admin Paneli Giriş")
    password = input("Şifre: ").strip()
    
    admin = AdminPanel()
    
    if password == admin.admin_password:
        print("✅ Giriş başarılı!")
        admin.load_licenses_from_file()
        admin.show_menu()
    else:
        print("❌ Yanlış şifre!")

if __name__ == "__main__":
    main() 