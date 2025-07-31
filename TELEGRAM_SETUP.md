# 📱 Telegram Bot Kurulum Rehberi

## 🤖 Bot Oluşturma

### 1. Telegram'da Bot Oluşturun
1. Telegram'da `@BotFather` ile konuşun
2. `/newbot` komutunu gönderin
3. Bot için bir isim verin (örn: "Trading Bot")
4. Bot için bir kullanıcı adı verin (örn: "my_trading_bot")
5. BotFather size bir **TOKEN** verecek, bunu kaydedin

### 2. Bot Token'ını Alın
BotFather'dan aldığınız token şuna benzer olacak:
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 3. Chat ID'nizi Bulun
1. Oluşturduğunuz bot ile konuşun
2. `/start` komutunu gönderin
3. Tarayıcınızda şu adrese gidin:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
   ```
   (BOT_TOKEN yerine kendi token'ınızı yazın)
4. JSON yanıtında `"chat":{"id":123456789}` kısmındaki sayıyı bulun
5. Bu sayı sizin **CHAT ID**'niz

### 4. Config Dosyasını Güncelleyin
`config.py` dosyasını açın ve şu bilgileri ekleyin:

```python
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Kendi token'ınız
ADMIN_CHAT_ID = "123456789"  # Kendi chat ID'niz
```

## 📱 Bot Özellikleri

### Bildirim Türleri:
1. **🤖 Bot Başlangıç Bildirimi**
   - Bot çalışmaya başladığında gönderilir
   - Bot ayarları ve tarama sıklığı bilgisi

2. **🚨 Fırsat Bildirimleri**
   - Her bulunan fırsat için detaylı bilgi
   - Fiyat, TP, SL, R/R oranı, kaldıraç bilgileri
   - 3 TP seviyesi (varsa)
   - Sinyal gücü ve güven seviyesi

3. **📊 Tarama Özeti**
   - Taranan coin sayısı
   - Bulunan fırsat sayısı
   - Tarama süresi
   - Tarih ve saat

4. **⚠️ Hata Bildirimleri**
   - Bot hatalarında uyarı
   - Yeniden başlatma bilgisi

### Örnek Bildirim:
```
🚨 FUTURES TRADING FIRSATI #1

📈 BTCUSDT - Long (TOBO)

💰 Fiyat: 43250.50
🎯 TP: 44500.00
🛑 SL: 42000.00

📊 Potansiyel: %2.89
⚖️ R/R: 1.5:1 ✅
⚡ Kaldıraç: 5x
📦 Pozisyon: Kasanın %5'i
🎯 Hedef: %14.45
⚠️ Risk: %9.63
🔒 Margin: ISOLATED
💸 Max Kayıp: %9.63

🔥 Sinyal Gücü: ÇOK GÜÇLÜ (%85)

✅ FUTURES İŞLEM AÇILABİLİR!

🎯 3 TP SEVİYESİ:
• TP1 (İlk Kâr): 44500.00 (Ana TP) | +%2.9
• TP2 (Orta Kâr): 46000.00 (0.382) | +%6.4
• TP3 (Maksimum): 48000.00 (Formasyon Hedefi) | +%11.0

📅 Tarih: 15.12.2024 14:30:25
```

## 🔧 Sorun Giderme

### Bot Mesaj Göndermiyor:
1. Token'ın doğru olduğundan emin olun
2. Chat ID'nin doğru olduğundan emin olun
3. Bot ile konuştuğunuzdan emin olun (`/start` komutu)
4. İnternet bağlantınızı kontrol edin

### Chat ID Bulamıyorum:
1. Bot ile mutlaka konuşun (`/start` gönderin)
2. getUpdates URL'sini doğru yazdığınızdan emin olun
3. JSON yanıtında `"chat"` kısmını arayın

### Test Mesajı Gönderme:
Bot çalıştıktan sonra ilk bildirim otomatik gelecektir. Eğer gelmezse config dosyasını kontrol edin.

## 🚀 Başlatma

Botu başlatmak için:
```bash
python botanlik.py
```

Bot başladığında Telegram'da bildirim alacaksınız! 📱 