import os
import threading

# Environment variables kontrolü
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
admin_chat_id = os.environ.get('ADMIN_CHAT_ID')

if not bot_token:
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return """
        <h1>🤖 Trading Bot - Kurulum Gerekli</h1>
        <p>❌ TELEGRAM_BOT_TOKEN environment variable eksik!</p>
        <p>Railway'de Variables sekmesinden ekleyin:</p>
        <ul>
            <li>TELEGRAM_BOT_TOKEN = 8243806452:AAHzrY3CYZFhX64FKd9wFCY-JwBUnoV8KQA</li>
            <li>ADMIN_CHAT_ID = 7977984015</li>
        </ul>
        """
    
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)

else:
    # Bot'u başlat
    print("🤖 Bot başlatılıyor...")
    print(f"📱 Bot Token: {bot_token[:20]}...")
    print(f"👤 Admin ID: {admin_chat_id}")
    
    # telegram_bot.py dosyasını çalıştır
    exec(open("telegram_bot.py").read()) 