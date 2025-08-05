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
            .license-item { padding: 10px; margin: 5px 0; border: 1px solid #eee; border-radius: 5px; }
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
                                <button class="btn btn-danger" onclick="deleteLicense('${license.key}')">🗑️ Sil</button>
                            </div>
                        `).join('');
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
                'price': info.get('price', 0)
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
            'expiry_date': None if license_type == 'unlimited' else None
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

if __name__ == '__main__':
    # Sadece Flask uygulamasını başlat, bot'u otomatik başlatma
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 