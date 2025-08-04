import os
import signal
import subprocess

print("🛑 Tüm bot instance'larını durduruyorum...")

# Python process'lerini bul ve durdur
try:
    # Railway'de çalışan Python process'lerini bul
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    
    for line in result.stdout.split('\n'):
        if 'python' in line and ('start.py' in line or 'botanlik.py' in line):
            parts = line.split()
            if len(parts) > 1:
                pid = parts[1]
                print(f"🔄 Process {pid} durduruluyor...")
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except:
                    pass
    
    print("✅ Tüm bot process'leri durduruldu!")
    
except Exception as e:
    print(f"❌ Hata: {e}")

print("🚀 Şimdi yeni bot başlatılabilir!") 