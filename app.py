from flask import Flask, jsonify, request, render_template_string
import threading
import time
import os
import json
from datetime import datetime
import telebot
from dotenv import load_dotenv
from license_manager import LicenseManager

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)

# Bot token'ını al - Yeni bot token'ı
BOT_TOKEN = "8259350638:AAEvnwmHddZ2raKa8bXYYxRG4U3kD0tdjZY"
print(f"🔍 Token kullanılıyor: {BOT_TOKEN[:20]}...")

# Bot'u oluştur
bot = telebot.TeleBot(BOT_TOKEN)
print("✅ Bot oluşturuldu!")

# Lisans yöneticisi
license_manager = LicenseManager()

# Bot durumu
bot_status = {
    "running": False,
    "last_run": None,
    "message": "Bot başlatılmadı"
}

# Kullanıcı durumları
user_states = {}

def run_bot_analysis():
    """Bot analizini ayrı thread'de çalıştır"""
    global bot_status
    bot_status["running"] = True
    bot_status["message"] = "Bot analizi çalışıyor..."
    
    try:
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
        "status": "Botanlik Bot API çalışıyor",
        "bot_status": bot_status,
        "endpoints": {
            "/": "Ana sayfa",
            "/status": "Bot durumu",
            "/start": "Bot'u başlat",
            "/health": "Sağlık kontrolü",
            "/admin": "Admin panel"
        }
    })

@app.route('/status')
def get_status():
    return jsonify(bot_status)

@app.route('/start')
def start_bot():
    if not bot_status["running"]:
        thread = threading.Thread(target=run_bot_analysis)
        thread.daemon = True
        thread.start()
        return jsonify({"message": "Bot başlatıldı", "status": "success"})
    else:
        return jsonify({"message": "Bot zaten çalışıyor", "status": "already_running"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/admin')
def admin_panel():
    """Admin panel HTML"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Botanlik Bot Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .header { text-align: center; margin-bottom: 30px; }
            .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .license-form { display: flex; gap: 10px; margin: 10px 0; }
            .license-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .license-list { max-height: 400px; overflow-y: auto; }
            .license-item { padding: 10px; margin: 5px 0; border: 1px solid #eee; border-radius: 5px; display: flex; align-items: center; gap: 10px; }
            .status-badge { padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }
            .status-badge.active { background: #28a745; color: white; }
            .status-badge.inactive { background: #dc3545; color: white; }
            .btn-warning { background: #ffc107; color: black; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Botanlik Bot Admin Panel</h1>
                <p>Bot durumu ve lisans yönetimi</p>
            </div>
            
            <div class="section">
                <h2>📊 Bot Durumu</h2>
                <div id="bot-status">Yükleniyor...</div>
                <button class="btn btn-primary" onclick="refreshStatus()">🔄 Yenile</button>
            </div>
            
            <div class="section">
                <h2>🔑 Lisans Yönetimi</h2>
                <div class="license-form">
                    <input type="text" id="license-key" class="license-input" placeholder="Lisans anahtarı">
                    <select id="license-type" class="license-input">
                        <option value="monthly">1 Aylık ($100)</option>
                        <option value="quarterly">3 Aylık ($200)</option>
                        <option value="unlimited">Sınırsız ($500)</option>
                    </select>
                    <button class="btn btn-success" onclick="addLicense()">➕ Lisans Ekle</button>
                    <button class="btn btn-primary" onclick="generateAutoLicense()">🎲 Otomatik Lisans Oluştur</button>
                </div>
                <div class="license-list" id="license-list">Yükleniyor...</div>
            </div>
            
            <div class="section">
                <h2>👥 Kullanıcı Yönetimi</h2>
                <div id="user-list">Yükleniyor...</div>
            </div>
        </div>
        
        <script>
            function refreshStatus() {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('bot-status').innerHTML = `
                            <p><strong>Durum:</strong> ${data.running ? '✅ Çalışıyor' : '❌ Durdu'}</p>
                            <p><strong>Son Çalışma:</strong> ${data.last_run || 'Henüz çalışmadı'}</p>
                            <p><strong>Mesaj:</strong> ${data.message}</p>
                        `;
                    });
            }
            
            function addLicense() {
                const key = document.getElementById('license-key').value;
                const type = document.getElementById('license-type').value;
                
                if (!key) {
                    alert('Lisans anahtarı gerekli!');
                    return;
                }
                
                fetch('/admin/add-license', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key, type})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Lisans eklendi!');
                        loadLicenses();
                    } else {
                        alert('Hata: ' + data.message);
                    }
                });
            }
            
            function loadLicenses() {
                fetch('/admin/licenses')
                    .then(response => response.json())
                    .then(data => {
                        const list = document.getElementById('license-list');
                        list.innerHTML = data.licenses.map(license => `
                            <div class="license-item">
                                <strong>${license.key}</strong> - ${license.type} ($${license.price})
                                <span class="status-badge ${license.active ? 'active' : 'inactive'}">
                                    ${license.active ? '✅ Aktif' : '❌ Pasif'}
                                </span>
                                <button class="btn btn-warning" onclick="toggleLicense('${license.key}', ${!license.active})">
                                    ${license.active ? '⏸️ Pasif Yap' : '▶️ Aktif Yap'}
                                </button>
                                <button class="btn btn-danger" onclick="deleteLicense('${license.key}')">🗑️ Sil</button>
                            </div>
                        `).join('');
                    });
            }
            
            function generateAutoLicense() {
                const type = document.getElementById('license-type').value;
                
                fetch('/admin/generate-license', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('license-key').value = data.license_key;
                        alert('Otomatik lisans oluşturuldu: ' + data.license_key);
                        loadLicenses();
                    } else {
                        alert('Hata: ' + data.message);
                    }
                });
            }
            
            function toggleLicense(key, active) {
                fetch('/admin/toggle-license', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({key, active})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Lisans ${active ? 'aktif' : 'pasif'} hale getirildi!`);
                        loadLicenses();
                    } else {
                        alert('Hata: ' + data.message);
                    }
                });
            }
            
            function deleteLicense(key) {
                if (confirm('Bu lisansı silmek istediğinizden emin misiniz?')) {
                    fetch('/admin/delete-license', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({key})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Lisans silindi!');
                            loadLicenses();
                        } else {
                            alert('Hata: ' + data.message);
                        }
                    });
                }
            }
            
            // Sayfa yüklendiğinde
            refreshStatus();
            loadLicenses();
        </script>
    </body>
    </html>
    """
    return html

@app.route('/admin/licenses')
def get_licenses():
    """Lisansları listele"""
    try:
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        license_list = []
        for key, info in licenses.items():
            license_list.append({
                'key': key,
                'type': info.get('type', 'unknown'),
                'price': info.get('price', 0),
                'active': info.get('active', True)  # Varsayılan olarak aktif
            })
        
        return jsonify({'licenses': license_list})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/admin/add-license', methods=['POST'])
def add_license():
    """Lisans ekle"""
    try:
        data = request.json
        key = data.get('key')
        license_type = data.get('type')
        
        if not key or not license_type:
            return jsonify({'success': False, 'message': 'Eksik parametreler'})
        
        # Lisans bilgilerini oluştur
        license_info = {
            'type': license_type,
            'price': {'monthly': 100, 'quarterly': 200, 'unlimited': 500}[license_type],
            'activated_date': datetime.now().isoformat(),
            'expiry_date': None if license_type == 'unlimited' else None,
            'active': True,
            'features': ['Temel Tarama', 'Telegram Bildirimleri', 'Formasyon Analizi']
        }
        
        # Lisansı kaydet
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        licenses[key] = license_info
        
        with open('licenses.json', 'w') as f:
            json.dump(licenses, f, indent=2)
        
        print(f"✅ Lisans eklendi: {key[:8]}...")
        
        return jsonify({'success': True, 'message': 'Lisans eklendi'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/delete-license', methods=['POST'])
def delete_license():
    """Lisans sil"""
    try:
        data = request.json
        key = data.get('key')
        
        if not key:
            return jsonify({'success': False, 'message': 'Lisans anahtarı gerekli'})
        
        # Lisansı sil
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        if key in licenses:
            del licenses[key]
            
            with open('licenses.json', 'w') as f:
                json.dump(licenses, f, indent=2)
            
            return jsonify({'success': True, 'message': 'Lisans silindi'})
        else:
            return jsonify({'success': False, 'message': 'Lisans bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/generate-license', methods=['POST'])
def generate_license():
    """Otomatik lisans oluştur"""
    try:
        data = request.json
        license_type = data.get('type')
        
        if not license_type:
            return jsonify({'success': False, 'message': 'Lisans tipi gerekli'})
        
        # Hash tabanlı lisans anahtarı oluştur
        import hashlib
        import time
        import random
        
        timestamp = str(int(time.time()))
        random_num = str(random.randint(1000, 9999))
        combined = f"{license_type}_{timestamp}_{random_num}"
        
        # SHA-256 hash oluştur ve 16 karakterlik parça al
        hash_object = hashlib.sha256(combined.encode())
        license_key = hash_object.hexdigest()[:16].upper()
        
        # Lisans bilgilerini oluştur
        license_info = {
            'type': license_type,
            'price': {'monthly': 100, 'quarterly': 200, 'unlimited': 500}[license_type],
            'activated_date': datetime.now().isoformat(),
            'expiry_date': None if license_type == 'unlimited' else None,
            'active': True,
            'features': ['Temel Tarama', 'Telegram Bildirimleri', 'Formasyon Analizi']
        }
        
        # Lisansı kaydet
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        licenses[license_key] = license_info
        
        with open('licenses.json', 'w') as f:
            json.dump(licenses, f, indent=2)
        
        print(f"✅ Otomatik lisans oluşturuldu: {license_key}")
        print(f"📋 Lisans bilgileri: {license_info}")
        
        return jsonify({
            'success': True, 
            'message': 'Lisans oluşturuldu',
            'license_key': license_key
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/toggle-license', methods=['POST'])
def toggle_license():
    """Lisans aktif/pasif durumunu değiştir"""
    try:
        data = request.json
        key = data.get('key')
        active = data.get('active')
        
        if not key:
            return jsonify({'success': False, 'message': 'Lisans anahtarı gerekli'})
        
        # Lisansı güncelle
        with open('licenses.json', 'r') as f:
            licenses = json.load(f)
        
        if key in licenses:
            licenses[key]['active'] = active
            
            with open('licenses.json', 'w') as f:
                json.dump(licenses, f, indent=2)
            
            status = "aktif" if active else "pasif"
            print(f"✅ Lisans durumu değiştirildi: {key[:8]}... - {status}")
            
            return jsonify({'success': True, 'message': f'Lisans {status} hale getirildi'})
        else:
            return jsonify({'success': False, 'message': 'Lisans bulunamadı'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Telegram Bot Handlers
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Başlangıç komutu"""
    user_id = message.from_user.id
    user_states[user_id] = "waiting_license"
    
    welcome_text = """
🤖 **Hoş Geldiniz Sniper Crypto!**

❌ **Lisansınız Yok!**

🔑 **Lisans Anahtarınızı Giriniz:** 
Lisans anahtarınızı buraya yazın.

💬 **Lisans Satın Almak İçin:** 
@ApfelTradingAdmin ile iletişime geçin.

📦 **Paketler:**
• 1 Aylık: $100
• 3 Aylık: $200  
• Sınırsız: $500
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['scan'])
def handle_scan(message):
    """Tarama komutu"""
    user_id = message.from_user.id
    
    # Lisans kontrolü
    success, result = license_manager.check_license_status()
    if not success:
        bot.reply_to(message, f"❌ {result}")
        return
    
    bot.reply_to(message, "🚀 TARAMA BAŞLATILIYOR\n⏱️ Yaklaşık 3-5 dakika içerisinde uygun işlemler gösterilecek...")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """Durum komutu"""
    user_id = message.from_user.id
    
    # Lisans kontrolü
    success, result = license_manager.check_license_status()
    if not success:
        bot.reply_to(message, f"❌ {result}")
        return
    
    bot.reply_to(message, "✅ Bot çalışıyor ve lisansınız aktif!")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Yardım komutu"""
    help_text = """
🤖 **Sniper Crypto Bot Komutları:**

/start - Bot'u başlat
/scan - Coin taraması yap
/status - Bot durumu
/help - Bu yardım mesajı
/test - Test komutu
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['test'])
def handle_test(message):
    """Test komutu"""
    bot.reply_to(message, "✅ Bot çalışıyor!")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Tüm mesajları işle"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    print(f"📨 Gelen mesaj: {text} (User: {user_id})")
    
    # Kullanıcı durumunu kontrol et
    if user_id not in user_states:
        user_states[user_id] = "waiting_license"
    
    if user_states[user_id] == "waiting_license":
        # Lisans anahtarı bekleniyor
        print(f"🔍 Lisans kontrol ediliyor: {text}")
        
        # Lisans doğrulama
        success, result = license_manager.validate_license(text)
        
        if success:
            print(f"✅ Lisans geçerli: {text}")
            user_states[user_id] = "licensed"
            bot.reply_to(message, f"✅ **Lisans Geçerli!**\n\n🎯 Artık bot'u kullanabilirsiniz!\n\nKomutlar:\n/scan - Tarama yap\n/status - Durum kontrolü\n/help - Yardım")
        else:
            print(f"❌ Lisans geçersiz: {text}")
            bot.reply_to(message, f"❌ **Yanlış Lisans Anahtarı!**\n\n🔑 **Gönderilen:** {text}\n\n❗ **Bu lisans anahtarı geçersiz!**\n\n💬 **Lisans Satın Almak İçin:**\n@ApfelTradingAdmin ile iletişime geçin.\n\n📦 **Paketler:**\n• 1 Aylık: $100\n• 3 Aylık: $200\n• Sınırsız: $500\n\n🔑 **Tekrar denemek için lisans anahtarınızı gönderin:**")
    else:
        # Lisanslı kullanıcı
        bot.reply_to(message, "✅ Lisansınız aktif! /scan komutu ile tarama yapabilirsiniz.")

def run_telegram_bot():
    """Telegram bot'u çalıştır"""
    print("🚀 Telegram Bot başlatılıyor...")
    print(f"📱 Bot Token: {BOT_TOKEN[:20]}...")
    
    try:
        # Webhook'u temizle ve eski güncellemeleri temizle
        bot.remove_webhook()
        
        # Eski güncellemeleri temizle
        try:
            bot.get_updates(offset=-1)
        except:
            pass
        
        print("📱 Bot polling başlatılıyor...")
        bot.polling(none_stop=True, interval=3, timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"❌ Bot hatası: {e}")
        # Hata durumunda tekrar dene
        import time
        time.sleep(10)
        run_telegram_bot()

if __name__ == '__main__':
    # Flask ve Telegram bot'u aynı anda çalıştır
    import threading
    
    # Telegram bot'u ayrı thread'de başlat
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask uygulamasını başlat
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 