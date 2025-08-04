#!/usr/bin/env python3
"""
Test script for signal_visualizer.py
"""

import os
import sys
import time

print("🔍 Signal Visualizer Test Başlatılıyor...")

try:
    from signal_visualizer import visualize_single_formation
    print("✅ signal_visualizer import başarılı")
except Exception as e:
    print(f"❌ signal_visualizer import hatası: {e}")
    sys.exit(1)

# Test verisi oluştur
test_formation_data = {
    'symbol': 'BTCUSDT',
    'direction': 'Long',
    'formation': 'Cup & Handle',
    'entry_price': 45000.0,
    'tp_levels': {
        'tp1': 47250.0,
        'tp2': 49500.0,
        'tp3': 51750.0
    },
    'sl_price': 42750.0,
    'quality_score': 85,
    'signal_strength': 75,
    'rr_ratio': 1.5
}

print("📊 Test verisi hazırlandı")
print(f"🔍 Symbol: {test_formation_data['symbol']}")
print(f"🔍 Direction: {test_formation_data['direction']}")
print(f"🔍 Formation: {test_formation_data['formation']}")

try:
    print("🎨 Görselleştirme başlatılıyor...")
    chart_path = visualize_single_formation(test_formation_data)
    
    if chart_path and os.path.exists(chart_path):
        print(f"✅ Grafik oluşturuldu: {chart_path}")
        print(f"📁 Dosya boyutu: {os.path.getsize(chart_path)} bytes")
        
        # Dosyayı sil
        os.remove(chart_path)
        print(f"🗑️ Test grafiği silindi")
        
        print("🎯 TEST BAŞARILI!")
    else:
        print(f"❌ Grafik oluşturulamadı")
        print(f"📁 Chart path: {chart_path}")
        print(f"📁 Dosya var mı: {os.path.exists(chart_path) if chart_path else 'None'}")
        
except Exception as e:
    print(f"❌ Görselleştirme hatası: {e}")
    import traceback
    print(f"🔍 Detaylı hata: {traceback.format_exc()}")

print("�� Test tamamlandı!") 