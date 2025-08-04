from flask import Flask, jsonify
import threading
import time
import os

app = Flask(__name__)

# Bot durumu
bot_status = {
    "running": False,
    "last_run": None,
    "message": "Bot başlatılmadı"
}

def run_bot():
    """Bot'u ayrı bir thread'de çalıştır"""
    global bot_status
    bot_status["running"] = True
    bot_status["message"] = "Bot çalışıyor..."
    
    try:
        # Bot'u import et ve çalıştır
        from botanlik import main as bot_main
        bot_main()
    except Exception as e:
        bot_status["message"] = f"Bot hatası: {str(e)}"
    finally:
        bot_status["running"] = False
        bot_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")

@app.route('/')
def home():
    return jsonify({
        "status": "Bot API çalışıyor",
        "bot_status": bot_status,
        "instructions": "Bot'u başlatmak için /start endpoint'ini kullan"
    })

@app.route('/start')
def start_bot():
    if not bot_status["running"]:
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return jsonify({"message": "Bot başlatıldı", "status": "success"})
    else:
        return jsonify({"message": "Bot zaten çalışıyor", "status": "already_running"})

@app.route('/status')
def get_status():
    return jsonify(bot_status)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

if __name__ == '__main__':
    # Sadece Flask uygulamasını başlat, bot'u otomatik başlatma
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 