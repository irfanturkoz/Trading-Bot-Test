# 🔐 Güvenli Token Kurulum Rehberi

## ⚠️ ÖNEMLİ: Token Güvenliği

Bot token'ınızı GitHub'da gizlemek için aşağıdaki adımları takip edin:

### 1. .env Dosyası Oluşturun

Proje klasörünüzde `.env` dosyası oluşturun:

```bash
# Windows PowerShell
"TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" | Out-File -FilePath .env -Encoding UTF8

# Linux/Mac
echo "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env
```

### 2. Token'ınızı Ekleyin

`.env` dosyasını açın ve token'ınızı ekleyin:

```
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

### 3. .gitignore Kontrolü

`.gitignore` dosyasında şu satırların olduğundan emin olun:

```
# Sensitive data
*.env
.env
.env.local
.env.production
```

### 4. Güvenlik Kontrolü

Token'ınızın GitHub'a yüklenmediğini kontrol edin:

```bash
git status
```

`.env` dosyası "untracked" olarak görünmemeli.

## 🚀 Bot Çalıştırma

### Gereksinimler

```bash
pip install -r requirements.txt
```

### Bot Başlatma

```bash
python app.py
```

## 📱 Telegram Bot Kurulumu

1. Telegram'da `@BotFather` ile konuşun
2. `/newbot` komutunu gönderin
3. Bot için isim ve kullanıcı adı verin
4. Aldığınız token'ı `.env` dosyasına ekleyin

## 🔍 Test Etme

Bot'un çalışıp çalışmadığını test etmek için:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token:', os.getenv('TELEGRAM_BOT_TOKEN')[:20] + '...')"
```

## ⚠️ Güvenlik Uyarıları

- ❌ Token'ı asla kod içinde yazmayın
- ❌ Token'ı GitHub'a yüklemeyin
- ❌ Token'ı başkalarıyla paylaşmayın
- ✅ Token'ı sadece `.env` dosyasında saklayın
- ✅ `.env` dosyasını `.gitignore`'a ekleyin

## 🆘 Sorun Giderme

### Token Bulunamadı Hatası

```
❌ TELEGRAM_BOT_TOKEN environment variable bulunamadı!
```

**Çözüm:**
1. `.env` dosyasının var olduğunu kontrol edin
2. Token'ın doğru yazıldığını kontrol edin
3. Dosya formatının doğru olduğunu kontrol edin

### 401 Unauthorized Hatası

```
Error code: 401. Description: Unauthorized
```

**Çözüm:**
1. Token'ın doğru olduğunu kontrol edin
2. Bot'un aktif olduğunu kontrol edin
3. Yeni bir token alın

## 📞 Destek

Sorun yaşarsanız:
1. `.env` dosyasını kontrol edin
2. Token'ın geçerli olduğunu doğrulayın
3. Bot'un Telegram'da aktif olduğunu kontrol edin 