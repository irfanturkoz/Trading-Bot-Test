# 🌐 Streamlit Admin Panel Kurulum Rehberi

## 🚀 Hızlı Başlangıç

### 1. **Gerekli Kütüphaneleri Yükleyin**
```bash
pip install -r requirements.txt
```

### 2. **Admin Panelini Başlatın**
```bash
streamlit run admin_panel_web.py
```

### 3. **Tarayıcıda Açın**
Panel otomatik olarak `http://localhost:8501` adresinde açılacaktır.

---

## 🔐 Giriş Bilgileri

- **Şifre:** `admin123`
- **URL:** `http://localhost:8501`

---

## 📊 Panel Özellikleri

### 🏠 **Dashboard**
- 📦 Toplam lisans sayısı
- 📅 Paket dağılımı (1 aylık, 3 aylık, sınırsız)
- 💰 Toplam gelir
- 📊 İnteraktif grafikler (pasta ve çubuk grafikler)

### ➕ **Yeni Lisans Oluştur**
- 📦 Paket seçimi (1 aylık/3 aylık/sınırsız)
- ✅ Paket özelliklerini görüntüleme
- 🔑 Otomatik lisans anahtarı oluşturma
- 💾 Lisansları kaydetme

### 📋 **Lisanslar**
- 🔍 Arama ve filtreleme
- 📊 Lisans listesi (tablo formatında)
- 📈 Özet istatistikler
- 💰 Toplam değer hesaplama

### ⚙️ **Ayarlar**
- 💾 Veri yönetimi (kaydetme/yükleme)
- 🔐 Güvenlik önerileri
- ℹ️ Sistem bilgileri

---

## 🎨 Özellikler

### ✅ **Modern Arayüz**
- Responsive tasarım
- Koyu/açık tema desteği
- Mobil uyumlu

### 📊 **İnteraktif Grafikler**
- Pasta grafik (paket dağılımı)
- Çubuk grafik (gelir dağılımı)
- Plotly ile profesyonel görünüm

### 🔍 **Gelişmiş Arama**
- Anahtar kelime arama
- Paket tipi filtreleme
- Gerçek zamanlı sonuçlar

### 💾 **Veri Yönetimi**
- Otomatik kaydetme
- JSON formatında veri
- Yedekleme desteği

---

## 🛠️ Gelişmiş Kullanım

### **Özel Port ile Çalıştırma**
```bash
streamlit run admin_panel_web.py --server.port 8080
```

### **Harici Erişim**
```bash
streamlit run admin_panel_web.py --server.address 0.0.0.0
```

### **Güvenlik Ayarları**
```bash
streamlit run admin_panel_web.py --server.enableCORS false
```

---

## 📱 Mobil Kullanım

Panel tamamen mobil uyumludur:
- 📱 Telefon ve tablet desteği
- 👆 Dokunmatik ekran optimizasyonu
- 📐 Responsive tasarım

---

## 🔧 Sorun Giderme

### **Panel Açılmıyor**
1. Port kontrolü: `netstat -an | grep 8501`
2. Firewall ayarları
3. Streamlit sürüm kontrolü: `streamlit --version`

### **Grafikler Görünmüyor**
1. Plotly kütüphanesi kontrolü: `pip show plotly`
2. Tarayıcı JavaScript desteği
3. İnternet bağlantısı (CDN için)

### **Veri Kaydedilmiyor**
1. Dosya izinleri kontrolü
2. Disk alanı kontrolü
3. JSON format kontrolü

---

## 🚀 Production Deployment

### **Heroku ile Deploy**
```bash
# requirements.txt gerekli
# Procfile oluşturun:
web: streamlit run admin_panel_web.py --server.port=$PORT --server.address=0.0.0.0
```

### **Docker ile Deploy**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "admin_panel_web.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **VPS ile Deploy**
```bash
# Screen ile arka planda çalıştırma
screen -S admin_panel
streamlit run admin_panel_web.py --server.port=8501 --server.address=0.0.0.0
# Ctrl+A+D ile çıkış
```

---

## 📊 Performans

### **Önerilen Sistem Gereksinimleri**
- 💻 CPU: 2+ çekirdek
- 🧠 RAM: 4GB+
- 💾 Disk: 10GB+
- 🌐 İnternet: Stabil bağlantı

### **Optimizasyon İpuçları**
- Büyük veri setleri için sayfalama
- Grafik güncellemelerini optimize edin
- Gereksiz yeniden yüklemeleri önleyin

---

## 🔐 Güvenlik

### **Öneriler**
- 🔑 Admin şifresini değiştirin
- 🔒 HTTPS kullanın
- 🛡️ Firewall ayarları
- 📝 Erişim logları tutun

### **Şifre Değiştirme**
`admin_panel_web.py` dosyasında:
```python
self.admin_password = "yeni_sifreniz"
```

---

## 📞 Destek

- 💬 İletişim: @tgtradingbot
- 📧 Email: [email adresiniz]
- 🌐 Web: [web siteniz]

**Başarılar! 🚀** 