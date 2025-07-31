import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from license_manager import LicenseManager
import random
import string

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Trading Bot Admin Panel",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    .license-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class AdminPanelWeb:
    def __init__(self):
        self.license_manager = LicenseManager()
        self.admin_password = "admin123"
        
    def generate_license_key(self, license_type, price):
        """Yeni lisans anahtarı oluşturur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if license_type == "monthly":
            prefix = "MONTHLY"
            duration = 30
        elif license_type == "quarterly":
            prefix = "QUARTERLY"
            duration = 90
        elif license_type == "unlimited":
            prefix = "UNLIMITED"
            duration = -1
        else:
            return None, "Geçersiz lisans tipi!"
        
        # Benzersiz anahtar oluştur
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        license_key = f"{prefix}_{timestamp}_{random_suffix}"
        
        # Lisans bilgilerini oluştur
        license_info = {
            "type": license_type,
            "duration": duration,
            "price": price,
            "features": self.get_features_by_type(license_type)
        }
        
        # Mevcut lisanslara ekle
        self.license_manager.valid_licenses[license_key] = license_info
        
        return license_key, license_info
    
    def get_features_by_type(self, license_type):
        """Lisans tipine göre özellikleri döndürür"""
        if license_type == "monthly":
            return ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi"]
        elif license_type == "quarterly":
            return ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek"]
        elif license_type == "unlimited":
            return ["Temel Tarama", "Telegram Bildirimleri", "Formasyon Analizi", "Öncelikli Destek", "Özel Formasyonlar", "7/24 Destek"]
        return []
    
    def save_licenses_to_file(self):
        """Lisansları dosyaya kaydeder"""
        try:
            with open("licenses.json", "w") as f:
                json.dump(self.license_manager.valid_licenses, f, indent=2)
            return True, "Lisanslar başarıyla kaydedildi!"
        except Exception as e:
            return False, f"Lisanslar kaydedilemedi: {e}"
    
    def load_licenses_from_file(self):
        """Lisansları dosyadan yükler"""
        try:
            if os.path.exists("licenses.json"):
                with open("licenses.json", "r") as f:
                    self.license_manager.valid_licenses = json.load(f)
                return True, "Lisanslar başarıyla yüklendi!"
        except Exception as e:
            return False, f"Lisanslar yüklenemedi: {e}"
        return False, "Lisans dosyası bulunamadı."

def main():
    # Ana başlık
    st.markdown('<h1 class="main-header">🤖 Trading Bot Admin Panel</h1>', unsafe_allow_html=True)
    
    # Sidebar - Giriş
    with st.sidebar:
        st.header("🔐 Giriş")
        password = st.text_input("Admin Şifresi", type="password")
        
        if st.button("Giriş Yap"):
            if password == "admin123":
                st.session_state.authenticated = True
                st.success("✅ Giriş başarılı!")
                st.rerun()
            else:
                st.error("❌ Yanlış şifre!")
    
    # Giriş kontrolü
    if not st.session_state.get('authenticated', False):
        st.warning("🔐 Lütfen sidebar'dan giriş yapın.")
        return
    
    # Admin paneli başlat
    admin = AdminPanelWeb()
    
    # Lisansları yükle
    if 'licenses_loaded' not in st.session_state:
        success, message = admin.load_licenses_from_file()
        if success:
            st.session_state.licenses_loaded = True
    
    # Ana dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_licenses = len(admin.license_manager.valid_licenses)
        st.metric("📦 Toplam Lisans", total_licenses)
    
    with col2:
        monthly_count = sum(1 for info in admin.license_manager.valid_licenses.values() if info['type'] == 'monthly')
        st.metric("📅 1 Aylık", monthly_count)
    
    with col3:
        quarterly_count = sum(1 for info in admin.license_manager.valid_licenses.values() if info['type'] == 'quarterly')
        st.metric("📅 3 Aylık", quarterly_count)
    
    with col4:
        unlimited_count = sum(1 for info in admin.license_manager.valid_licenses.values() if info['type'] == 'unlimited')
        st.metric("♾️ Sınırsız", unlimited_count)
    
    # Toplam gelir
    total_revenue = sum(info['price'] for info in admin.license_manager.valid_licenses.values())
    st.markdown(f"""
    <div class="metric-card success-card">
        <h3>💰 Toplam Gelir: ${total_revenue:,}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab'lar
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Yeni Lisans", "📋 Lisanslar", "⚙️ Ayarlar"])
    
    with tab1:
        st.header("📊 Dashboard")
        
        # Grafikler
        col1, col2 = st.columns(2)
        
        with col1:
            # Paket dağılımı
            license_types = {
                '1 Aylık': monthly_count,
                '3 Aylık': quarterly_count,
                'Sınırsız': unlimited_count
            }
            
            if sum(license_types.values()) > 0:
                fig_pie = px.pie(
                    values=list(license_types.values()),
                    names=list(license_types.keys()),
                    title="📦 Paket Dağılımı",
                    color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Gelir dağılımı
            revenue_by_type = {
                '1 Aylık': monthly_count * 200,
                '3 Aylık': quarterly_count * 500,
                'Sınırsız': unlimited_count * 1500
            }
            
            if sum(revenue_by_type.values()) > 0:
                fig_bar = px.bar(
                    x=list(revenue_by_type.keys()),
                    y=list(revenue_by_type.values()),
                    title="💰 Gelir Dağılımı",
                    color=list(revenue_by_type.values()),
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Son aktiviteler
        st.subheader("🕒 Son Aktiviteler")
        st.info("Bu bölüm gerçek zamanlı aktiviteleri gösterecek.")
    
    with tab2:
        st.header("➕ Yeni Lisans Oluştur")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 Paket Seçimi")
            
            package_type = st.selectbox(
                "Lisans Tipi",
                ["monthly", "quarterly", "unlimited"],
                format_func=lambda x: {
                    "monthly": "1 Aylık - $200",
                    "quarterly": "3 Aylık - $500",
                    "unlimited": "Sınırsız - $1500"
                }[x]
            )
            
            # Paket özelliklerini göster
            features = admin.get_features_by_type(package_type)
            st.subheader("✅ Özellikler")
            for feature in features:
                st.write(f"• {feature}")
        
        with col2:
            st.subheader("🔑 Lisans Oluştur")
            
            if st.button("🚀 Yeni Lisans Oluştur", type="primary"):
                price_map = {"monthly": 200, "quarterly": 500, "unlimited": 1500}
                license_key, license_info = admin.generate_license_key(package_type, price_map[package_type])
                
                if license_key:
                    st.success("✅ Yeni lisans oluşturuldu!")
                    
                    # Lisans bilgilerini göster
                    st.markdown(f"""
                    <div class="license-card">
                        <h4>🔑 Lisans Anahtarı</h4>
                        <code style="background-color: #f8f9fa; padding: 0.5rem; border-radius: 0.25rem; font-size: 1.1rem;">{license_key}</code>
                        <br><br>
                        <strong>📦 Paket:</strong> {license_info['type'].upper()}<br>
                        <strong>💰 Fiyat:</strong> ${license_info['price']}<br>
                        <strong>⏰ Süre:</strong> {license_info['duration']} gün" if license_info['duration'] != -1 else "Sınırsız"
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Kopyalama butonu
                    st.button("📋 Kopyala", on_click=lambda: st.write("Kopyalandı!"))
                    
                    # Lisansları kaydet
                    success, message = admin.save_licenses_to_file()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error(f"❌ Hata: {license_info}")
    
    with tab3:
        st.header("📋 Mevcut Lisanslar")
        
        # Arama ve filtreleme
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("🔍 Lisans Ara", placeholder="Anahtar kelime...")
        
        with col2:
            filter_type = st.selectbox("📦 Paket Filtresi", ["Tümü", "monthly", "quarterly", "unlimited"])
        
        # Lisansları listele
        licenses_data = []
        for key, info in admin.license_manager.valid_licenses.items():
            if search_term and search_term.lower() not in key.lower():
                continue
            if filter_type != "Tümü" and info['type'] != filter_type:
                continue
                
            licenses_data.append({
                "Anahtar": key,
                "Tip": info['type'].upper(),
                "Fiyat": f"${info['price']}",
                "Süre": f"{info['duration']} gün" if info['duration'] != -1 else "Sınırsız",
                "Özellikler": len(info['features'])
            })
        
        if licenses_data:
            df = pd.DataFrame(licenses_data)
            st.dataframe(df, use_container_width=True)
            
            # İstatistikler
            st.subheader("📊 Özet")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Toplam", len(licenses_data))
            
            with col2:
                total_price = sum(int(row['Fiyat'].replace('$', '')) for row in licenses_data)
                st.metric("Toplam Değer", f"${total_price:,}")
            
            with col3:
                avg_price = total_price / len(licenses_data) if licenses_data else 0
                st.metric("Ortalama Fiyat", f"${avg_price:.0f}")
        else:
            st.warning("🔍 Arama kriterlerine uygun lisans bulunamadı.")
    
    with tab4:
        st.header("⚙️ Ayarlar")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💾 Veri Yönetimi")
            
            if st.button("💾 Lisansları Kaydet"):
                success, message = admin.save_licenses_to_file()
                if success:
                    st.success(message)
                else:
                    st.error(message)
            
            if st.button("📂 Lisansları Yükle"):
                success, message = admin.load_licenses_from_file()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            st.subheader("🔐 Güvenlik")
            
            st.info("""
            **Güvenlik Önerileri:**
            - Admin şifresini düzenli değiştirin
            - Lisans dosyalarını yedekleyin
            - Güvenli sunucu kullanın
            """)
        
        # Sistem bilgileri
        st.subheader("ℹ️ Sistem Bilgileri")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Python Sürümü", "3.8+")
        
        with col2:
            st.metric("Streamlit Sürümü", "1.28+")
        
        with col3:
            st.metric("Son Güncelleme", datetime.now().strftime("%d.%m.%Y"))
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        🤖 Trading Bot Admin Panel | 💬 İletişim: @tgtradingbot
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 