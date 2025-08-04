#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGNAL VISUALIZER MODULE
========================

Bu modül, tespit edilen formasyonları görselleştirir ve Telegram'a gönderir.
Formasyon çizgileri, giriş noktaları, TP/SL seviyeleri otomatik olarak çizilir.

Author: Trading Bot Team
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Matplotlib font ayarları - Railway için
import matplotlib
matplotlib.use('Agg')  # GUI olmadan çalış
plt.rcParams['font.family'] = 'DejaVu Sans'  # Linux'ta mevcut font
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False

# Local imports
from data_fetcher import fetch_ohlcv
from formation_detector import (
    find_all_tobo, find_all_obo, detect_falling_wedge, 
    calculate_fibonacci_levels, detect_cup_and_handle, is_falling_wedge,
    detect_bullish_bearish_flag, filter_high_quality_formations,
    detect_inverse_head_and_shoulders, detect_head_and_shoulders  # Yeni gelişmiş fonksiyonlar
)
from utils import format_price
from telegram_notifier import send_telegram_message

# Matplotlib ayarları
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.style.use('dark_background')


class SignalVisualizer:
    """Sinyal görselleştirme sınıfı"""
    
    def __init__(self):
        self.colors = {
            'candle_up': '#00ff88',
            'candle_down': '#ff4444',
            'formation_line': '#ffaa00',
            'entry_point': '#00ffff',
            'tp1': '#00ff00',
            'tp2': '#ffff00',
            'tp3': '#ff8800',
            'sl': '#ff0000',
            'volume': '#4444ff'
        }
    
    def get_formation_data(self, symbol: str, interval: str = '1h', limit: int = 200) -> pd.DataFrame:
        """
        Formasyon analizi için veri çeker
        
        Args:
            symbol (str): Sembol adı
            interval (str): Zaman dilimi
            limit (int): Kaç mum alınacak
            
        Returns:
            pd.DataFrame: OHLCV verisi
        """
        try:
            url = f"https://fapi.binance.com/fapi/v1/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['open_time'] = df.index
            
            return df
            
        except Exception as e:
            print(f"❌ {symbol} veri alınamadı: {e}")
            return pd.DataFrame()
    
    def find_formation_points(self, df: pd.DataFrame, formation_type: str, formation_data: Dict) -> Dict:
        """
        Formasyon çizgileri için noktaları bulur
        
        Args:
            df (pd.DataFrame): OHLCV verisi
            formation_type (str): Formasyon tipi
            formation_data (Dict): Formasyon verisi
            
        Returns:
            Dict: Çizgi noktaları
        """
        points = {}
        
        try:
            # Son 50 mumu al
            recent_data = df.tail(50)
            current_price = df['close'].iloc[-1]
            
            if formation_type == 'FALLING_WEDGE':
                # Falling Wedge için direnç ve destek çizgileri
                # Direnç çizgisi için yüksek noktalar
                highs = recent_data['high'].values
                high_indices = []
                
                # Yerel maksimumları bul
                for i in range(1, len(highs) - 1):
                    if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                        high_indices.append(i)
                
                if len(high_indices) >= 2:
                    # İlk iki yüksek nokta - numeric index kullan
                    points['resistance_x'] = [high_indices[0], high_indices[1]]
                    points['resistance_y'] = [highs[high_indices[0]], highs[high_indices[1]]]
                
                # Destek çizgisi için düşük noktalar
                lows = recent_data['low'].values
                low_indices = []
                
                for i in range(1, len(lows) - 1):
                    if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                        low_indices.append(i)
                
                if len(low_indices) >= 2:
                    points['support_x'] = [low_indices[0], low_indices[1]]
                    points['support_y'] = [lows[low_indices[0]], lows[low_indices[1]]]
            
            elif formation_type in ['TOBO', 'OBO']:
                # TOBO/OBO için boyun çizgisi - mevcut fiyatın %1 üstü/altı
                if formation_type == 'TOBO':
                    neckline_price = current_price * 1.01  # %1 üstü
                else:  # OBO
                    neckline_price = current_price * 0.99  # %1 altı
                
                points['neckline'] = {
                    'price': neckline_price,
                    'start': df.index[0],
                    'end': df.index[-1]
                }
                
                print(f"✅ {formation_type} boyun çizgisi: {format_price(neckline_price)}")
            
            elif formation_type == 'CUP_AND_HANDLE':
                # Cup and Handle için destek çizgisi
                support_price = recent_data['low'].min()
                points['support'] = {
                    'price': support_price,
                    'start': df.index[0],
                    'end': df.index[-1]
                }
            
            elif formation_type in ['BULLISH_FLAG', 'BEARISH_FLAG']:
                # Flag için bayrak direği ve kanal çizgileri
                # Bayrak direği (dikey çizgi)
                pole_start = recent_data.index[0]
                pole_end = recent_data.index[len(recent_data)//3]  # İlk 1/3'ü
                points['flag_pole'] = {
                    'start': pole_start,
                    'end': pole_end
                }
                
                # Kanal çizgileri (paralel çizgiler)
                channel_high = recent_data['high'].max()
                channel_low = recent_data['low'].min()
                points['flag_channel'] = {
                    'upper': channel_high,
                    'lower': channel_low,
                    'start': df.index[0],
                    'end': df.index[-1]
                }
            
            else:
                # Diğer formasyonlar için basit destek/direnç
                high_price = recent_data['high'].max()
                low_price = recent_data['low'].min()
                
                points['resistance'] = {
                    'price': high_price,
                    'start': df.index[0],
                    'end': df.index[-1]
                }
                points['support'] = {
                    'price': low_price,
                    'start': df.index[0],
                    'end': df.index[-1]
                }
                
        except Exception as e:
            print(f"❌ Formasyon noktaları bulunamadı: {e}")
        
        return points
    
    def calculate_target_levels(self, entry_price: float, direction: str, formation_data: Dict) -> Dict:
        """
        TP ve SL seviyelerini hesaplar - SON KURALLAR (SAPMA YOK):
        
        🔁 GENEL KURALLAR:
        - Giriş fiyatı ile SL ve TP oranlarını yönüne göre doğru hesapla:
          - Long işlemlerde: TP > Giriş > SL
          - Short işlemlerde: TP < Giriş < SL
        - Stop Loss (SL) seviyesi her zaman giriş fiyatının %3 uzağında olacak.
        - Risk/Ödül (R/R) oranı sadece TP1 ile SL arasındaki fark kullanılarak hesaplanacak.
        - TP1, TP2, TP3 sırasıyla giriş fiyatına göre %4.5 / %6.75 / %10.0 uzaklıkta olacak.
        - Yön: "Long" ise TP'ler giriş fiyatının üstünde, "Short" ise TP'ler girişin altında olacak.
        - TP seviyelerinin sıralaması yönle uyumlu olacak:
          - Long: TP1 < TP2 < TP3
          - Short: TP1 > TP2 > TP3
        
        ⛔ HATALI YAPILMAMASI GEREKENLER:
        - TP'ler long pozisyonda girişin altında olamaz.
        - TP'ler short pozisyonda girişin üstünde olamaz.
        - SL oranı asla %3 dışında olamaz.
        - TP'lerin sırası yönle ters olamaz.
        - R/R oranı yalnızca TP1 ile SL arasından hesaplanmalı.
        """
        levels = {}
        
        if direction == 'Long':
            # 🔼 LONG İŞLEM KURALLARI
            sl = entry_price * 0.97  # %3 altında (sabit)
            tp1 = entry_price * 1.045  # %4.5 yukarıda
            tp2 = entry_price * 1.0675 # %6.75 yukarıda
            tp3 = entry_price * 1.10   # %10.0 yukarıda
            
            print(f"🟢 LONG SİNYAL HESAPLAMASI:")
            print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
            print(f"🛑 SL: {format_price(sl)} (Girişin %3 altında)")
            print(f"🎯 TP1: {format_price(tp1)} (Girişin %4.5 üstünde)")
            print(f"🎯 TP2: {format_price(tp2)} (Girişin %6.75 üstünde)")
            print(f"🎯 TP3: {format_price(tp3)} (Girişin %10.0 üstünde)")
            
            # Güvenlik kontrolü: SL girişin altında olmalı (Long)
            if sl >= entry_price:
                print(f"🚨 HATA: SL ({format_price(sl)}) giriş fiyatının ({format_price(entry_price)}) üstünde! Düzeltiliyor...")
                sl = entry_price * 0.97
                print(f"✅ Düzeltildi: SL = {format_price(sl)}")
            
            # Güvenlik kontrolü: TP'ler girişin üstünde olmalı (Long)
            if tp1 <= entry_price:
                print(f"🚨 HATA: TP1 ({format_price(tp1)}) giriş fiyatının ({format_price(entry_price)}) altında! Düzeltiliyor...")
                tp1 = entry_price * 1.045
                tp2 = entry_price * 1.0675
                tp3 = entry_price * 1.10
                print(f"✅ Düzeltildi: TP1 = {format_price(tp1)}, TP2 = {format_price(tp2)}, TP3 = {format_price(tp3)}")
            
            # R/R oranı hesapla: (tp1 - entry) / (entry - sl) - SADECE TP1 VE SL
            rr_ratio = (tp1 - entry_price) / (entry_price - sl)
            print(f"📈 R/R Oranı: {rr_ratio:.2f}:1")
            
            levels = {
                'tp1': round(tp1, 6),
                'tp2': round(tp2, 6),
                'tp3': round(tp3, 6),
                'sl': round(sl, 6),
                'rr_ratio': round(rr_ratio, 2)
            }
            
        else:
            # 🔻 SHORT İŞLEM KURALLARI - DÜZELTİLDİ
            sl = entry_price * 1.03  # %3 üstünde (sabit)
            tp1 = entry_price * 0.955  # %4.5 aşağıda
            tp2 = entry_price * 0.9325 # %6.75 aşağıda
            tp3 = entry_price * 0.90   # %10.0 aşağıda
            
            print(f"🔻 SHORT SİNYAL HESAPLAMASI:")
            print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
            print(f"🛑 SL: {format_price(sl)} (Girişin %3 üstünde)")
            print(f"🎯 TP1: {format_price(tp1)} (Girişin %4.5 altında)")
            print(f"🎯 TP2: {format_price(tp2)} (Girişin %6.75 altında)")
            print(f"🎯 TP3: {format_price(tp3)} (Girişin %10.0 altında)")
            
            # Güvenlik kontrolü: SL girişin üstünde olmalı (Short)
            if sl <= entry_price:
                print(f"🚨 HATA: SL ({format_price(sl)}) giriş fiyatının ({format_price(entry_price)}) altında! Düzeltiliyor...")
                sl = entry_price * 1.03
                print(f"✅ Düzeltildi: SL = {format_price(sl)}")
            
            # Güvenlik kontrolü: TP'ler girişin altında olmalı (Short)
            if tp1 >= entry_price:
                print(f"🚨 HATA: TP1 ({format_price(tp1)}) giriş fiyatının ({format_price(entry_price)}) üstünde! Düzeltiliyor...")
                tp1 = entry_price * 0.955
                tp2 = entry_price * 0.9325
                tp3 = entry_price * 0.90
                print(f"✅ Düzeltildi: TP1 = {format_price(tp1)}, TP2 = {format_price(tp2)}, TP3 = {format_price(tp3)}")
            
            # R/R oranı hesapla: (entry - tp1) / (sl - entry) - SADECE TP1 VE SL
            rr_ratio = (entry_price - tp1) / (sl - entry_price)
            print(f"📈 R/R Oranı: {rr_ratio:.2f}:1")
            
            levels = {
                'tp1': round(tp1, 6),
                'tp2': round(tp2, 6),
                'tp3': round(tp3, 6),
                'sl': round(sl, 6),
                'rr_ratio': round(rr_ratio, 2)
            }
        
        return levels
    
    def create_candlestick_chart(self, df: pd.DataFrame, formation_type: str, 
                                formation_data: Dict, entry_price: float, 
                                direction: str, symbol: str) -> str:
        """
        Mum grafiği oluşturur ve formasyon çizgilerini ekler
        
        Args:
            df (pd.DataFrame): OHLCV verisi
            formation_type (str): Formasyon tipi
            formation_data (Dict): Formasyon verisi
            entry_price (float): Giriş fiyatı
            direction (str): 'Long' veya 'Short'
            symbol (str): Sembol adı
            
        Returns:
            str: Kaydedilen dosya yolu
        """
        try:
            # Son 100 mumu al
            chart_data = df.tail(100).copy()
            
            # mplfinance için veriyi hazırla
            chart_data.index.name = 'Date'
            
            # Manuel mum grafiği oluştur
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Mum grafiği çiz - Manuel profesyonel mumlar
            print(f"🔍 {len(chart_data)} mum çiziliyor...")
            
            # Mum genişliği - profesyonel kalınlık
            body_width = 0.6  # Profesyonel kalınlık
            
            for i, (timestamp, row) in enumerate(chart_data.iterrows()):
                open_price = row['open']
                close_price = row['close']
                high_price = row['high']
                low_price = row['low']
                
                # Mum rengi
                if close_price >= open_price:
                    color = self.colors['candle_up']  # Yeşil
                    body_bottom = open_price
                    body_top = close_price
                else:
                    color = self.colors['candle_down']  # Kırmızı
                    body_bottom = close_price
                    body_top = open_price
                
                # Fitil (dikey çizgi) - profesyonel kalınlık
                ax1.plot([i, i], [low_price, high_price], color='white', linewidth=1.5, alpha=1.0, solid_capstyle='round')
                
                # Mum gövdesi - profesyonel dikdörtgen
                body_left = i - body_width/2
                body_height = body_top - body_bottom
                
                # Minimum mum gövdesi yüksekliği
                price_range = high_price - low_price
                min_height = max(price_range * 0.7, price_range * 0.08)  # %70 minimum, ama en az %8
                
                if body_height < min_height:
                    body_height = min_height
                    body_center = (body_top + body_bottom) / 2
                    body_bottom = body_center - body_height / 2
                    body_top = body_center + body_height / 2
                
                # Gövde dikdörtgeni - profesyonel kalınlık
                rect = plt.Rectangle((body_left, body_bottom), body_width, body_height, 
                                   facecolor=color, edgecolor='white', linewidth=1.0, alpha=1.0)
                ax1.add_patch(rect)
            
            print(f"✅ Mumlar çizildi, formasyon çizgileri ekleniyor...")
            
            # Formasyon çizgilerini ekle
            formation_points = self.find_formation_points(df, formation_type, formation_data)
            
            if formation_type == 'FALLING_WEDGE':
                print(f"🔍 Falling Wedge formasyon çizgileri çiziliyor...")
                # Direnç çizgisi
                if 'resistance_x' in formation_points:
                    # İndeksleri chart_data'ya göre ayarla
                    resistance_x = formation_points['resistance_x']
                    resistance_y = formation_points['resistance_y']
                    
                    # Chart data'nın başlangıç indeksini bul
                    start_idx = len(df) - len(chart_data)
                    adjusted_resistance_x = [x - start_idx for x in resistance_x if x >= start_idx]
                    adjusted_resistance_y = [resistance_y[i] for i, x in enumerate(resistance_x) if x >= start_idx]
                    
                    print(f"📊 Direnç çizgisi noktaları: {adjusted_resistance_x}, {adjusted_resistance_y}")
                    
                    if len(adjusted_resistance_x) >= 2:
                        ax1.plot(adjusted_resistance_x, adjusted_resistance_y, 
                                color=self.colors['formation_line'], linewidth=2, linestyle='--', 
                                label='Direnç Çizgisi')
                        print(f"✅ Direnç çizgisi çizildi")
                
                # Destek çizgisi
                if 'support_x' in formation_points:
                    # İndeksleri chart_data'ya göre ayarla
                    support_x = formation_points['support_x']
                    support_y = formation_points['support_y']
                    
                    # Chart data'nın başlangıç indeksini bul
                    start_idx = len(df) - len(chart_data)
                    adjusted_support_x = [x - start_idx for x in support_x if x >= start_idx]
                    adjusted_support_y = [support_y[i] for i, x in enumerate(support_x) if x >= start_idx]
                    
                    print(f"📊 Destek çizgisi noktaları: {adjusted_support_x}, {adjusted_support_y}")
                    
                    if len(adjusted_support_x) >= 2:
                        ax1.plot(adjusted_support_x, adjusted_support_y, 
                                color=self.colors['formation_line'], linewidth=2, linestyle='--', 
                                label='Destek Çizgisi')
                        print(f"✅ Destek çizgisi çizildi")
            
            elif formation_type in ['TOBO', 'OBO']:
                # Boyun çizgisi
                if 'neckline' in formation_points:
                    neckline = formation_points['neckline']
                    ax1.axhline(y=neckline['price'], color=self.colors['formation_line'], 
                               linewidth=2, linestyle='--', label='Boyun Çizgisi')
                    print(f"✅ Boyun çizgisi çizildi: {format_price(neckline['price'])}")
            
            elif formation_type == 'CUP_AND_HANDLE':
                # Destek çizgisi
                if 'support' in formation_points:
                    support = formation_points['support']
                    ax1.axhline(y=support['price'], color=self.colors['formation_line'], 
                               linewidth=2, linestyle='--', label='Destek Çizgisi')
            
            elif formation_type in ['BULLISH_FLAG', 'BEARISH_FLAG']:
                # Flag için paralel çizgiler
                if 'flag_pole' in formation_points:
                    pole = formation_points['flag_pole']
                    ax1.axvline(x=pole['start'], color=self.colors['formation_line'], 
                               linewidth=2, linestyle='-', label='Bayrak Direği')
                
                if 'flag_channel' in formation_points:
                    channel = formation_points['flag_channel']
                    ax1.axhline(y=channel['upper'], color=self.colors['formation_line'], 
                               linewidth=1, linestyle='--', label='Üst Kanal')
                    ax1.axhline(y=channel['lower'], color=self.colors['formation_line'], 
                               linewidth=1, linestyle='--', label='Alt Kanal')
            
            else:
                # Diğer formasyonlar için destek/direnç çizgileri
                if 'resistance' in formation_points:
                    resistance = formation_points['resistance']
                    ax1.axhline(y=resistance['price'], color=self.colors['formation_line'], 
                               linewidth=2, linestyle='--', label='Direnç Çizgisi')
                
                if 'support' in formation_points:
                    support = formation_points['support']
                    ax1.axhline(y=support['price'], color=self.colors['formation_line'], 
                               linewidth=2, linestyle='--', label='Destek Çizgisi')
            
            # Giriş noktası
            entry_index = len(chart_data) - 1
            ax1.scatter(entry_index, entry_price, color=self.colors['entry_point'], 
                       s=100, marker='o', label='Giriş Noktası', zorder=5)
            
            # TP ve SL seviyeleri
            levels = self.calculate_target_levels(entry_price, direction, formation_data)
            
            # TP seviyeleri
            ax1.axhline(y=levels['tp1'], color=self.colors['tp1'], linewidth=1, 
                       linestyle=':', label=f'TP1: {format_price(levels["tp1"])}')
            ax1.axhline(y=levels['tp2'], color=self.colors['tp2'], linewidth=1, 
                       linestyle=':', label=f'TP2: {format_price(levels["tp2"])}')
            ax1.axhline(y=levels['tp3'], color=self.colors['tp3'], linewidth=1, 
                       linestyle=':', label=f'TP3: {format_price(levels["tp3"])}')
            
            # SL seviyesi
            ax1.axhline(y=levels['sl'], color=self.colors['sl'], linewidth=2, 
                       linestyle='-', label=f'SL: {format_price(levels["sl"])}')
            
            # Grafik ayarları
            ax1.set_title(f'{symbol} - {formation_type} Formasyonu', 
                         fontsize=16, fontweight='bold', color='white')
            ax1.set_ylabel('Fiyat (USDT)', color='white')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left', framealpha=0.8)
            
            # X ekseni ayarları
            ax1.set_xticks(range(0, len(chart_data), 20))
            ax1.set_xticklabels([chart_data.index[i].strftime('%m-%d %H:%M') 
                                for i in range(0, len(chart_data), 20)], 
                               rotation=45, color='white')
            
            # Hacim grafiği
            volumes = chart_data['volume'].values
            colors = [self.colors['candle_up'] if chart_data['close'].iloc[i] >= chart_data['open'].iloc[i] 
                     else self.colors['candle_down'] for i in range(len(chart_data))]
            
            ax2.bar(range(len(volumes)), volumes, color=colors, alpha=0.7)
            ax2.set_ylabel('Hacim', color='white')
            ax2.set_xlabel('Zaman', color='white')
            ax2.grid(True, alpha=0.3)
            
            # X ekseni ayarları (hacim için)
            ax2.set_xticks(range(0, len(chart_data), 20))
            ax2.set_xticklabels([chart_data.index[i].strftime('%m-%d %H:%M') 
                                for i in range(0, len(chart_data), 20)], 
                               rotation=45, color='white')
            
            plt.tight_layout()
            
            # Dosyayı kaydet
            filename = f'signal_{symbol}_{formation_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='black')
            plt.close()
            
            return filename
            
        except Exception as e:
            print(f"❌ Grafik oluşturma hatası: {e}")
            return None
    
    def create_signal_message(self, symbol: str, formation_type: str, 
                            entry_price: float, direction: str, levels: Dict, formation_data: Dict = None) -> str:
        """
        Telegram mesajı oluşturur
        
        Args:
            symbol (str): Sembol adı
            formation_type (str): Formasyon tipi
            entry_price (float): Giriş fiyatı
            direction (str): 'Long' veya 'Short'
            levels (Dict): Hedef seviyeler
            formation_data (Dict): Formasyon verisi (kalite skoru için)
            
        Returns:
            str: Telegram mesajı
        """
        formation_names = {
            'FALLING_WEDGE': '🔻 Düşen Takoz (Falling Wedge)',
            'TOBO': '📈 Üçgen Dışı Kırılım (TOBO)',
            'OBO': '📉 Üçgen Dışı Kırılım (OBO)',
            'CUP_HANDLE': '☕️ Fincan ve Kulp (Cup & Handle)',
            'BULLISH_FLAG': '🚩 Yükselen Bayrak (Bullish Flag)',
            'BEARISH_FLAG': '🏴 Düşen Bayrak (Bearish Flag)'
        }
        
        direction_emoji = '🟢' if direction == 'Long' else '🔴'
        
        # Kalite skoru ve R/R oranı - yeni sistem için
        quality_score = 0
        rr_ratio = 1.5
        
        if formation_data and 'quality_score' in formation_data:
            quality_score_data = formation_data.get('quality_score', 0)
            # quality_score bir dict ise total_score'u al, değilse direkt kullan
            if isinstance(quality_score_data, dict):
                quality_score = quality_score_data.get('total_score', 0)
            else:
                quality_score = quality_score_data
            rr_ratio = levels.get('rr_ratio', 1.5)
        else:
            # Eski sistem
            quality_score = formation_data.get('total_score', 0) if formation_data else 0
            # R/R oranı hesaplama - güvenli hesaplama
            try:
                if 'tp1' in levels and 'sl' in levels:
                    tp1 = levels['tp1']
                    sl = levels['sl']
                    if isinstance(tp1, (int, float)) and isinstance(sl, (int, float)) and isinstance(entry_price, (int, float)):
                        if entry_price > sl:  # Long pozisyon
                            rr_ratio = (tp1 - entry_price) / (entry_price - sl)
                        else:  # Short pozisyon
                            rr_ratio = (entry_price - sl) / (tp1 - entry_price)
                    else:
                        rr_ratio = 1.5
                else:
                    rr_ratio = 1.5
            except:
                rr_ratio = 1.5
        
        # Yön bazlı yüzde hesaplama
        if direction == 'Long':
            tp1_percent = ((levels['tp1']/entry_price-1)*100)
            tp2_percent = ((levels['tp2']/entry_price-1)*100)
            tp3_percent = ((levels['tp3']/entry_price-1)*100)
            sl_percent = ((levels['sl']/entry_price-1)*100)
        else:  # Short
            tp1_percent = ((levels['tp1']/entry_price-1)*100)  # Negatif olmalı
            tp2_percent = ((levels['tp2']/entry_price-1)*100)  # Negatif olmalı
            tp3_percent = ((levels['tp3']/entry_price-1)*100)  # Negatif olmalı
            sl_percent = ((levels['sl']/entry_price-1)*100)     # Pozitif olmalı
        
        message = f"""
🚨 **YENİ SİNYAL TESPİT EDİLDİ!** 🚨

📊 **Sembol:** {symbol}
🔍 **Formasyon:** {formation_names.get(formation_type, formation_type)}
{direction_emoji} **Yön:** {direction}
💰 **Giriş Fiyatı:** {format_price(entry_price)} USDT

🎯 **Hedef Seviyeler:**
• TP1: {format_price(levels['tp1'])} USDT ({tp1_percent:+.1f}%)
• TP2: {format_price(levels['tp2'])} USDT ({tp2_percent:+.1f}%)
• TP3: {format_price(levels['tp3'])} USDT ({tp3_percent:+.1f}%)
• SL: {format_price(levels['sl'])} USDT ({sl_percent:+.1f}%)

📈 **Risk/Ödül Oranı:** {rr_ratio:.2f}:1
🎯 **Kalite Skoru:** {quality_score}/400

⏰ **Sinyal Zamanı:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ **Risk Uyarısı:** Bot şuanda test aşamasındadır. Verilen grafikler yatırım tavsiyesi olmamakla beraber orta/yüksek ölçüde riskler taşımaktadır.
        """
        
        return message.strip()
    
    def visualize_single_formation(self, symbol: str, interval: str, formation: Dict, debug_mode=False) -> bool:
        """
        Tek bir formasyonu görselleştirir
        
        Args:
            symbol (str): Sembol adı
            interval (str): Zaman dilimi
            formation (Dict): Formasyon verisi
            debug_mode (bool): Debug modu
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            # Veri al
            df = self.get_formation_data(symbol, interval)
            if df.empty:
                print("❌ Veri alınamadı!")
                return False
            
            # Formasyon bilgileri
            formation_type = formation['type']
            direction = formation.get('direction', 'Long')
            
            # YENİ KURAL: Giriş fiyatı her zaman formasyonun kırılım mumunun kapanış fiyatı olmalı
            current_price = df['close'].iloc[-1]
            entry_price = current_price  # Kırılım mumunun kapanış fiyatı
            
            print(f"💰 Giriş Fiyatı: {format_price(entry_price)} (Kırılım mumunun kapanış fiyatı)")
            
            # Yeni gelişmiş formasyon tespit sistemi için farklı veri yapısı
            if formation_type in ['TOBO', 'OBO'] and 'quality_score' in formation:
                
                quality_score_data = formation.get('quality_score', 0)
                # quality_score bir dict ise total_score'u al, değilse direkt kullan
                if isinstance(quality_score_data, dict):
                    quality_score = quality_score_data.get('total_score', 0)
                else:
                    quality_score = quality_score_data
                rr_levels = formation.get('rr_levels', {})
                
                if debug_mode:
                    print(f"✅ Gelişmiş {formation_type} formasyonu görselleştiriliyor!")
                    print(f"📊 Yön: {direction}")
                    print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
                    print(f"🎯 Kalite Skor: {quality_score}/400")
                    print(f"📈 R/R Oranı: {rr_levels.get('rr_ratio', 0):.2f}:1")
                
                # Hedef seviyeleri her zaman calculate_target_levels ile hesapla
                print(f"🔧 OBO/TOBO formasyonu için hedef seviyeler yeniden hesaplanıyor...")
                levels = self.calculate_target_levels(entry_price, direction, formation)
            else:
                # Eski sistem - YENİ KURAL: Her zaman kırılım mumunun kapanış fiyatı
                entry_price = current_price  # Kırılım mumunun kapanış fiyatı
                print(f"💰 Giriş Fiyatı: {format_price(entry_price)} (Kırılım mumunun kapanış fiyatı)")
                
                quality_score = formation.get('quality_score', 0)
                
                if debug_mode:
                    print(f"✅ {formation_type} formasyonu görselleştiriliyor!")
                    print(f"📊 Yön: {direction}")
                    print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
                    print(f"🎯 Kalite Skor: {quality_score}")
                
                # Hedef seviyeleri hesapla - YENİ DÜZELTİLMİŞ YÖNTEM
                levels = self.calculate_target_levels(entry_price, direction, formation)
                
                # SHORT sinyaller için ek kontrol
                if direction == 'Short':
                    print(f"🔻 SHORT SİNYAL KONTROLÜ:")
                    print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
                    print(f"🛑 SL: {format_price(levels['sl'])} (Girişin üstünde olmalı)")
                    print(f"🎯 TP1: {format_price(levels['tp1'])} (Girişin altında olmalı)")
                    print(f"🎯 TP2: {format_price(levels['tp2'])} (Girişin altında olmalı)")
                    print(f"🎯 TP3: {format_price(levels['tp3'])} (Girişin altında olmalı)")
                    
                    # Güvenlik kontrolü
                    if levels['sl'] <= entry_price:
                        print(f"🚨 HATA: SL ({format_price(levels['sl'])}) giriş fiyatının ({format_price(entry_price)}) altında! Düzeltiliyor...")
                        levels['sl'] = entry_price * 1.03
                    if levels['tp1'] >= entry_price:
                        print(f"🚨 HATA: TP1 ({format_price(levels['tp1'])}) giriş fiyatının ({format_price(entry_price)}) üstünde! Düzeltiliyor...")
                        levels['tp1'] = entry_price * 0.955
                        levels['tp2'] = entry_price * 0.9325
                        levels['tp3'] = entry_price * 0.90
            
            # Grafik oluştur
            filename = self.create_candlestick_chart(df, formation_type, formation, 
                                                   entry_price, direction, symbol)
            
            if not filename:
                print("❌ Grafik oluşturulamadı!")
                return False
            
            # Telegram mesajı oluştur
            message = self.create_signal_message(symbol, formation_type, entry_price, direction, levels, formation)
            
            # Telegram'a gönder - ADMIN_CHAT_ID'ye gönder
            try:
                send_telegram_message(message, filename)
                print(f"✅ {formation_type} sinyali Telegram'a gönderildi: {filename}")
                return True
            except Exception as e:
                print(f"❌ Telegram gönderim hatası: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Tek formasyon görselleştirme hatası: {e}")
            return False

    def visualize_multiple_formations(self, symbol: str, interval: str, formations: List[Dict], debug_mode=False) -> bool:
        """
        Birden fazla formasyonu tek bir grafikte görselleştirir
        
        Args:
            symbol (str): Sembol adı
            interval (str): Zaman dilimi
            formations (List[Dict]): Formasyon listesi
            debug_mode (bool): Debug modu
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            if not formations:
                print("❌ Görselleştirilecek formasyon yok!")
                return False
            
            # Veri al
            df = self.get_formation_data(symbol, interval)
            if df.empty:
                print("❌ Veri alınamadı!")
                return False
            
            if debug_mode:
                print(f"🎯 {len(formations)} formasyon tek grafikte görselleştiriliyor...")
            
            # Grafik oluştur
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                           gridspec_kw={'height_ratios': [3, 1]})
            
            # Mum grafiği
            for i in range(len(df)):
                if df['close'].iloc[i] >= df['open'].iloc[i]:
                    color = self.colors['candle_up']
                    alpha = 0.8
                else:
                    color = self.colors['candle_down']
                    alpha = 0.8
                
                ax1.bar(df.index[i], df['high'].iloc[i] - df['low'].iloc[i], 
                       bottom=df['low'].iloc[i], width=0.6, color=color, alpha=alpha)
                ax1.bar(df.index[i], df['close'].iloc[i] - df['open'].iloc[i], 
                       bottom=df['open'].iloc[i], width=0.6, color=color, alpha=1)
            
            # Her formasyon için çizgiler çiz
            formation_info = []
            current_price = df['close'].iloc[-1]
            
            for i, formation in enumerate(formations):
                formation_type = formation.get('type', 'UNKNOWN')
                quality_score = formation.get('quality_score', 0)
                direction = formation.get('direction', 'Long')
                
                # Formasyon bilgilerini topla
                formation_info.append({
                    'type': formation_type,
                    'direction': direction,
                    'quality_score': quality_score
                })
                
                # Formasyon çizgilerini çiz
                if formation_type in ['TOBO', 'OBO']:
                    # TOBO/OBO için omuz ve boyun çizgileri
                    if 'sol_omuz' in formation and 'bas' in formation and 'sag_omuz' in formation:
                        sol_omuz_idx = formation.get('sol_omuz_index', 0)
                        bas_idx = formation.get('bas_index', 0)
                        sag_omuz_idx = formation.get('sag_omuz_index', 0)
                        
                        # Omuz çizgileri
                        ax1.plot([df.index[sol_omuz_idx], df.index[bas_idx], df.index[sag_omuz_idx]], 
                                [formation['sol_omuz'], formation['bas'], formation['sag_omuz']], 
                                color=self.colors['formation_line'], linewidth=2, 
                                label=f'{formation_type} Omuzlar')
                        
                        # Boyun çizgisi (yaklaşık)
                        if 'neckline' in formation:
                            neckline_price = formation.get('neckline', current_price)
                            ax1.axhline(y=neckline_price, color='yellow', linestyle='--', 
                                       alpha=0.7, label=f'{formation_type} Boyun')
                
                elif formation_type == 'FALLING_WEDGE':
                    # Falling Wedge için trend çizgileri
                    if 'upper_line' in formation and 'lower_line' in formation:
                        ax1.plot(formation['upper_line'], color='red', linewidth=2, 
                                label='Falling Wedge Üst')
                        ax1.plot(formation['lower_line'], color='green', linewidth=2, 
                                label='Falling Wedge Alt')
                
                elif formation_type == 'CUP_AND_HANDLE':
                    # Cup & Handle için destek çizgisi
                    if 'support' in formation:
                        ax1.axhline(y=formation['support'], color='green', linestyle='--', 
                                   alpha=0.7, label='Cup & Handle Destek')
                
                elif formation_type in ['BULLISH_FLAG', 'BEARISH_FLAG']:
                    # Flag için paralel çizgiler
                    if 'upper_parallel' in formation and 'lower_parallel' in formation:
                        ax1.plot(formation['upper_parallel'], color='orange', linewidth=2, 
                                label=f'{formation_type} Üst')
                        ax1.plot(formation['lower_parallel'], color='orange', linewidth=2, 
                                label=f'{formation_type} Alt')
                
                # Giriş noktası
                ax1.scatter(df.index[-1], current_price, color=self.colors['entry_point'], 
                           s=100, zorder=5, label='Giriş Noktası')
            
            # Hacim grafiği
            ax2.bar(df.index, df['volume'], color=self.colors['volume'], alpha=0.7)
            
            # Grafik ayarları
            ax1.set_title(f'{symbol} - {interval} - Çoklu Formasyon Analizi', 
                         fontsize=14, fontweight='bold', color='white')
            ax1.set_ylabel('Fiyat', color='white')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left', fontsize=8)
            
            ax2.set_title('Hacim', fontsize=12, color='white')
            ax2.set_ylabel('Hacim', color='white')
            ax2.set_xlabel('Zaman', color='white')
            ax2.grid(True, alpha=0.3)
            
            # Tarih formatı
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            
            plt.tight_layout()
            
            # Grafik kaydet
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"multiple_formations_{symbol}_{interval}_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='black')
            plt.close()
            
            # Telegram mesajı oluştur
            message = f"🎯 **{symbol} - {interval} - Çoklu Formasyon Sinyali**\n\n"
            message += f"📊 **Tespit Edilen Formasyonlar:**\n"
            
            for i, info in enumerate(formation_info, 1):
                message += f"   {i}. **{info['type']}** ({info['direction']}) - Skor: {info['quality_score']}/200\n"
            
            message += f"\n💰 **Mevcut Fiyat:** {format_price(current_price)}"
            message += f"\n⏰ **Zaman:** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            message += f"\n\n🔍 **Toplam {len(formations)} güçlü formasyon tespit edildi!**"
            
            # Telegram'a gönder
            try:
                send_telegram_message(message, filename)
                print(f"✅ Çoklu formasyon sinyali Telegram'a gönderildi: {filename}")
                return True
            except Exception as e:
                print(f"❌ Telegram gönderim hatası: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Çoklu formasyon görselleştirme hatası: {e}")
            return False

    def detect_and_visualize_formation(self, symbol: str, interval: str = '1h', debug_mode=False) -> bool:
        """
        Formasyon tespit eder ve görselleştirir
        
        Args:
            symbol (str): Sembol adı
            interval (str): Zaman dilimi
            debug_mode (bool): Debug modu
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            print(f"🔍 {symbol} formasyon analizi başlatılıyor...")
            
            # Veri al
            df = self.get_formation_data(symbol, interval)
            if df.empty:
                print("❌ Veri alınamadı!")
                return False
            
            # ÇOKLU FORMASYON TESPİTİ
            all_formations = []
            
            # GELİŞMİŞ TOBO tespiti (Yeni 5.0 kuralları)
            tobo_formation = detect_inverse_head_and_shoulders(df, window=30)
            if tobo_formation:
                if tobo_formation and isinstance(tobo_formation, dict):
                    tobo_formation['type'] = 'TOBO'
                    tobo_formation['direction'] = 'Long'
                    all_formations.append(tobo_formation)
                    print(f"✅ Gelişmiş TOBO tespit edildi")
            
            # GELİŞMİŞ OBO tespiti (Yeni 5.0 kuralları)
            obo_formation = detect_head_and_shoulders(df, window=30)
            if obo_formation:
                if obo_formation and isinstance(obo_formation, dict):
                    obo_formation['type'] = 'OBO'
                    obo_formation['direction'] = 'Short'
                    all_formations.append(obo_formation)
                    print(f"✅ Gelişmiş OBO tespit edildi")
            
            # Falling Wedge (eski fonksiyon - botanlik ile uyumlu)
            falling_wedge = detect_falling_wedge(df)
            if falling_wedge:
                for formation in falling_wedge:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'FALLING_WEDGE'
                        formation['direction'] = 'Long'
                        all_formations.append(formation)
            
            # TOBO (GERİ AÇILDI)
            tobo_formations = find_all_tobo(df)
            if tobo_formations:
                for formation in tobo_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'TOBO'
                        formation['direction'] = 'Long'
                        all_formations.append(formation)
                        print(f"✅ Legacy TOBO tespit edildi")
            
            # OBO (GERİ AÇILDI)
            obo_formations = find_all_obo(df)
            if obo_formations:
                for formation in obo_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'OBO'
                        formation['direction'] = 'Short'
                        all_formations.append(formation)
                        print(f"✅ Legacy OBO tespit edildi")
            
            # Cup & Handle
            cup_formations = detect_cup_and_handle(df)
            if cup_formations:
                for formation in cup_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'CUP_HANDLE'
                        formation['direction'] = 'Long'
                        all_formations.append(formation)
            
            # Bullish/Bearish Flag
            flag_formations = detect_bullish_bearish_flag(df)
            if flag_formations:
                for formation in flag_formations:
                    if formation and isinstance(formation, dict):
                        if formation.get('type') == 'Bullish Flag':
                            formation['type'] = 'BULLISH_FLAG'
                            formation['direction'] = 'Long'
                        elif formation.get('type') == 'Bearish Flag':
                            formation['type'] = 'BEARISH_FLAG'
                            formation['direction'] = 'Short'
                        all_formations.append(formation)
            
            if debug_mode:
                print(f"📈 Tespit edilen formasyon sayısı: {len(all_formations)}")
                for formation in all_formations:
                    print(f"   - {formation.get('type', 'UNKNOWN')} (Skor: {formation.get('score', 'N/A')})")
            
            if not all_formations:
                print("❌ Formasyon bulunamadı!")
                return False
            
            # KALİTE FİLTRESİ - Sadece güçlü formasyonları al
            filtered_formations = filter_high_quality_formations(df, all_formations, debug_mode)
            
            if debug_mode:
                print(f"🎯 Kalite filtresi sonrası: {len(filtered_formations)} güçlü formasyon")
                for formation in filtered_formations:
                    print(f"   ✅ {formation.get('type', 'UNKNOWN')} (Kalite Skor: {formation.get('quality_score', 'N/A')})")
            
            if not filtered_formations:
                print("❌ Güçlü formasyon bulunamadı!")
                return False
            
            # En iyi formasyonu seç (kalite skoruna göre)
            best_formation = None
            best_score = 0
            
            for formation in filtered_formations:
                quality_score = formation.get('quality_score', 0)
                if quality_score > best_score:
                    best_score = quality_score
                    best_formation = formation
            
            if not best_formation:
                best_formation = filtered_formations[0]  # İlk formasyonu al
            
            # Formasyon bilgileri
            formation_type = best_formation['type']
            direction = best_formation.get('direction', 'Long')
            # Formasyon verilerinden entry_price al
            if 'entry_price' in best_formation and best_formation['entry_price'] > 0:
                entry_price = best_formation['entry_price']
            elif 'neckline' in best_formation and best_formation['neckline'] > 0:
                entry_price = best_formation['neckline']
            else:
                entry_price = df['close'].iloc[-1]
            
            print(f"✅ {formation_type} formasyonu tespit edildi!")
            print(f"📊 Yön: {direction}")
            print(f"💰 Giriş Fiyatı: {format_price(entry_price)}")
            
            # Hedef seviyeleri hesapla
            levels = self.calculate_target_levels(entry_price, direction, best_formation)
            
            # Grafik oluştur
            filename = self.create_candlestick_chart(df, formation_type, best_formation, 
                                                   entry_price, direction, symbol)
            
            if not filename:
                print("❌ Grafik oluşturulamadı!")
                return False
            
            # Telegram mesajı oluştur
            message = self.create_signal_message(symbol, formation_type, entry_price, direction, levels)
            
            # Telegram'a gönder
            try:
                send_telegram_message(message, filename)
                print(f"✅ Sinyal Telegram'a gönderildi: {filename}")
                return True
            except Exception as e:
                print(f"❌ Telegram gönderim hatası: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Formasyon analizi hatası: {e}")
            return False


def main():
    """
    Test fonksiyonu
    """
    print("🚀 Signal Visualizer Test Başlatılıyor...")
    print("=" * 50)
    
    visualizer = SignalVisualizer()
    
    # Test sembolleri
    test_symbols = ['SOLUSDT', 'AVAXUSDT', 'MATICUSDT']
    
    for symbol in test_symbols:
        print(f"\n🔍 {symbol} test ediliyor...")
        success = visualizer.detect_and_visualize_formation(symbol, debug_mode=True)
        
        if success:
            print(f"✅ {symbol} analizi başarılı!")
        else:
            print(f"❌ {symbol} analizi başarısız!")
        
        # Kısa bekleme
        import time
        time.sleep(2)
    
    print("\n✅ Test tamamlandı!")


if __name__ == "__main__":
    main() 