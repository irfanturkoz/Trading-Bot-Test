#!/usr/bin/env python3
"""
Botanlik - Kripto Sinyal Botu
Gelişmiş formasyon tespiti ve risk yönetimi
"""

import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '7977984015')

# Import modules
from formation_detector import (
    detect_tobo, detect_obo, detect_cup_and_handle, 
    detect_falling_wedge, detect_bullish_bearish_flag,
    filter_high_quality_formations, analyze_multiple_timeframes,
    detect_inverse_head_and_shoulders, detect_head_and_shoulders  # Yeni gelişmiş fonksiyonlar
)
from data_fetcher import fetch_ohlcv
from signal_visualizer import SignalVisualizer
from telegram_notifier import send_telegram_message
from utils import format_price
from advanced_formation_analyzer import AdvancedFormationAnalyzer
from tp_sl_calculator import calculate_strict_tp_sl, format_signal_levels

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def get_usdt_symbols():
    """
    Binance Futures'tan USDT çiftlerini çeker
    
    Returns:
        list: USDT sembol listesi
    """
    try:
        url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
        response = requests.get(url, timeout=10)
        data = response.json()
        symbols = [s['symbol'] for s in data['symbols'] 
                  if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
        return symbols
    except Exception as e:
        print(f"❌ Sembol listesi alınamadı: {e}")
        return []

def get_current_price(symbol):
    """
    Sembolün anlık fiyatını çeker
    
    Args:
        symbol (str): Sembol adı
        
    Returns:
        float: Anlık fiyat veya None
    """
    try:
        url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price']) if 'price' in data else None
    except Exception as e:
        print(f"❌ {symbol} fiyatı alınamadı: {e}")
        return None

# ============================================================================
# RISK MANAGEMENT FUNCTIONS
# ============================================================================

def calculate_optimal_risk(symbol, current_price, tp, sl, direction):
    """
    ISOLATED işlemler için sabit 5x kaldıraç ile risk seviyesini hesaplar
    
    Args:
        symbol (str): Sembol adı
        current_price (float): Mevcut fiyat
        tp (float): Take Profit seviyesi
        sl (float): Stop Loss seviyesi
        direction (str): 'Long' veya 'Short'
        
    Returns:
        dict: Risk hesaplama sonuçları
    """
    if direction == 'Long':
        if current_price <= sl or tp <= current_price:
            return {
                'risk_level': 'Geçersiz',
                'leverage': '5x',
                'position_size': 'Kasanın %5\'i',
                'risk_reward': '0.0:1',
                'potential_gain': '%0.0',
                'margin_type': 'ISOLATED',
                'risk_amount': '%0.0',
                'max_loss': '%0.0'
            }
        risk_percent = (current_price - sl) / current_price
        reward_percent = (tp - current_price) / current_price
    else:
        if current_price >= sl or tp >= current_price:
            return {
                'risk_level': 'Geçersiz',
                'leverage': '5x',
                'position_size': 'Kasanın %5\'i',
                'risk_reward': '0.0:1',
                'potential_gain': '%0.0',
                'margin_type': 'ISOLATED',
                'risk_amount': '%0.0',
                'max_loss': '%0.0'
            }
        risk_percent = (sl - current_price) / current_price
        reward_percent = (current_price - tp) / current_price
    
    risk_reward_ratio = reward_percent / risk_percent if risk_percent > 0 else 0
    
    return {
        'risk_level': 'Sabit 5x',
        'leverage': '5x',
        'position_size': 'Kasanın %5\'i',
        'risk_reward': f'{risk_reward_ratio:.1f}:1',
        'potential_gain': f'%{reward_percent*5*100:.1f}',
        'margin_type': 'ISOLATED',
        'risk_amount': f'%{risk_percent*5*100:.1f}',
        'max_loss': f'%{risk_percent*5*100:.1f}'
    }

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_symbol(symbol, interval='4h', debug_mode=False):
    """
    Tek sembol için formasyon analizi yapar
    
    Args:
        symbol (str): Sembol adı
        interval (str): Zaman dilimi
        debug_mode (bool): Debug modu
        
    Returns:
        dict: Analiz sonuçları
    """
    try:
        if debug_mode:
            print(f"🔍 {symbol} analizi başlatılıyor...")
        
        # Veri çek
        df = fetch_ohlcv(symbol, interval)
        if df is None or len(df) < 100:
            if debug_mode:
                print(f"❌ {symbol} için yeterli veri yok")
            return None
        
        if debug_mode:
            print(f"✅ {symbol} verisi alındı ({len(df)} mum)")
        
        # Tüm formasyonları tespit et
        formations = []
        
        # GELİŞMİŞ TOBO tespiti (Yeni 5.0 kuralları)
        tobo_result = detect_inverse_head_and_shoulders(df, window=30)
        if tobo_result:
            formations.append(tobo_result)
            if debug_mode:
                print(f"📊 Gelişmiş TOBO tespit edildi: {tobo_result.get('quality_score', 'N/A')}/400")
        
        # GELİŞMİŞ OBO tespiti (Yeni 5.0 kuralları)
        obo_result = detect_head_and_shoulders(df, window=30)
        if obo_result:
            formations.append(obo_result)
            if debug_mode:
                print(f"📊 Gelişmiş OBO tespit edildi: {obo_result.get('quality_score', 'N/A')}/400")
        
        # Eski formasyon tespitleri (yedek olarak)
        old_tobo_result = detect_tobo(df)
        if old_tobo_result:
            formations.append(old_tobo_result)
            if debug_mode:
                print(f"📊 Eski TOBO tespit edildi: {old_tobo_result.get('score', 'N/A')}")
        
        old_obo_result = detect_obo(df)
        if old_obo_result:
            formations.append(old_obo_result)
            if debug_mode:
                print(f"📊 Eski OBO tespit edildi: {old_obo_result.get('score', 'N/A')}")
        
        # Cup & Handle tespiti
        cup_handle_result = detect_cup_and_handle(df)
        if cup_handle_result:
            formations.append(cup_handle_result)
            if debug_mode:
                print(f"📊 Cup & Handle tespit edildi: {cup_handle_result.get('score', 'N/A')}")
        
        # Falling Wedge tespiti
        falling_wedge_result = detect_falling_wedge(df)
        if falling_wedge_result:
            formations.append(falling_wedge_result)
            if debug_mode:
                print(f"📊 Falling Wedge tespit edildi: {falling_wedge_result.get('score', 'N/A')}")
        
        # Bullish/Bearish Flag tespiti
        flag_result = detect_bullish_bearish_flag(df)
        if flag_result:
            formations.append(flag_result)
            if debug_mode:
                print(f"📊 Flag tespit edildi: {flag_result.get('score', 'N/A')}")
        
        if debug_mode:
            print(f"📊 Toplam {len(formations)} formasyon tespit edildi")
        
        # Kalite filtresi uygula
        strong_formations = filter_high_quality_formations(df, formations, debug_mode)
        
        if debug_mode:
            print(f"🎯 Güçlü formasyon sayısı: {len(strong_formations)}")
        
        # TÜM GÜÇLÜ FORMASYONLARI GÖRSELLEŞTİR
        if strong_formations:
            try:
                visualizer = SignalVisualizer()
                
                if debug_mode:
                    print(f"🎯 {len(strong_formations)} güçlü formasyon bulundu")
                
                # Tüm güçlü formasyonları görselleştir
                for i, formation in enumerate(strong_formations, 1):
                    formation_type = formation.get('type', 'UNKNOWN')
                    quality_score = formation.get('quality_score', 0)
                    
                    if debug_mode:
                        print(f"📊 {i}. Formasyon: {formation_type} (Skor: {quality_score})")
                    
                    # Her formasyonu ayrı ayrı görselleştir
                    visualizer.visualize_single_formation(symbol, interval, formation, debug_mode)
                        
            except Exception as e:
                print(f"❌ Görselleştirme hatası: {e}")
        
        return {
            'symbol': symbol,
            'interval': interval,
            'total_formations': len(formations),
            'strong_formations': len(strong_formations),
            'best_formation': strong_formations[0] if strong_formations else None
        }
        
    except Exception as e:
        print(f"❌ {symbol} analiz hatası: {e}")
        return None

def get_scan_results(symbols=None, interval='4h', max_workers=5, debug_mode=False):
    """
    Çoklu sembol taraması yapar
    
    Args:
        symbols (list): Sembol listesi (None ise tüm USDT çiftleri)
        interval (str): Zaman dilimi
        max_workers (int): Maksimum thread sayısı
        debug_mode (bool): Debug modu
        
    Returns:
        dict: Tarama sonuçları
    """
    try:
        if symbols is None:
            symbols = get_usdt_symbols()
        
        if debug_mode:
            print(f"🔍 {len(symbols)} sembol taranacak...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(analyze_symbol, symbol, interval, debug_mode): symbol 
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result and result.get('strong_formations', 0) > 0:
                        results.append(result)
                        if debug_mode:
                            print(f"✅ {symbol}: {result['strong_formations']} güçlü formasyon")
                except Exception as e:
                    if debug_mode:
                        print(f"❌ {symbol} analiz hatası: {e}")
        
        if debug_mode:
            print(f"🎯 Tarama tamamlandı: {len(results)} sembolde güçlü formasyon bulundu")
        
        return results
        
    except Exception as e:
        print(f"❌ Tarama hatası: {e}")
        return []

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Ana fonksiyon - Bot çalıştırma
    """
    try:
        print("🚀 Botanlik Bot başlatılıyor...")

        # Gelişmiş formasyon analiz sistemi
        print("🔍 Gelişmiş formasyon analiz sistemi başlatılıyor...")
        analyzer = AdvancedFormationAnalyzer()
        
        # Tüm sembolleri tara
        print("📊 Tüm USDT sembolleri taranıyor...")
        scan_results = analyzer.scan_all_symbols(max_workers=3)  # Daha az worker

        if scan_results:
            print(f"✅ {len(scan_results)} yüksek kaliteli formasyon bulundu")

            # En iyi 3 formasyonu seç
            top_results = []
            for result in scan_results:
                if result.get('success') and result.get('best_formation'):
                    top_results.append(result)

            # Kalite skoruna göre sırala ve en iyi 3'ü al
            def get_quality_score(result):
                quality_score = result.get('quality_score', 0)
                if isinstance(quality_score, dict):
                    return quality_score.get('total_score', 0)
                return quality_score
            
            top_results.sort(key=get_quality_score, reverse=True)
            top_3_results = top_results[:3]

            if top_3_results:
                print(f"🎯 En iyi 3 formasyon seçildi:")
                for i, result in enumerate(top_3_results, 1):
                    symbol = result['symbol']
                    formation = result['best_formation']
                    quality_score = result.get('quality_score', 0)
                    if isinstance(quality_score, dict):
                        quality_score_int = quality_score.get('total_score', 0)
                    else:
                        quality_score_int = quality_score
                    rr_ratio = formation.get('rr_levels', {}).get('rr_ratio', 0)
                    
                    print(f"{i}. {symbol}: {formation['type']} (Skor: {quality_score_int}/400, R/R: {rr_ratio:.2f}:1)")
                
                # Her bir formasyon için görselleştirme ve Telegram gönderimi
                for i, result in enumerate(top_3_results, 1):
                    symbol = result['symbol']
                    formation = result['best_formation']
                    quality_score = result.get('quality_score', 0)
                    if isinstance(quality_score, dict):
                        quality_score_int = quality_score.get('total_score', 0)
                    else:
                        quality_score_int = quality_score
                    
                    print(f"\n📊 {i}. Sıra - {symbol} işleniyor...")
                    print(f"📊 Formasyon Tipi: {formation['type']}")
                    print(f"🎯 Kalite Skoru: {quality_score_int}/400")
                    print(f"📈 R/R Oranı: {formation.get('rr_levels', {}).get('rr_ratio', 0):.2f}:1")
                    
                    # Görselleştirme ve Telegram gönderimi
                    try:
                        visualizer = SignalVisualizer()
                        success = visualizer.visualize_single_formation(
                            symbol, '4h', formation, debug_mode=True
                        )
                        
                        if success:
                            print(f"✅ {symbol} sinyali başarıyla gönderildi!")
                        else:
                            print(f"❌ {symbol} görselleştirme hatası!")
                            
                    except Exception as e:
                        print(f"❌ {symbol} görselleştirme hatası: {e}")
                    
                    # Formasyonlar arası kısa bekleme
                    if i < len(top_3_results):
                        print("⏳ Sonraki formasyon için bekleniyor...")
                        time.sleep(2)  # 2 saniye bekle
            else:
                print("❌ Yüksek kaliteli formasyon bulunamadı")
        else:
            print("❌ Hiç formasyon bulunamadı")

    except Exception as e:
        print(f"❌ Ana fonksiyon hatası: {e}")

if __name__ == "__main__":
    main() 