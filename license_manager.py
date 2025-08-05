import hashlib
import json
import os
from datetime import datetime, timedelta
import requests

class LicenseManager:
    def __init__(self):
        self.license_file = "license.json"
        self.licenses_file = "licenses.json"  # Admin panelinde oluşturulan lisanslar
        self.contact_telegram = "@tgtradingbot"
        
        # Varsayılan lisans anahtarları (geriye uyumluluk için)
        self.valid_licenses = {
            # 1 Aylık Paket - $200
            "MONTHLY_2024_001": {
                "type": "monthly",
                "duration": 30,
                "price": 200,
                "features": ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi"]
            },
            "MONTHLY_2024_002": {
                "type": "monthly", 
                "duration": 30,
                "price": 200,
                "features": ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi"]
            },
            
            # 3 Aylık Paket - $500 (İndirimli)
            "QUARTERLY_2024_001": {
                "type": "quarterly",
                "duration": 90,
                "price": 500,
                "features": ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek"]
            },
            "QUARTERLY_2024_002": {
                "type": "quarterly",
                "duration": 90,
                "price": 500,
                "features": ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek"]
            },
            
            # Sınırsız Paket - $1500
            "UNLIMITED_2024_001": {
                "type": "unlimited",
                "duration": -1,  # -1 = sınırsız
                "price": 1500,
                "features": ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek", "Özel Formasyonlar", "7/24 Destek"]
            },
            "UNLIMITED_2024_002": {
                "type": "unlimited",
                "duration": -1,
                "price": 1500,
                "features": ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek", "Özel Formasyonlar", "7/24 Destek"]
            }
        }
        
        # Admin panelinde oluşturulan lisansları yükle
        self.load_admin_licenses()
    
    def load_admin_licenses(self):
        """Admin panelinde oluşturulan lisansları yükler"""
        try:
            if os.path.exists(self.licenses_file):
                with open(self.licenses_file, 'r') as f:
                    admin_licenses = json.load(f)
                
                print(f"📂 Admin lisansları yükleniyor...")
                print(f"📋 Bulunan lisanslar: {list(admin_licenses.keys())}")
                
                # Admin lisanslarını mevcut listeye ekle
                for key, value in admin_licenses.items():
                    self.valid_licenses[key] = value
                    print(f"✅ Lisans eklendi: {key} - {value.get('type', 'unknown')}")
                    
                print(f"📂 {len(admin_licenses)} admin lisansı yüklendi.")
                print(f"📋 Toplam lisans sayısı: {len(self.valid_licenses)}")
            else:
                print(f"❌ {self.licenses_file} dosyası bulunamadı!")
        except Exception as e:
            print(f"❌ Admin lisansları yüklenemedi: {e}")
    
    def validate_license(self, license_key):
        """Lisans anahtarını doğrular"""
        # Önce admin lisanslarını yeniden yükle (güncel olması için)
        self.load_admin_licenses()
        
        print(f"🔍 Doğrulanan anahtar: {license_key}")
        print(f"📋 Mevcut anahtarlar: {list(self.valid_licenses.keys())}")
        
        if license_key not in self.valid_licenses:
            print(f"❌ Lisans bulunamadı: {license_key}")
            return False, "Geçersiz lisans anahtarı!"
        
        license_info = self.valid_licenses[license_key]
        print(f"✅ Lisans bulundu: {license_info}")
        
        # Lisansın aktif olup olmadığını kontrol et (admin panel lisansları için)
        if 'active' in license_info and not license_info.get('active', True):
            print(f"❌ Lisans pasif: {license_key}")
            return False, "Lisans pasif durumda!"
        
        print(f"✅ Lisans aktif: {license_key}")
        
        # Lisans bilgilerini kaydet
        license_data = {
            "key": license_key,
            "type": license_info["type"],
            "activated_date": datetime.now().isoformat(),
            "expiry_date": None,
            "features": license_info.get("features", []),  # Eğer yoksa boş liste
            "price": license_info.get("price", 0)  # Eğer yoksa 0
        }
        
        # Süre hesapla (admin panel lisansları için duration alanı yok)
        if "duration" in license_info:
            if license_info["duration"] == -1:  # Sınırsız
                license_data["expiry_date"] = None
                license_data["status"] = "active"
            else:
                expiry_date = datetime.now() + timedelta(days=license_info["duration"])
                license_data["expiry_date"] = expiry_date.isoformat()
                license_data["status"] = "active"
        else:
            # Admin panel lisansları için
            license_data["expiry_date"] = None  # Şimdilik sınırsız
            license_data["status"] = "active"
        
        # Lisans bilgilerini kaydet
        self.save_license(license_data)
        
        return True, license_data
    
    def check_license_status(self):
        """Mevcut lisans durumunu kontrol eder"""
        if not os.path.exists(self.license_file):
            return False, "Lisans bulunamadı! Lütfen lisans anahtarı girin."
        
        try:
            with open(self.license_file, 'r') as f:
                license_data = json.load(f)
            
            # Sınırsız lisans kontrolü
            if license_data["type"] == "unlimited":
                return True, license_data
            
            # Süre kontrolü (duration alanı yoksa varsayılan değerler kullan)
            if "duration" in license_data:
                if license_data["duration"] == -1:  # Sınırsız
                    return True, license_data
                elif license_data["duration"] > 0:
                    # Süre hesaplama
                    expiry_date = datetime.now() + timedelta(days=license_data["duration"])
                    if datetime.now() > expiry_date:
                        return False, "Lisans süreniz dolmuş! Yenilemek için @tgtradingbot ile iletişime geçin."
            else:
                # Admin panel lisansları için expiry_date kontrolü
                if license_data.get("expiry_date"):
                    expiry_date = datetime.fromisoformat(license_data["expiry_date"])
                    if datetime.now() > expiry_date:
                        return False, "Lisans süreniz dolmuş! Yenilemek için @tgtradingbot ile iletişime geçin."
            
            return True, license_data
            
        except Exception as e:
            return False, f"Lisans dosyası okunamadı: {e}"
    
    def save_license(self, license_data):
        """Lisans bilgilerini dosyaya kaydeder"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(license_data, f, indent=2)
        except Exception as e:
            print(f"Lisans kaydedilemedi: {e}")
    
    def get_license_info(self):
        """Lisans bilgilerini döndürür"""
        success, result = self.check_license_status()
        if success:
            return result
        return None
    
    def show_pricing_info(self):
        """Fiyatlandırma bilgilerini gösterir"""
        print("\n" + "="*60)
        print("🎯 TRADING BOT - LİSANS PAKETLERİ")
        print("="*60)
        print("📦 1 AYLIK PAKET - $200")
        print("   ✅ Temel Tarama")
        print("   ✅ Telegram Bildirimleri") 
        print("   ✅ Formasyon Analizi")
        print("   ⏰ 30 gün geçerli")
        print()
        print("📦 3 AYLIK PAKET - $500 (İndirimli)")
        print("   ✅ Temel Tarama")
        print("   ✅ Telegram Bildirimleri")
        print("   ✅ Formasyon Analizi")
        print("   ✅ Öncelikli Destek")
        print("   ⏰ 90 gün geçerli")
        print()
        print("📦 SINIRSIZ PAKET - $1500")
        print("   ✅ Temel Tarama")
        print("   ✅ Telegram Bildirimleri")
        print("   ✅ Formasyon Analizi")
        print("   ✅ Öncelikli Destek")
        print("   ✅ Özel Formasyonlar")
        print("   ✅ 7/24 Destek")
        print("   ⏰ Sınırsız kullanım")
        print("="*60)
        print(f"💬 İletişim: {self.contact_telegram}")
        print("="*60)
    
    def get_remaining_days(self):
        """Kalan gün sayısını döndürür"""
        license_info = self.get_license_info()
        if not license_info:
            return 0
        
        if license_info["type"] == "unlimited":
            return -1  # Sınırsız
        
        if license_info["expiry_date"]:
            expiry_date = datetime.fromisoformat(license_info["expiry_date"])
            remaining = (expiry_date - datetime.now()).days
            return max(0, remaining)
        
        return 0 