# Railway Debug Rehberi

## Sorun: Railway'de Proje Çekilemiyor

### 1. Environment Variables Kontrolü

Railway'de şu environment variables'ların doğru set edildiğinden emin olun:

```
TELEGRAM_BOT_TOKEN=8243806452:AAHzrY3CYZFhX64FKd9wFCY-JwBUnoV8KQA
ADMIN_CHAT_ID=7977984015
```

### 2. Railway Dashboard Kontrolü

1. Railway Dashboard'a git
2. Projenizi seçin
3. "Variables" sekmesine gidin
4. Şu değişkenlerin olduğunu kontrol edin:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_CHAT_ID`

### 3. Debug Bilgileri

Kod şu debug bilgilerini verecek:

```
🔍 Environment variables kontrol ediliyor...
🔍 Tüm environment variables:
  TELEGRAM_BOT_TOKEN: 8243806452:AAHzrY3CYZFhX64FKd9wFCY-JwBUnoV8KQA
  ADMIN_CHAT_ID: 7977984015
  RAILWAY_*: [çeşitli railway değişkenleri]
```

### 4. Bot Token Test

Bot token'ı test edilecek:

```
🔍 Bot token test ediliyor...
✅ Bot token geçerli!
```

### 5. Olası Sorunlar ve Çözümler

#### Sorun 1: TELEGRAM_BOT_KEY vs TELEGRAM_BOT_TOKEN
- **Sorun**: Kod `TELEGRAM_BOT_TOKEN` arıyor ama Railway'de `TELEGRAM_BOT_KEY` var
- **Çözüm**: Railway'de variable adını `TELEGRAM_BOT_TOKEN` olarak değiştirin

#### Sorun 2: Bot Token Geçersiz
- **Sorun**: Bot token 401 hatası veriyor
- **Çözüm**: Yeni bir bot token alın ve Railway'de güncelleyin

#### Sorun 3: Import Hataları
- **Sorun**: `botanlik.py` veya `telegram_bot.py` import edilemiyor
- **Çözüm**: Dosyaların doğru yerde olduğunu kontrol edin

### 6. Test Script'i

`test_env.py` script'ini çalıştırarak environment variables'ları test edin:

```bash
python test_env.py
```

### 7. Railway Log Kontrolü

Railway'de şu log'ları arayın:

```
🔍 Environment variables kontrol ediliyor...
✅ Bot token environment variable'dan yüklendi
🔍 Debug: Token başlangıcı: 8243806452:AAHzrY3CY...
🔍 Debug: Token uzunluğu: 46
✅ ADMIN_CHAT_ID yüklendi: 7977984015
🔍 Bot token test ediliyor...
✅ Bot token geçerli!
```

### 8. Yeni Proje Oluşturma

Eğer sorun devam ederse:

1. Railway'de yeni bir proje oluşturun
2. GitHub repository'nizi bağlayın
3. Environment variables'ları doğru şekilde set edin
4. Deploy edin

### 9. İletişim

Sorun devam ederse şu bilgileri paylaşın:
- Railway log'larının tamamı
- Environment variables listesi
- Hata mesajları 