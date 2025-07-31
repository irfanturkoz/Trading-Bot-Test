# 🔑 Lisans Sistemi Rehberi

## 📦 Lisans Paketleri

### 1. **1 AYLIK PAKET - $200**
- ✅ Temel Tarama
- ✅ Telegram Bildirimleri
- ✅ Formasyon Analizi
- ⏰ 30 gün geçerli

### 2. **3 AYLIK PAKET - $500 (İndirimli)**
- ✅ Temel Tarama
- ✅ Telegram Bildirimleri
- ✅ Formasyon Analizi
- ✅ Öncelikli Destek
- ⏰ 90 gün geçerli

### 3. **SINIRSIZ PAKET - $1500**
- ✅ Temel Tarama
- ✅ Telegram Bildirimleri
- ✅ Formasyon Analizi
- ✅ Öncelikli Destek
- ✅ Özel Formasyonlar
- ✅ 7/24 Destek
- ⏰ Sınırsız kullanım

---

## 🚀 Kullanıcı Kılavuzu

### Bot Başlatma:
```bash
python botanlik.py
```

Bot başladığında:
1. Lisans kontrolü yapılır
2. Lisans yoksa fiyatlandırma gösterilir
3. Lisans anahtarı istenir
4. Doğru anahtar girilirse bot çalışır

### Lisans Bilgilerini Görme:
```bash
python license_info.py
```

---

## 🔧 Admin Paneli

### Admin Paneli Başlatma:
```bash
python admin_panel.py
```

**Şifre:** `admin123`

### Admin Panel Özellikleri:
1. **📋 Tüm Lisansları Göster**
   - Mevcut tüm lisans anahtarlarını listeler

2. **➕ Yeni Lisans Ekle**
   - Yeni lisans anahtarı oluşturur
   - Otomatik benzersiz anahtar üretir

3. **📊 Lisans İstatistikleri**
   - Toplam lisans sayısı
   - Paket dağılımı
   - Toplam gelir

4. **💾 Lisansları Kaydet**
   - Lisansları `licenses.json` dosyasına kaydeder

5. **📂 Lisansları Yükle**
   - `licenses.json` dosyasından lisansları yükler

---

## 📁 Dosya Yapısı

```
📦 Trading Bot
├── 🐍 botanlik.py          # Ana bot (lisans kontrolü ile)
├── 🔑 license_manager.py   # Lisans yönetimi
├── 📊 license_info.py      # Lisans bilgilerini göster
├── 🔧 admin_panel.py       # Admin paneli
├── 📄 config.py            # Bot ayarları
├── 📄 license.json         # Aktif lisans bilgileri
├── 📄 licenses.json        # Tüm lisans anahtarları
└── 📱 telegram_notifier.py # Telegram bildirimleri
```

---

## 💰 Satış Süreci

### 1. **Müşteri İletişimi**
- Müşteri `@tgtradingbot` ile iletişime geçer
- Paket seçimi yapar (1 aylık/3 aylık/sınırsız)

### 2. **Ödeme**
- Müşteri ödemeyi yapar
- Admin panelinden yeni lisans oluşturulur

### 3. **Lisans Teslimi**
- Lisans anahtarı müşteriye gönderilir
- Müşteri anahtarı bot'a girer
- Bot çalışmaya başlar

### 4. **Destek**
- Müşteri sorunları için `@tgtradingbot` ile iletişim
- Öncelikli destek (3 aylık ve sınırsız paketler için)

---

## 🔐 Güvenlik

### Lisans Anahtarları:
- Benzersiz ve karmaşık yapıda
- Zaman damgalı
- Rastgele karakterler içerir

### Örnek Anahtar Formatları:
- `MONTHLY_20241215_143025_ABC123`
- `QUARTERLY_20241215_143025_DEF456`
- `UNLIMITED_20241215_143025_GHI789`

---

## 📊 İstatistikler

### Gelir Hesaplama:
- **1 Aylık:** $200 × satış sayısı
- **3 Aylık:** $500 × satış sayısı
- **Sınırsız:** $1500 × satış sayısı

### Örnek Senaryo:
- 10 adet 1 aylık: $2,000
- 5 adet 3 aylık: $2,500
- 2 adet sınırsız: $3,000
- **Toplam:** $7,500

---

## 🚨 Önemli Notlar

1. **Lisans Süresi:** Süre dolduğunda bot otomatik durur
2. **İletişim:** Tüm sorunlar için `@tgtradingbot`
3. **Yenileme:** Lisans bitmeden önce yenileme yapılmalı
4. **Güvenlik:** Admin şifresini güvenli tutun
5. **Yedekleme:** `licenses.json` dosyasını düzenli yedekleyin

---

## 🎯 Başarı İpuçları

1. **Müşteri Desteği:** Hızlı ve kaliteli destek verin
2. **Demo:** Potansiyel müşterilere demo gösterin
3. **Referans:** Memnun müşterilerden referans alın
4. **Güncelleme:** Botu düzenli güncelleyin
5. **Pazarlama:** Sosyal medyada bot özelliklerini paylaşın

**Başarılar! 🚀💰** 