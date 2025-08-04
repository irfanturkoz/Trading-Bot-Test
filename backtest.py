#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRYPTO SIGNAL BOT BACKTEST MODULE
==================================

Bu modül, kripto sinyal botu için kapsamlı backtest fonksiyonları sağlar.
Geçmiş verileri analiz eder, formasyon tespiti yapar ve performans metrikleri hesaplar.

Author: Trading Bot Team
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import requests
import time
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Local imports
from data_fetcher import fetch_ohlcv
from formation_detector import (
    find_all_tobo, find_all_obo, detect_falling_wedge, 
    calculate_fibonacci_levels, calculate_macd, calculate_bollinger_bands, 
    calculate_stochastic, calculate_adx, detect_cup_and_handle
)
from botanlik import calculate_optimal_risk, optimize_tp_sl_fixed, format_price

# Türkçe karakter desteği için
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
sns.set_style("whitegrid")


class BacktestResult:
    """Backtest sonuçlarını saklayan sınıf"""
    
    def __init__(self):
        self.signals = []
        self.total_signals = 0
        self.successful_tp1 = 0
        self.successful_tp2 = 0
        self.successful_tp3 = 0
        self.hit_sl = 0
        self.total_rr = 0.0
        self.avg_rr = 0.0
        
    def add_signal(self, signal_data: Dict):
        """Yeni sinyal ekle"""
        self.signals.append(signal_data)
        self.total_signals += 1
        
        # Başarılı TP'leri say
        if signal_data.get('tp1_hit', False):
            self.successful_tp1 += 1
        if signal_data.get('tp2_hit', False):
            self.successful_tp2 += 1
        if signal_data.get('tp3_hit', False):
            self.successful_tp3 += 1
        if signal_data.get('sl_hit', False):
            self.hit_sl += 1
            
        # R/R oranını ekle
        if signal_data.get('rr_ratio'):
            self.total_rr += signal_data['rr_ratio']
    
    def calculate_metrics(self):
        """Metrikleri hesapla"""
        if self.total_signals > 0:
            self.avg_rr = self.total_rr / self.total_signals
            self.tp1_success_rate = (self.successful_tp1 / self.total_signals) * 100
            self.tp2_success_rate = (self.successful_tp2 / self.total_signals) * 100
            self.tp3_success_rate = (self.successful_tp3 / self.total_signals) * 100
            self.sl_hit_rate = (self.hit_sl / self.total_signals) * 100
        else:
            self.avg_rr = 0
            self.tp1_success_rate = 0
            self.tp2_success_rate = 0
            self.tp3_success_rate = 0
            self.sl_hit_rate = 0


def get_historical_data(symbol: str, interval: str = '1h', limit: int = 1000) -> pd.DataFrame:
    """
    Binance API'den geçmiş veri çeker
    
    Args:
        symbol (str): Sembol adı
        interval (str): Zaman dilimi (1h, 4h, 1d)
        limit (int): Kaç mum alınacak
        
    Returns:
        pd.DataFrame: OHLCV verisi
    """
    try:
        # Binance API endpoint
        url = f"https://fapi.binance.com/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # DataFrame'e çevir
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Veri tiplerini düzelt
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # open_time sütununu ekle (formation_detector için gerekli)
        df['open_time'] = df.index
        
        return df
        
    except Exception as e:
        print(f"❌ {symbol} geçmiş veri alınamadı: {e}")
        return pd.DataFrame()


def detect_formations_on_dataframe(df: pd.DataFrame) -> List[Dict]:
    """
    DataFrame üzerinde formasyon tespiti yapar
    
    Args:
        df (pd.DataFrame): OHLCV verisi
        
    Returns:
        List[Dict]: Tespit edilen formasyonlar
    """
    formations = []
    
    try:
        # TOBO formasyonları
        tobo_formations = find_all_tobo(df)
        if tobo_formations:
            for formation in tobo_formations:
                if formation:
                    # Basit skor hesaplama
                    formation['type'] = 'TOBO'
                    formation['direction'] = 'Long'
                    formation['score'] = 60  # Sabit skor
                    formations.append(formation)
        
        # OBO formasyonları
        obo_formations = find_all_obo(df)
        if obo_formations:
            for formation in obo_formations:
                if formation:
                    formation['type'] = 'OBO'
                    formation['direction'] = 'Short'
                    formation['score'] = 55  # Sabit skor
                    formations.append(formation)
        
        # Cup & Handle formasyonları
        cup_handle_formations = detect_cup_and_handle(df)
        if cup_handle_formations:
            for formation in cup_handle_formations:
                if formation:
                    formation['type'] = 'CUP_HANDLE'
                    formation['direction'] = 'Long'
                    formation['score'] = 65  # Sabit skor
                    formations.append(formation)
        
        # Falling Wedge formasyonları
        falling_wedge_formations = detect_falling_wedge(df)
        if falling_wedge_formations:
            for formation in falling_wedge_formations:
                if formation:
                    formation['type'] = 'FALLING_WEDGE'
                    formation['direction'] = 'Long'
                    formation['score'] = 50  # Sabit skor
                    formations.append(formation)
                    
    except Exception as e:
        print(f"❌ Formasyon tespiti hatası: {e}")
    
    return formations


def calculate_tp_levels(entry_price: float, direction: str, fibo_levels: Dict) -> Tuple[float, float, float]:
    """
    TP seviyelerini hesaplar
    
    Args:
        entry_price (float): Giriş fiyatı
        direction (str): 'Long' veya 'Short'
        fibo_levels (Dict): Fibonacci seviyeleri
        
    Returns:
        Tuple[float, float, float]: TP1, TP2, TP3
    """
    if direction == 'Long':
        # Long pozisyon için TP seviyeleri
        tp1 = entry_price * 1.01  # %1
        tp2 = entry_price * 1.02  # %2
        tp3 = entry_price * 1.03  # %3
        
        # Fibonacci seviyelerini kullan
        if fibo_levels:
            if '0.236' in fibo_levels and fibo_levels['0.236'] > entry_price:
                tp1 = fibo_levels['0.236']
            if '0.382' in fibo_levels and fibo_levels['0.382'] > entry_price:
                tp2 = fibo_levels['0.382']
            if '0.5' in fibo_levels and fibo_levels['0.5'] > entry_price:
                tp3 = fibo_levels['0.5']
    else:
        # Short pozisyon için TP seviyeleri
        tp1 = entry_price * 0.99  # %1
        tp2 = entry_price * 0.98  # %2
        tp3 = entry_price * 0.97  # %3
        
        # Fibonacci seviyelerini kullan
        if fibo_levels:
            if '0.236' in fibo_levels and fibo_levels['0.236'] < entry_price:
                tp1 = fibo_levels['0.236']
            if '0.382' in fibo_levels and fibo_levels['0.382'] < entry_price:
                tp2 = fibo_levels['0.382']
            if '0.5' in fibo_levels and fibo_levels['0.5'] < entry_price:
                tp3 = fibo_levels['0.5']
    
    return tp1, tp2, tp3


def check_target_hits(df: pd.DataFrame, signal_index: int, tp1: float, tp2: float, tp3: float, 
                     sl: float, direction: str) -> Dict:
    """
    Hedeflere ulaşılıp ulaşılmadığını kontrol eder
    
    Args:
        df (pd.DataFrame): OHLCV verisi
        signal_index (int): Sinyal mumunun indeksi
        tp1, tp2, tp3 (float): Take Profit seviyeleri
        sl (float): Stop Loss seviyesi
        direction (str): 'Long' veya 'Short'
        
    Returns:
        Dict: Hedef sonuçları
    """
    # Sinyal sonrası mumları al
    future_data = df.iloc[signal_index+1:]
    
    if future_data.empty:
        return {
            'tp1_hit': False, 'tp2_hit': False, 'tp3_hit': False, 'sl_hit': False,
            'exit_price': None, 'exit_reason': 'Veri yetersiz'
        }
    
    tp1_hit = False
    tp2_hit = False
    tp3_hit = False
    sl_hit = False
    exit_price = None
    exit_reason = 'Hedef ulaşılmadı'
    
    for idx, row in future_data.iterrows():
        high = row['high']
        low = row['low']
        
        if direction == 'Long':
            # Long pozisyon için kontrol
            if high >= tp3 and not tp3_hit:
                tp3_hit = True
                exit_price = tp3
                exit_reason = 'TP3'
            elif high >= tp2 and not tp2_hit:
                tp2_hit = True
                exit_price = tp2
                exit_reason = 'TP2'
            elif high >= tp1 and not tp1_hit:
                tp1_hit = True
                exit_price = tp1
                exit_reason = 'TP1'
            elif low <= sl:
                sl_hit = True
                exit_price = sl
                exit_reason = 'SL'
                break
        else:
            # Short pozisyon için kontrol
            if low <= tp3 and not tp3_hit:
                tp3_hit = True
                exit_price = tp3
                exit_reason = 'TP3'
            elif low <= tp2 and not tp2_hit:
                tp2_hit = True
                exit_price = tp2
                exit_reason = 'TP2'
            elif low <= tp1 and not tp1_hit:
                tp1_hit = True
                exit_price = tp1
                exit_reason = 'TP1'
            elif high >= sl:
                sl_hit = True
                exit_price = sl
                exit_reason = 'SL'
                break
    
    return {
        'tp1_hit': tp1_hit,
        'tp2_hit': tp2_hit,
        'tp3_hit': tp3_hit,
        'sl_hit': sl_hit,
        'exit_price': exit_price,
        'exit_reason': exit_reason
    }


def run_backtest(symbol: str, interval: str = '1h', days: int = 30) -> BacktestResult:
    """
    Ana backtest fonksiyonu
    
    Args:
        symbol (str): Sembol adı
        interval (str): Zaman dilimi
        days (int): Kaç günlük veri analiz edilecek
        
    Returns:
        BacktestResult: Backtest sonuçları
    """
    print(f"🔍 {symbol} backtest başlatılıyor...")
    print(f"📊 Zaman dilimi: {interval}")
    print(f"📅 Analiz süresi: {days} gün")
    
    # Geçmiş veriyi al
    df = get_historical_data(symbol, interval, limit=days*24)  # 1 saatlik için
    
    if df.empty:
        print("❌ Veri alınamadı!")
        return BacktestResult()
    
    print(f"✅ {len(df)} mum verisi alındı")
    
    result = BacktestResult()
    
    # Her 100 mumda bir formasyon tespiti yap (daha büyük parçalar)
    step_size = 100
    
    for i in range(0, len(df) - step_size, step_size):
        # Mevcut veri parçasını al
        current_df = df.iloc[i:i+step_size].copy()
        
        # Minimum veri kontrolü
        if len(current_df) < 50:
            continue
            
        # Formasyon tespiti yap
        try:
            formations = detect_formations_on_dataframe(current_df)
            print(f"🔍 {i//step_size + 1}. parça: {len(formations)} formasyon bulundu")
        except Exception as e:
            print(f"❌ {i//step_size + 1}. parça formasyon hatası: {e}")
            continue
        
        for formation in formations:
            if not formation or 'score' not in formation:
                continue
            
            # Debug: Formasyon skorunu yazdır
            print(f"   📊 {formation.get('type', 'Unknown')}: Skor {formation['score']}")
            
            # Sinyal kalitesi kontrolü - çok düşük eşik
            if formation['score'] < 10:  # Eşiği çok düşürdük
                continue
            
            # Giriş fiyatı (son mumun kapanış fiyatı)
            entry_price = current_df['close'].iloc[-1]
            direction = formation.get('direction', 'Long')
            
            # Fibonacci seviyelerini hesapla
            fibo_levels = calculate_fibonacci_levels(current_df)
            
            # TP seviyelerini hesapla
            tp1, tp2, tp3 = calculate_tp_levels(entry_price, direction, fibo_levels)
            
            # SL seviyesini hesapla
            if direction == 'Long':
                sl = entry_price * 0.98  # %2 stop loss
            else:
                sl = entry_price * 1.02  # %2 stop loss
            
            # R/R oranını hesapla
            if direction == 'Long':
                rr_ratio = (tp1 - entry_price) / (entry_price - sl)
            else:
                rr_ratio = (entry_price - tp1) / (sl - entry_price)
            
            # Hedeflere ulaşılıp ulaşılmadığını kontrol et
            target_results = check_target_hits(df, i + step_size - 1, tp1, tp2, tp3, sl, direction)
            
            # Sinyal verilerini hazırla
            signal_data = {
                'timestamp': current_df.index[-1],
                'symbol': symbol,
                'formation_type': formation['type'],
                'direction': direction,
                'entry_price': entry_price,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'sl': sl,
                'rr_ratio': rr_ratio,
                'formation_score': formation['score'],
                **target_results
            }
            
            result.add_signal(signal_data)
    
    # Metrikleri hesapla
    result.calculate_metrics()
    
    print(f"✅ Backtest tamamlandı!")
    print(f"📈 Toplam sinyal: {result.total_signals}")
    print(f"🎯 TP1 başarı oranı: {result.tp1_success_rate:.1f}%")
    print(f"🎯 TP2 başarı oranı: {result.tp2_success_rate:.1f}%")
    print(f"🎯 TP3 başarı oranı: {result.tp3_success_rate:.1f}%")
    print(f"🛑 SL vurma oranı: {result.sl_hit_rate:.1f}%")
    print(f"📊 Ortalama R/R: {result.avg_rr:.2f}")
    
    return result


def create_visualizations(result: BacktestResult, symbol: str):
    """
    Backtest sonuçlarını görselleştirir
    
    Args:
        result (BacktestResult): Backtest sonuçları
        symbol (str): Sembol adı
    """
    if result.total_signals == 0:
        print("❌ Görselleştirme için yeterli veri yok!")
        return
    
    try:
        # Matplotlib backend ayarı
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        
        # Figure boyutunu ayarla
        plt.figure(figsize=(15, 10))
        
        # 1. Başarı oranları (Bar chart)
        plt.subplot(2, 2, 1)
        success_rates = [
            result.tp1_success_rate,
            result.tp2_success_rate,
            result.tp3_success_rate,
            result.sl_hit_rate
        ]
        labels = ['TP1', 'TP2', 'TP3', 'SL']
        colors = ['#2ecc71', '#27ae60', '#16a085', '#e74c3c']
        
        bars = plt.bar(labels, success_rates, color=colors, alpha=0.7)
        plt.title(f'{symbol} - Hedef Başarı Oranları', fontsize=14, fontweight='bold')
        plt.ylabel('Başarı Oranı (%)')
        plt.ylim(0, 100)
        
        # Bar üzerine değerleri yaz
        for bar, rate in zip(bars, success_rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 2. Sinyal dağılımı (Pie chart)
        plt.subplot(2, 2, 2)
        formation_types = {}
        for signal in result.signals:
            formation_type = signal['formation_type']
            formation_types[formation_type] = formation_types.get(formation_type, 0) + 1
        
        if formation_types:
            plt.pie(formation_types.values(), labels=formation_types.keys(), autopct='%1.1f%%',
                    startangle=90, colors=plt.cm.Set3(np.linspace(0, 1, len(formation_types))))
            plt.title('Formasyon Dağılımı', fontsize=14, fontweight='bold')
        
        # 3. R/R dağılımı (Histogram)
        plt.subplot(2, 2, 3)
        rr_values = [signal['rr_ratio'] for signal in result.signals if signal['rr_ratio'] > 0]
        if rr_values:
            plt.hist(rr_values, bins=20, color='#3498db', alpha=0.7, edgecolor='black')
            plt.title('R/R Oranı Dağılımı', fontsize=14, fontweight='bold')
            plt.xlabel('R/R Oranı')
            plt.ylabel('Frekans')
            plt.axvline(result.avg_rr, color='red', linestyle='--', 
                       label=f'Ortalama: {result.avg_rr:.2f}')
            plt.legend()
        
        # 4. Zaman serisi (Line chart)
        plt.subplot(2, 2, 4)
        if result.signals:
            dates = [signal['timestamp'] for signal in result.signals]
            scores = [signal['formation_score'] for signal in result.signals]
            
            plt.plot(dates, scores, marker='o', linestyle='-', color='#9b59b6', alpha=0.7)
            plt.title('Formasyon Skorları Zaman Serisi', fontsize=14, fontweight='bold')
            plt.xlabel('Tarih')
            plt.ylabel('Formasyon Skoru')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'backtest_results_{symbol}.png', dpi=300, bbox_inches='tight')
        print(f"✅ Görselleştirme kaydedildi: backtest_results_{symbol}.png")
        plt.close()  # Figure'ı kapat
        
    except Exception as e:
        print(f"❌ Görselleştirme hatası: {e}")
        print("📊 Sonuçlar sadece konsola yazdırıldı.")


def print_detailed_results(result: BacktestResult, symbol: str):
    """
    Detaylı sonuçları yazdırır
    
    Args:
        result (BacktestResult): Backtest sonuçları
        symbol (str): Sembol adı
    """
    print(f"\n{'='*60}")
    print(f"📊 {symbol} DETAYLI BACKTEST SONUÇLARI")
    print(f"{'='*60}")
    
    print(f"🔍 Toplam Sinyal: {result.total_signals}")
    print(f"📈 Başarılı TP1: {result.successful_tp1} ({result.tp1_success_rate:.1f}%)")
    print(f"📈 Başarılı TP2: {result.successful_tp2} ({result.tp2_success_rate:.1f}%)")
    print(f"📈 Başarılı TP3: {result.successful_tp3} ({result.tp3_success_rate:.1f}%)")
    print(f"🛑 SL Vurma: {result.hit_sl} ({result.sl_hit_rate:.1f}%)")
    print(f"📊 Ortalama R/R: {result.avg_rr:.2f}")
    
    print(f"\n📋 SON 10 SİNYAL:")
    print(f"{'Tarih':<20} {'Formasyon':<15} {'Yön':<6} {'Giriş':<10} {'TP1':<8} {'TP2':<8} {'TP3':<8} {'SL':<8} {'Sonuç':<10}")
    print("-" * 100)
    
    for signal in result.signals[-10:]:
        date_str = signal['timestamp'].strftime('%Y-%m-%d %H:%M')
        formation = signal['formation_type']
        direction = signal['direction']
        entry = format_price(signal['entry_price'])
        tp1_status = "✓" if signal['tp1_hit'] else "✗"
        tp2_status = "✓" if signal['tp2_hit'] else "✗"
        tp3_status = "✓" if signal['tp3_hit'] else "✗"
        sl_status = "✓" if signal['sl_hit'] else "✗"
        result_str = signal['exit_reason']
        
        print(f"{date_str:<20} {formation:<15} {direction:<6} {entry:<10} {tp1_status:<8} {tp2_status:<8} {tp3_status:<8} {sl_status:<8} {result_str:<10}")


def main():
    """
    Ana fonksiyon
    """
    print("🚀 Crypto Signal Bot Backtest Başlatılıyor...")
    print("=" * 60)
    
    # Test parametreleri
    symbol = "BTCUSDT"
    interval = "1h"
    days = 14  # Daha fazla veri test için
    
    # Backtest çalıştır
    result = run_backtest(symbol, interval, days)
    
    if result.total_signals > 0:
        # Detaylı sonuçları yazdır
        print_detailed_results(result, symbol)
        
        # Görselleştirme oluştur
        create_visualizations(result, symbol)
        
        print(f"\n✅ Backtest tamamlandı! Sonuçlar 'backtest_results_{symbol}.png' dosyasına kaydedildi.")
    else:
        print("❌ Backtest sonucu bulunamadı!")


if __name__ == "__main__":
    main() 