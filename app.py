import os
import threading
from flask import Flask, render_template_string, request, redirect, session
import json
import random
import string
import hashlib
import time

# Flask app oluştur
app = Flask(__name__)
app.secret_key = 'admin_panel_secret_key_2024'

# Environment variables kontrolü
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
admin_chat_id = os.environ.get('ADMIN_CHAT_ID')

# Bot'u ayrı thread'de çalıştır
def run_bot():
    try:
        print("🤖 Bot başlatılıyor...")
        print(f"📱 Bot Token: {bot_token[:20]}...")
        print(f"👤 Admin ID: {admin_chat_id}")
        
        # Environment variables'ları set et
        os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
        os.environ['ADMIN_CHAT_ID'] = admin_chat_id
        
        # telegram_bot.py dosyasını çalıştır
        exec(open("telegram_bot.py").read())
    except Exception as e:
        print(f"❌ Bot başlatma hatası: {e}")

# Bot thread'ini başlat
if bot_token:
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ Bot thread başlatıldı")

# Admin panel HTML template
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1f77b4 0%, #2c3e50 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .content { padding: 30px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
            text-align: center;
        }
        .stat-card h3 { font-size: 2rem; color: #1f77b4; margin-bottom: 10px; }
        .stat-card p { color: #666; font-weight: 500; }
        .section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
        }
        .section h2 { color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem; }
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-group select, .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-group select:focus, .form-group input:focus {
            outline: none;
            border-color: #1f77b4;
        }
        .btn {
            background: linear-gradient(135deg, #1f77b4 0%, #2c3e50 100%);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .license-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
        }
        .license-item {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .license-item.unlimited { border-left-color: #dc3545; }
        .license-item.monthly { border-left-color: #ffc107; }
        .license-item.quarterly { border-left-color: #17a2b8; }
        .license-info h4 { color: #333; margin-bottom: 5px; }
        .license-info p { color: #666; font-size: 14px; }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .login-form {
            max-width: 400px;
            margin: 100px auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .login-form h2 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-form">
        <h2>🔐 Admin Girişi</h2>
        <form method="POST" action="/admin/login">
            <div class="form-group">
                <label for="password">Şifre:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Giriş Yap</button>
        </form>
        {% if error %}
        <div class="alert alert-error">{{ error }}</div>
        {% endif %}
    </div>
    {% else %}
    <div class="container">
        <div class="header">
            <h1>🤖 Trading Bot Admin Panel</h1>
            <p>Lisans Yönetimi ve İstatistikler</p>
        </div>
        
        <div class="content">
            {% if message %}
            <div class="alert alert-success">{{ message }}</div>
            {% endif %}
            
            {% if error %}
            <div class="alert alert-error">{{ error }}</div>
            {% endif %}
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>{{ stats.total_licenses }}</h3>
                    <p>Toplam Lisans</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.unlimited_licenses }}</h3>
                    <p>Sınırsız Lisans</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.monthly_licenses }}</h3>
                    <p>Aylık Lisans</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.quarterly_licenses }}</h3>
                    <p>3 Aylık Lisans</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🔑 Yeni Lisans Oluştur</h2>
                <form method="POST" action="/admin/create_license">
                    <div class="form-group">
                        <label for="license_type">Lisans Tipi:</label>
                        <select id="license_type" name="license_type" required>
                            <option value="monthly">Aylık ($100)</option>
                            <option value="quarterly">3 Aylık ($200)</option>
                            <option value="unlimited">Sınırsız ($500)</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Lisans Oluştur</button>
                </form>
            </div>
            
            <div class="section">
                <h2>📋 Mevcut Lisanslar</h2>
                <div class="license-list">
                    {% for license_key, license_info in licenses.items() %}
                    <div class="license-item {{ license_info.type }}">
                        <div class="license-info">
                            <h4>{{ license_key }}</h4>
                            <p>Tip: {{ license_info.type.upper() }} | Fiyat: ${{ license_info.price }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="section">
                <h2>🚪 Çıkış</h2>
                <form method="POST" action="/admin/logout">
                    <button type="submit" class="btn">Çıkış Yap</button>
                </form>
            </div>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

def load_licenses():
    """Lisansları yükle"""
    try:
        with open('licenses.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_licenses(licenses):
    """Lisansları kaydet"""
    with open('licenses.json', 'w', encoding='utf-8') as f:
        json.dump(licenses, f, indent=2, ensure_ascii=False)

def generate_hash_like_key():
    """Hash-like lisans anahtarı oluştur"""
    random_data = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    timestamp = str(int(time.time()))
    combined = random_data + timestamp
    hash_object = hashlib.sha256(combined.encode())
    hash_hex = hash_object.hexdigest()
    key = hash_hex[:16].upper()
    formatted_key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])
    return formatted_key

@app.route('/')
def home():
    return redirect('/admin')

@app.route('/admin')
def admin_panel():
    if 'logged_in' not in session:
        return render_template_string(ADMIN_TEMPLATE, logged_in=False)
    
    licenses = load_licenses()
    
    # İstatistikleri hesapla
    stats = {
        'total_licenses': len(licenses),
        'unlimited_licenses': len([l for l in licenses.values() if l.get('type') == 'unlimited']),
        'monthly_licenses': len([l for l in licenses.values() if l.get('type') == 'monthly']),
        'quarterly_licenses': len([l for l in licenses.values() if l.get('type') == 'quarterly'])
    }
    
    return render_template_string(
        ADMIN_TEMPLATE, 
        logged_in=True, 
        licenses=licenses, 
        stats=stats,
        message=session.pop('message', None),
        error=session.pop('error', None)
    )

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    
    if password == 'admin123':  # Güvenli şifre kullanın!
        session['logged_in'] = True
        return redirect('/admin')
    else:
        return render_template_string(ADMIN_TEMPLATE, logged_in=False, error='Yanlış şifre!')

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return redirect('/admin')

@app.route('/admin/create_license', methods=['POST'])
def create_license():
    if 'logged_in' not in session:
        return redirect('/admin')
    
    license_type = request.form.get('license_type')
    
    if license_type == 'monthly':
        price = 100
        duration = 30
    elif license_type == 'quarterly':
        price = 200
        duration = 90
    elif license_type == 'unlimited':
        price = 500
        duration = -1
    else:
        session['error'] = 'Geçersiz lisans tipi!'
        return redirect('/admin')
    
    # Yeni lisans oluştur
    license_key = generate_hash_like_key()
    licenses = load_licenses()
    
    licenses[license_key] = {
        "type": license_type,
        "duration": duration,
        "price": price,
        "features": [
            "Temel Tarama",
            "Telegram Bildirimleri",
            "Formasyon Analizi"
        ]
    }
    
    if license_type == 'quarterly':
        licenses[license_key]["features"].append("Öncelikli Destek")
    elif license_type == 'unlimited':
        licenses[license_key]["features"].extend([
            "Öncelikli Destek",
            "Özel Formasyonlar",
            "7/24 Destek"
        ])
    
    save_licenses(licenses)
    session['message'] = f'Yeni {license_type} lisans oluşturuldu: {license_key}'
    
    return redirect('/admin')

if __name__ == '__main__':
    print("🚀 Admin Panel başlatılıyor...")
    
    # Railway için port ayarları
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Admin Panel: http://0.0.0.0:{port}/admin")
    print("🔐 Şifre: admin123")
    
    app.run(host='0.0.0.0', port=port, debug=False) 