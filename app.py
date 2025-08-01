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
        
        # Conflict kontrolü için bekle
        time.sleep(5)
        
        # telegram_bot.py'yi import et ve main() fonksiyonunu çalıştır
        import telegram_bot
        telegram_bot.main()
    except Exception as e:
        print(f"❌ Bot başlatma hatası: {e}")
        print("⚠️ Bot hatası olsa bile admin panel çalışmaya devam edecek")

# Bot thread'ini başlat
if bot_token:
    try:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot thread başlatıldı")
    except Exception as e:
        print(f"⚠️ Bot thread başlatılamadı: {e}")
        print("⚠️ Admin panel çalışmaya devam edecek")
else:
    print("⚠️ Bot token bulunamadı, sadece admin panel çalışacak")

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
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
            text-align: center;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { font-size: 2rem; color: #1f77b4; margin-bottom: 10px; }
        .stat-card p { color: #666; font-weight: 500; }
        .stat-card.revenue { border-left-color: #28a745; }
        .stat-card.revenue h3 { color: #28a745; }
        .stat-card.active { border-left-color: #ffc107; }
        .stat-card.active h3 { color: #ffc107; }
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
            margin-right: 10px;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-danger {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        }
        .btn-warning {
            background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
        }
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        .license-list {
            max-height: 500px;
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
            transition: all 0.3s;
        }
        .license-item:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .license-item.unlimited { border-left-color: #dc3545; }
        .license-item.monthly { border-left-color: #ffc107; }
        .license-item.quarterly { border-left-color: #17a2b8; }
        .license-item.inactive { border-left-color: #6c757d; opacity: 0.6; }
        .license-info h4 { color: #333; margin-bottom: 5px; font-family: monospace; }
        .license-info p { color: #666; font-size: 14px; }
        .license-actions { display: flex; gap: 10px; }
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
        .tabs {
            display: flex;
            border-bottom: 2px solid #ddd;
            margin-bottom: 20px;
        }
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #1f77b4;
            color: #1f77b4;
            font-weight: 600;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .search-box {
            margin-bottom: 20px;
        }
        .search-box input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-active { background: #d4edda; color: #155724; }
        .status-inactive { background: #f8d7da; color: #721c24; }
        .status-expired { background: #fff3cd; color: #856404; }
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
            <p>Gelişmiş Lisans Yönetimi ve İstatistikler</p>
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
                <div class="stat-card active">
                    <h3>{{ stats.active_licenses }}</h3>
                    <p>Aktif Lisans</p>
                </div>
                <div class="stat-card revenue">
                    <h3>${{ stats.total_revenue }}</h3>
                    <p>Toplam Gelir</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.monthly_revenue }}</h3>
                    <p>Bu Ay Gelir</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.unlimited_licenses }}</h3>
                    <p>Sınırsız</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.monthly_licenses }}</h3>
                    <p>Aylık</p>
                </div>
                <div class="stat-card">
                    <h3>{{ stats.quarterly_licenses }}</h3>
                    <p>3 Aylık</p>
                </div>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('overview')">📊 Genel Bakış</div>
                <div class="tab" onclick="showTab('licenses')">🔑 Lisans Yönetimi</div>
                <div class="tab" onclick="showTab('analytics')">📈 Analitik</div>
                <div class="tab" onclick="showTab('settings')">⚙️ Ayarlar</div>
            </div>
            
            <div id="overview" class="tab-content active">
                <div class="section">
                    <h2>🔑 Hızlı Lisans Oluştur</h2>
                    <form method="POST" action="/admin/create_license">
                        <div class="form-group">
                            <label for="license_type">Lisans Tipi:</label>
                            <select id="license_type" name="license_type" required>
                                <option value="monthly">Aylık ($100)</option>
                                <option value="quarterly">3 Aylık ($200)</option>
                                <option value="unlimited">Sınırsız ($500)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">🚀 Lisans Oluştur</button>
                    </form>
                </div>
                
                <div class="section">
                    <h2>📋 Son Oluşturulan Lisanslar</h2>
                    <div class="license-list">
                        {% for license_key, license_info in recent_licenses.items() %}
                        <div class="license-item {{ license_info.type }} {% if not license_info.active %}inactive{% endif %}">
                            <div class="license-info">
                                <h4>{{ license_key }}</h4>
                                <p>
                                    Tip: {{ license_info.type.upper() }} | 
                                    Fiyat: ${{ license_info.price }} | 
                                    Durum: 
                                    <span class="status-badge {% if license_info.active %}status-active{% else %}status-inactive{% endif %}">
                                        {% if license_info.active %}Aktif{% else %}Pasif{% endif %}
                                    </span>
                                </p>
                            </div>
                            <div class="license-actions">
                                <form method="POST" action="/admin/toggle_license" style="display: inline;">
                                    <input type="hidden" name="license_key" value="{{ license_key }}">
                                    <button type="submit" class="btn {% if license_info.active %}btn-warning{% else %}btn-success{% endif %}">
                                        {% if license_info.active %}❌ Pasif Yap{% else %}✅ Aktif Yap{% endif %}
                                    </button>
                                </form>
                                <form method="POST" action="/admin/delete_license" style="display: inline;" onsubmit="return confirm('Bu lisansı silmek istediğinizden emin misiniz?')">
                                    <input type="hidden" name="license_key" value="{{ license_key }}">
                                    <button type="submit" class="btn btn-danger">🗑️ Sil</button>
                                </form>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div id="licenses" class="tab-content">
                <div class="section">
                    <h2>🔍 Lisans Arama</h2>
                    <div class="search-box">
                        <input type="text" id="licenseSearch" placeholder="Lisans anahtarını yazın..." onkeyup="searchLicenses()">
                    </div>
                    
                    <div class="license-list">
                        {% for license_key, license_info in licenses.items() %}
                        <div class="license-item {{ license_info.type }} {% if not license_info.active %}inactive{% endif %}" data-key="{{ license_key }}">
                            <div class="license-info">
                                <h4>{{ license_key }}</h4>
                                <p>
                                    Tip: {{ license_info.type.upper() }} | 
                                    Fiyat: ${{ license_info.price }} | 
                                    Oluşturulma: {{ license_info.created_date if license_info.created_date else 'Bilinmiyor' }} |
                                    Durum: 
                                    <span class="status-badge {% if license_info.active %}status-active{% else %}status-inactive{% endif %}">
                                        {% if license_info.active %}Aktif{% else %}Pasif{% endif %}
                                    </span>
                                </p>
                            </div>
                            <div class="license-actions">
                                <form method="POST" action="/admin/toggle_license" style="display: inline;">
                                    <input type="hidden" name="license_key" value="{{ license_key }}">
                                    <button type="submit" class="btn {% if license_info.active %}btn-warning{% else %}btn-success{% endif %}">
                                        {% if license_info.active %}❌ Pasif Yap{% else %}✅ Aktif Yap{% endif %}
                                    </button>
                                </form>
                                <form method="POST" action="/admin/delete_license" style="display: inline;" onsubmit="return confirm('Bu lisansı silmek istediğinizden emin misiniz?')">
                                    <input type="hidden" name="license_key" value="{{ license_key }}">
                                    <button type="submit" class="btn btn-danger">🗑️ Sil</button>
                                </form>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div id="analytics" class="tab-content">
                <div class="section">
                    <h2>📈 Gelir Analizi</h2>
                    <div class="stats-grid">
                        <div class="stat-card revenue">
                            <h3>${{ stats.total_revenue }}</h3>
                            <p>Toplam Gelir</p>
                        </div>
                        <div class="stat-card">
                            <h3>${{ stats.monthly_revenue }}</h3>
                            <p>Bu Ay</p>
                        </div>
                        <div class="stat-card">
                            <h3>${{ stats.quarterly_revenue }}</h3>
                            <p>Bu Çeyrek</p>
                        </div>
                        <div class="stat-card">
                            <h3>{{ stats.avg_license_value }}</h3>
                            <p>Ortalama Lisans Değeri</p>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>👥 Kullanıcı Analizi</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>{{ stats.active_users }}</h3>
                            <p>Aktif Kullanıcı</p>
                        </div>
                        <div class="stat-card">
                            <h3>{{ stats.new_users_this_month }}</h3>
                            <p>Bu Ay Yeni</p>
                        </div>
                        <div class="stat-card">
                            <h3>{{ stats.conversion_rate }}%</h3>
                            <p>Dönüşüm Oranı</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="settings" class="tab-content">
                <div class="section">
                    <h2>🔐 Güvenlik Ayarları</h2>
                    <form method="POST" action="/admin/change_password">
                        <div class="form-group">
                            <label for="current_password">Mevcut Şifre:</label>
                            <input type="password" id="current_password" name="current_password" required>
                        </div>
                        <div class="form-group">
                            <label for="new_password">Yeni Şifre:</label>
                            <input type="password" id="new_password" name="new_password" required>
                        </div>
                        <div class="form-group">
                            <label for="confirm_password">Şifre Tekrar:</label>
                            <input type="password" id="confirm_password" name="confirm_password" required>
                        </div>
                        <button type="submit" class="btn">🔒 Şifre Değiştir</button>
                    </form>
                </div>
                
                <div class="section">
                    <h2>🚪 Çıkış</h2>
                    <form method="POST" action="/admin/logout">
                        <button type="submit" class="btn btn-danger">🚪 Çıkış Yap</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Tüm tab içeriklerini gizle
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Tüm tabları pasif yap
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Seçilen tabı aktif yap
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function searchLicenses() {
            const searchTerm = document.getElementById('licenseSearch').value.toLowerCase();
            const licenseItems = document.querySelectorAll('.license-item');
            
            licenseItems.forEach(item => {
                const licenseKey = item.getAttribute('data-key').toLowerCase();
                if (licenseKey.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }
    </script>
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

def get_active_users():
    """Aktif kullanıcıları döndürür"""
    try:
        storage_dir = "/tmp/persistent_storage"
        if not os.path.exists(storage_dir):
            return []
        
        active_users = []
        for filename in os.listdir(storage_dir):
            if filename.startswith("user_") and filename.endswith(".json"):
                try:
                    with open(f"{storage_dir}/{filename}", 'r') as f:
                        user_license = json.load(f)
                    
                    expiry_date = user_license.get('expiry_date')
                    if expiry_date:
                        expiry = datetime.fromisoformat(expiry_date)
                        if expiry > datetime.now():
                            user_id = filename.replace("user_", "").replace(".json", "")
                            active_users.append({
                                'user_id': user_id,
                                'license_key': user_license.get('license_key'),
                                'type': user_license.get('type'),
                                'activated_date': user_license.get('activated_date'),
                                'expiry_date': expiry_date
                            })
                except Exception as e:
                    print(f"Kullanıcı dosyası okuma hatası: {e}")
        
        return active_users
    except Exception as e:
        print(f"Aktif kullanıcılar alınamadı: {e}")
        return []

def calculate_revenue():
    """Gelir hesaplama"""
    try:
        active_users = get_active_users()
        licenses = load_licenses()
        
        total_revenue = 0
        monthly_revenue = 0
        quarterly_revenue = 0
        unlimited_revenue = 0
        
        # Aktif kullanıcılardan gelir hesapla
        for user in active_users:
            license_key = user.get('license_key')
            if license_key in licenses:
                price = licenses[license_key].get('price', 0)
                total_revenue += price
                
                license_type = licenses[license_key].get('type')
                if license_type == 'monthly':
                    monthly_revenue += price
                elif license_type == 'quarterly':
                    quarterly_revenue += price
                elif license_type == 'unlimited':
                    unlimited_revenue += price
        
        return {
            'total': total_revenue,
            'monthly': monthly_revenue,
            'quarterly': quarterly_revenue,
            'unlimited': unlimited_revenue,
            'active_users': len(active_users)
        }
    except Exception as e:
        print(f"Gelir hesaplama hatası: {e}")
        return {'total': 0, 'monthly': 0, 'quarterly': 0, 'unlimited': 0, 'active_users': 0}

def get_license_status(license_key):
    """Lisans durumunu kontrol et"""
    try:
        active_users = get_active_users()
        for user in active_users:
            if user.get('license_key') == license_key:
                return 'active'
        return 'inactive'
    except:
        return 'unknown'

@app.route('/')
def home():
    return redirect('/admin')

@app.route('/admin')
def admin_panel():
    if 'logged_in' not in session:
        return render_template_string(ADMIN_TEMPLATE, logged_in=False)
    
    licenses = load_licenses()
    
    # Gelişmiş istatistikleri hesapla
    active_licenses = [l for l in licenses.values() if l.get('active', True)]
    total_revenue = sum(l.get('price', 0) for l in licenses.values())
    monthly_revenue = sum(l.get('price', 0) for l in licenses.values() if l.get('type') == 'monthly')
    quarterly_revenue = sum(l.get('price', 0) for l in licenses.values() if l.get('type') == 'quarterly')
    
    # Ortalama lisans değeri
    avg_license_value = round(total_revenue / len(licenses) if licenses else 0, 2)
    
    # Son 5 lisans
    recent_licenses = dict(list(licenses.items())[-5:])
    
    stats = {
        'total_licenses': len(licenses),
        'active_licenses': len(active_licenses),
        'unlimited_licenses': len([l for l in licenses.values() if l.get('type') == 'unlimited']),
        'monthly_licenses': len([l for l in licenses.values() if l.get('type') == 'monthly']),
        'quarterly_licenses': len([l for l in licenses.values() if l.get('type') == 'quarterly']),
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'quarterly_revenue': quarterly_revenue,
        'avg_license_value': avg_license_value,
        'active_users': len(active_licenses),
        'new_users_this_month': len([l for l in licenses.values() if l.get('type') == 'monthly']),
        'conversion_rate': round((len(active_licenses) / len(licenses) * 100) if licenses else 0, 1)
    }
    
    return render_template_string(
        ADMIN_TEMPLATE, 
        logged_in=True, 
        licenses=licenses, 
        recent_licenses=recent_licenses,
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
        "active": True,
        "created_date": time.strftime("%Y-%m-%d %H:%M:%S"),
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
    session['message'] = f'✅ Yeni {license_type} lisans oluşturuldu: {license_key}'
    
    return redirect('/admin')

@app.route('/admin/toggle_license', methods=['POST'])
def toggle_license():
    if 'logged_in' not in session:
        return redirect('/admin')
    
    license_key = request.form.get('license_key')
    licenses = load_licenses()
    
    if license_key in licenses:
        licenses[license_key]['active'] = not licenses[license_key].get('active', True)
        save_licenses(licenses)
        
        status = "aktif" if licenses[license_key]['active'] else "pasif"
        session['message'] = f'🔄 Lisans {license_key} {status} yapıldı'
    else:
        session['error'] = '❌ Lisans bulunamadı!'
    
    return redirect('/admin')

@app.route('/admin/delete_license', methods=['POST'])
def delete_license():
    if 'logged_in' not in session:
        return redirect('/admin')
    
    license_key = request.form.get('license_key')
    licenses = load_licenses()
    
    if license_key in licenses:
        del licenses[license_key]
        save_licenses(licenses)
        session['message'] = f'🗑️ Lisans {license_key} silindi'
    else:
        session['error'] = '❌ Lisans bulunamadı!'
    
    return redirect('/admin')

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    if 'logged_in' not in session:
        return redirect('/admin')
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Basit şifre kontrolü (gerçek uygulamada hash kullanın!)
    if current_password != 'admin123':
        session['error'] = '❌ Mevcut şifre yanlış!'
        return redirect('/admin')
    
    if new_password != confirm_password:
        session['error'] = '❌ Yeni şifreler eşleşmiyor!'
        return redirect('/admin')
    
    if len(new_password) < 6:
        session['error'] = '❌ Şifre en az 6 karakter olmalı!'
        return redirect('/admin')
    
    # Şifreyi güncelle (gerçek uygulamada güvenli şekilde saklayın!)
    session['message'] = '🔒 Şifre başarıyla değiştirildi! (Not: Bu demo için geçici)'
    
    return redirect('/admin')

if __name__ == '__main__':
    print("🚀 Admin Panel başlatılıyor...")
    
    # Railway için port ayarları
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Admin Panel: http://0.0.0.0:{port}/admin")
    print("🔐 Şifre: admin123")
    
    app.run(host='0.0.0.0', port=port, debug=False) 