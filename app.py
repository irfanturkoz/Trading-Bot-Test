from flask import Flask, request, jsonify
import os
import threading
import time
import subprocess
import sys

app = Flask(__name__)

# Bot'u ayrı bir process'te başlat
def start_bot_process():
    print("🤖 Bot process başlatılıyor...")
    
    # Bot'u ayrı bir Python process'inde çalıştır
    try:
        # telegram_bot.py dosyasını doğrudan çalıştır
        subprocess.Popen([sys.executable, "telegram_bot.py"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        print("✅ Bot process başlatıldı")
    except Exception as e:
        print(f"❌ Bot process hatası: {e}")

# Bot process'ini başlat
print("🚀 Bot process'i başlatılıyor...")
start_bot_process()

@app.route('/')
def home():
    return jsonify({
        "status": "Bot çalışıyor!",
        "message": "Telegram bot aktif durumda"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 