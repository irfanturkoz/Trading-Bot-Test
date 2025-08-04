import os
import signal
import subprocess
import time

print("🛑 Tüm bot instance'larını durduruyorum...")

# Railway'de çalışan Python process'lerini bul ve durdur
try:
    # ps aux komutu ile process'leri listele
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    
    killed_count = 0
    for line in result.stdout.split('\n'):
        if 'python' in line and ('start.py' in line or 'botanlik.py' in line or 'telegram_bot.py' in line or 'app.py' in line):
            parts = line.split()
            if len(parts) > 1:
                pid = parts[1]
                try:
                    print(f"🔄 Process {pid} durduruluyor...")
                    # Önce SIGTERM ile dene
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    
                    # Hala çalışıyorsa SIGKILL ile zorla durdur
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"💀 Process {pid} zorla durduruldu")
                    except:
                        pass
                    
                    killed_count += 1
                    time.sleep(1)  # Kısa bekle
                except Exception as e:
                    print(f"❌ Process {pid} durdurulamadı: {e}")
    
    print(f"✅ {killed_count} bot process'i durduruldu!")
    
    # 10 saniye bekle
    print("⏳ 10 saniye bekleniyor...")
    time.sleep(10)
    
    # Kalan process'leri kontrol et
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    remaining = 0
    for line in result.stdout.split('\n'):
        if 'python' in line and ('start.py' in line or 'botanlik.py' in line or 'telegram_bot.py' in line or 'app.py' in line):
            remaining += 1
    
    if remaining == 0:
        print("✅ Tüm bot process'leri durduruldu!")
    else:
        print(f"⚠️ {remaining} bot process'i hala çalışıyor")
        
except Exception as e:
    print(f"❌ Hata: {e}")

print("🚀 Şimdi yeni bot başlatılabilir!")

# 5 saniye daha bekle
time.sleep(5)

# start.py'yi başlat
print("🚀 start.py başlatılıyor...")
try:
    subprocess.run(['python', 'start.py'], check=True)
except Exception as e:
    print(f"❌ start.py başlatılamadı: {e}") 