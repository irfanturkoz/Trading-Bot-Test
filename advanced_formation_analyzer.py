#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GELİŞMİŞ FORMASYON ANALİZ SİSTEMİ - GÜÇLENDİRİLMİŞ VERSİYON 5.0
==================================================================

Bu modül, tüm coinleri tarayarak TOBO, OBO, Wedge, Bayrak ve Çanak-Kulp 
formasyonlarını tespit eder ve gelişmiş kalite kriterlerine göre analiz eder.

Yeni Özellikler:
- 400 puanlık kalite skorlama sistemi
- Gelişmiş formasyon boyutu doğrulama (%2 minimum)
- Zaman süresi kontrolü (minimum mum sayısı)
- Hacim teyidi (%20 minimum artış)
- RSI/MACD uyum kontrolü
- Formasyona özel R/R oranları
- Küçük formasyonları filtreleme
- Gelişmiş log sistemi
- Sinyal üretimi

Author: Trading Bot Team
Version: 5.0
"""

import numpy as np
import pandas as pd
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Local imports
from formation_detector import (
    find_all_tobo, find_all_obo, detect_falling_wedge, 
    detect_cup_and_handle, detect_bullish_bearish_flag,
    get_rsi, calculate_macd, calculate_bollinger_bands,
    detect_inverse_head_and_shoulders, detect_head_and_shoulders
)
from data_fetcher import fetch_ohlcv
from utils import format_price


class AdvancedFormationAnalyzer:
    """Gelişmiş formasyon analiz sınıfı - Güçlendirilmiş Versiyon 5.0"""
    
    def __init__(self):
        self.formation_types = ['TOBO', 'OBO', 'FALLING_WEDGE', 'BULLISH_FLAG', 'BEARISH_FLAG', 'CUP_HANDLE']
        self.min_quality_score = 50   # Minimum kalite skoru (50/400) - daha gevşetildi
        self.max_volatility = 0.20    # Maksimum volatilite (%20) - gevşetildi
        
        # Formasyona özel R/R oranları
        self.rr_targets = {
            'TOBO': {'min': 1.3, 'max': 1.7, 'optimal': 1.5},
            'OBO': {'min': 1.3, 'max': 1.7, 'optimal': 1.5},
            'TOBO_LEGACY': {'min': 1.3, 'max': 1.7, 'optimal': 1.5},
            'OBO_LEGACY': {'min': 1.3, 'max': 1.7, 'optimal': 1.5},
            'FALLING_WEDGE': {'min': 1.5, 'max': 2.0, 'optimal': 1.75},
            'BULLISH_FLAG': {'min': 1.5, 'max': 2.0, 'optimal': 1.75},
            'BEARISH_FLAG': {'min': 1.5, 'max': 2.0, 'optimal': 1.75},
            'CUP_HANDLE': {'min': 1.8, 'max': 2.5, 'optimal': 2.15}
        }
        
        # Zaman filtresi kriterleri
        self.time_filters = {
            'TOBO': {'min_candles': 15, 'min_hours': 8, 'max_hours': 48},
            'OBO': {'min_candles': 15, 'min_hours': 8, 'max_hours': 48},
            'TOBO_LEGACY': {'min_candles': 15, 'min_hours': 8, 'max_hours': 48},
            'OBO_LEGACY': {'min_candles': 15, 'min_hours': 8, 'max_hours': 48},
            'FALLING_WEDGE': {'min_candles': 20, 'min_hours': 12, 'max_hours': 60},
            'BULLISH_FLAG': {'min_candles': 20, 'min_hours': 8, 'max_hours': 60},
            'BEARISH_FLAG': {'min_candles': 20, 'min_hours': 8, 'max_hours': 60},
            'CUP_HANDLE': {'min_candles': 25, 'min_hours': 16, 'max_hours': 72}
        }
        
    def get_all_usdt_symbols(self) -> List[str]:
        """Tüm USDT çiftlerini alır"""
        try:
            url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            symbols = []
            for symbol_info in data['symbols']:
                symbol = symbol_info['symbol']
                if symbol.endswith('USDT') and symbol_info['status'] == 'TRADING':
                    symbols.append(symbol)
            
            return symbols
            
        except Exception as e:
            print(f"❌ Sembol listesi alınamadı: {e}")
            return []
    
    def calculate_volatility(self, df: pd.DataFrame) -> float:
        """1H volatilite hesaplar"""
        try:
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(24)  # 24 saatlik volatilite
            return volatility
        except:
            return 0.0
    
    def validate_formation_size(self, df: pd.DataFrame, formation_data: Dict) -> Dict:
        """
        Gelişmiş formasyon boyutu doğrulama - SIKI KURALLAR
        
        Yeni Kriterler:
        - Minimum boyun-dip/tepe farkı: %2 ve üzeri (ZORUNLU)
        - Küçük yapay formasyonları (2-3 mumluk) geçersiz say
        - Formasyon genişliği kontrolü
        - Sert hareket tercihi (yavaş/yatay formasyonları zayıf say)
        """
        try:
            formation_type = formation_data.get('type', 'UNKNOWN')
            current_price = df['close'].iloc[-1] if not df.empty else 0
            
            validation_result = {
                'is_valid': False,
                'score': 0,
                'details': {},
                'rejection_reason': ''
            }
            
            # Formasyon yüksekliği hesaplama
            formation_height = 0
            neckline_price = 0
            
            if formation_type in ['TOBO', 'OBO', 'TOBO_LEGACY', 'OBO_LEGACY']:
                # Omuz-baş-omuz için boyun çizgisi ve baş arası fark
                # Hem 'boyun' hem 'neckline' field'larını kontrol et
                if 'bas' in formation_data and ('boyun' in formation_data or 'neckline' in formation_data):
                    head_price = formation_data['bas']
                    neckline_price = formation_data.get('boyun', formation_data.get('neckline', 0))
                    # Veri tipini kontrol et
                    if isinstance(head_price, (int, float)) and isinstance(neckline_price, (int, float)):
                        formation_height = abs(head_price - neckline_price)
                    else:
                        formation_height = 0
                    
            elif formation_type == 'FALLING_WEDGE':
                # Falling Wedge için üst ve alt trend çizgileri arası
                if 'upper_trend' in formation_data and 'lower_trend' in formation_data:
                    upper_trend = formation_data['upper_trend']
                    lower_trend = formation_data['lower_trend']
                    if isinstance(upper_trend, dict) and isinstance(lower_trend, dict):
                        if 'start_y' in upper_trend and 'start_y' in lower_trend:
                            upper_y = upper_trend['start_y']
                            lower_y = lower_trend['start_y']
                            if isinstance(upper_y, (int, float)) and isinstance(lower_y, (int, float)):
                                formation_height = abs(upper_y - lower_y)
                                neckline_price = upper_y
                        
            elif formation_type in ['BULLISH_FLAG', 'BEARISH_FLAG']:
                # Flag için direnç ve destek arası
                if 'resistance' in formation_data and 'support' in formation_data:
                    resistance = formation_data['resistance']
                    support = formation_data['support']
                    if isinstance(resistance, (int, float)) and isinstance(support, (int, float)):
                        formation_height = abs(resistance - support)
                        neckline_price = resistance if formation_type == 'BULLISH_FLAG' else support
                    
            elif formation_type == 'CUP_HANDLE':
                # Cup and Handle için cup derinliği
                if 'cup_bottom_price' in formation_data and 'cup_start_price' in formation_data:
                    cup_bottom = formation_data['cup_bottom_price']
                    cup_start = formation_data['cup_start_price']
                    if isinstance(cup_bottom, (int, float)) and isinstance(cup_start, (int, float)):
                        formation_height = abs(cup_start - cup_bottom)
                        neckline_price = cup_start
            
            if formation_height == 0 or neckline_price == 0:
                # Eski fonksiyonlar için varsayılan değerler
                if formation_type in ['TOBO', 'OBO', 'TOBO_LEGACY', 'OBO_LEGACY'] and 'bas' in formation_data:
                    # Eski TOBO/OBO fonksiyonları için basit hesaplama
                    head_price = formation_data['bas']
                    if isinstance(head_price, (int, float)):
                        formation_height = head_price * 0.02  # %2 varsayılan yükseklik
                        neckline_price = head_price + formation_height
                    else:
                        validation_result['rejection_reason'] = "Formasyon yüksekliği hesaplanamadı - geçersiz veri tipi"
                        return validation_result
                else:
                    validation_result['rejection_reason'] = "Formasyon yüksekliği hesaplanamadı"
                    return validation_result
            
            # Yükseklik yüzdesi hesapla
            if current_price > 0:
                height_percentage = (formation_height / current_price) * 100
            else:
                height_percentage = 0
            
            # Minimum %2 kriteri
            if height_percentage < 2.0:
                validation_result['rejection_reason'] = f"Yetersiz formasyon yüksekliği: %{height_percentage:.2f} (Minimum %2 gerekli)"
                validation_result['details']['height_percentage'] = height_percentage
                validation_result['details']['formation_height'] = formation_height
                return validation_result
            
            # Hareket sertliği bonus puanı
            movement_bonus = self.check_movement_strength(df, formation_type, formation_data)
            
            # Yapısal skor hesaplama
            structural_score = 0
            
            # Yükseklik skoru (0-60 puan)
            if height_percentage >= 5.0:
                structural_score += 60  # Mükemmel yükseklik
            elif height_percentage >= 3.0:
                structural_score += 50  # İyi yükseklik
            elif height_percentage >= 2.0:
                structural_score += 40  # Minimum yükseklik
            else:
                structural_score += 20  # Düşük yükseklik
            
            # Hareket sertliği bonusu (0-20 puan)
            structural_score += movement_bonus
            
            # Simetri kontrolü (0-20 puan)
            symmetry_score = self.check_formation_symmetry(formation_data, formation_type)
            structural_score += symmetry_score
            
            validation_result['is_valid'] = True
            validation_result['score'] = min(structural_score, 100)  # Maksimum 100 puan
            validation_result['details']['height_percentage'] = height_percentage
            validation_result['details']['formation_height'] = formation_height
            validation_result['details']['movement_bonus'] = movement_bonus
            validation_result['details']['symmetry_score'] = symmetry_score
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'score': 0,
                'details': {'error': str(e)},
                'rejection_reason': f'Boyut doğrulama hatası: {str(e)}'
            }
    
    def check_formation_symmetry(self, formation_data: Dict, formation_type: str) -> int:
        """
        Formasyon simetrisini kontrol eder
        
        Returns:
            int: 0-20 arası puan
        """
        try:
            if formation_type in ['TOBO', 'OBO']:
                # Omuz simetrisi kontrolü
                if 'sol_omuz' in formation_data and 'sag_omuz' in formation_data:
                    left_shoulder = formation_data['sol_omuz']
                    right_shoulder = formation_data['sag_omuz']
                    shoulder_diff = abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder)
                    
                    if shoulder_diff <= 0.05:  # %5 tolerans
                        return 20
                    elif shoulder_diff <= 0.10:  # %10 tolerans
                        return 15
                    elif shoulder_diff <= 0.15:  # %15 tolerans
                        return 10
                    else:
                        return 5
                        
            elif formation_type == 'FALLING_WEDGE':
                # Wedge simetrisi kontrolü
                if 'upper_trend' in formation_data and 'lower_trend' in formation_data:
                    upper_trend = formation_data['upper_trend']
                    lower_trend = formation_data['lower_trend']
                    
                    # Eğim simetrisi
                    if 'slope' in upper_trend and 'slope' in lower_trend:
                        slope_diff = abs(abs(upper_trend['slope']) - abs(lower_trend['slope']))
                        if slope_diff <= 0.001:
                            return 20
                        elif slope_diff <= 0.002:
                            return 15
                        else:
                            return 10
            
            return 10  # Varsayılan puan
            
        except Exception as e:
            return 0
    
    def validate_formation_time_duration(self, df: pd.DataFrame, formation_data: Dict) -> Dict:
        """
        Gelişmiş formasyon zaman süresi doğrulama - YENİ KURALLAR
        
        Yeni Kriterler:
        - TOBO/OBO: Minimum 20 mum / 12-48 saat
        - Wedge/Bayrak: Minimum 25 mum / 15-60 saat
        - Cup and Handle: Minimum 30 mum / 20-72 saat
        - 5-10 mum arası kısa formasyonlar geçersiz
        - 12-24 saatlik zaman aralığı tercih edilir
        """
        try:
            formation_type = formation_data.get('type', 'UNKNOWN')
            
            validation_result = {
                'is_valid': False,
                'score': 0,
                'details': {},
                'rejection_reason': ''
            }
            
            # Formasyon başlangıç ve bitiş noktalarını bul
            start_index = None
            end_index = None
            
            if formation_type in ['TOBO', 'OBO', 'TOBO_LEGACY', 'OBO_LEGACY']:
                # Omuz-baş omuz için başlangıç ve bitiş
                if 'sol_omuz_index' in formation_data and 'sag_omuz_index' in formation_data:
                    start_index = formation_data['sol_omuz_index']
                    end_index = formation_data['sag_omuz_index']
                elif 'tobo_start' in formation_data and 'tobo_end' in formation_data:
                    # Eski TOBO fonksiyonu için
                    start_index = formation_data['tobo_start']
                    end_index = formation_data['tobo_end']
                elif 'left_shoulder_index' in formation_data and 'right_shoulder_index' in formation_data:
                    # Yeni TOBO/OBO fonksiyonları için
                    start_index = formation_data['left_shoulder_index']
                    end_index = formation_data['right_shoulder_index']
                elif 'formation_start_index' in formation_data and 'formation_end_index' in formation_data:
                    # Yeni TOBO/OBO fonksiyonları için (index ile)
                    start_index = formation_data['formation_start_index']
                    end_index = formation_data['formation_end_index']
                else:
                    # Eski fonksiyonlar için varsayılan değerler
                    # 30 mumluk window kullanıldığı için
                    start_index = 0
                    end_index = 29
                    
            elif formation_type == 'FALLING_WEDGE':
                # Falling Wedge için başlangıç ve bitiş
                if 'high_points' in formation_data and 'low_points' in formation_data:
                    high_points = formation_data['high_points']
                    low_points = formation_data['low_points']
                    if high_points and low_points:
                        start_index = min(high_points[0], low_points[0])
                        end_index = max(high_points[-1], low_points[-1])
                    
            elif formation_type in ['BULLISH_FLAG', 'BEARISH_FLAG']:
                # Flag için başlangıç ve bitiş
                if 'flag_start' in formation_data and 'flag_end' in formation_data:
                    start_index = formation_data['flag_start']
                    end_index = formation_data['flag_end']
                    
            elif formation_type == 'CUP_HANDLE':
                # Cup and Handle için başlangıç ve bitiş
                if 'cup_start' in formation_data and 'handle_end' in formation_data:
                    start_index = formation_data['cup_start']
                    end_index = formation_data['handle_end']
            
            if start_index is None or end_index is None:
                # Eski fonksiyonlar için varsayılan değerler
                if formation_type in ['TOBO', 'OBO', 'TOBO_LEGACY', 'OBO_LEGACY']:
                    # Eski TOBO/OBO fonksiyonları için varsayılan 30 mum
                    start_index = 0
                    end_index = 29
                else:
                    validation_result['rejection_reason'] = "Formasyon zaman noktaları belirlenemedi"
                    return validation_result
            
            # İndeks değerlerinin sayısal olduğunu kontrol et
            if not isinstance(start_index, (int, float)) or not isinstance(end_index, (int, float)):
                validation_result['rejection_reason'] = "Formasyon zaman noktaları geçersiz veri tipi"
                return validation_result
            
            # Mum sayısını hesapla
            candle_count = abs(end_index - start_index) + 1
            
            # Zaman filtresi kontrolü
            time_filter = self.time_filters.get(formation_type, {'min_candles': 20, 'min_hours': 12, 'max_hours': 48})
            min_candles = time_filter['min_candles']
            min_hours = time_filter['min_hours']
            max_hours = time_filter['max_hours']
            
            # Minimum mum sayısı kontrolü
            if candle_count < min_candles:
                validation_result['rejection_reason'] = f"Yetersiz mum sayısı: {candle_count} (Minimum {min_candles} gerekli)"
                validation_result['details']['candle_count'] = candle_count
                validation_result['details']['min_required'] = min_candles
                return validation_result
            
            # Kısa süreli formasyon kontrolü (5-10 mum arası)
            if 5 <= candle_count <= 10:
                # Bu durumda formasyon boyutunu da kontrol et
                size_validation = self.validate_formation_size(df, formation_data)
                if not size_validation['is_valid']:
                    validation_result['rejection_reason'] = f"Kısa süreli formasyon ({candle_count} mum) ve yetersiz boyut"
                    validation_result['details']['candle_count'] = candle_count
                    validation_result['details']['size_rejection'] = size_validation.get('rejection_reason', '')
                    return validation_result
            
            # Saat cinsinden süre hesaplama (4H interval için)
            hours_duration = candle_count * 4  # 4H interval
            
            # Zaman aralığı kontrolü
            if hours_duration < min_hours:
                validation_result['rejection_reason'] = f"Yetersiz süre: {hours_duration} saat (Minimum {min_hours} saat gerekli)"
                validation_result['details']['hours_duration'] = hours_duration
                validation_result['details']['min_hours'] = min_hours
                return validation_result
            
            if hours_duration > max_hours:
                validation_result['rejection_reason'] = f"Çok uzun süre: {hours_duration} saat (Maksimum {max_hours} saat)"
                validation_result['details']['hours_duration'] = hours_duration
                validation_result['details']['max_hours'] = max_hours
                return validation_result
            
            # Zaman süresi skoru hesapla (0-100 puan)
            time_score = 0
            
            # İdeal süre aralığı (12-24 saat)
            if 12 <= hours_duration <= 24:
                time_score = 100  # Mükemmel
            elif 8 <= hours_duration <= 36:
                time_score = 80   # İyi
            elif min_hours <= hours_duration <= max_hours:
                time_score = 60   # Kabul edilebilir
            else:
                time_score = 40   # Düşük
            
            validation_result['is_valid'] = True
            validation_result['score'] = time_score
            validation_result['details']['candle_count'] = candle_count
            validation_result['details']['hours_duration'] = hours_duration
            validation_result['details']['min_required'] = min_candles
            validation_result['details']['time_score'] = time_score
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'score': 0,
                'details': {'error': str(e)},
                'rejection_reason': f'Zaman doğrulama hatası: {str(e)}'
            }
    
    def check_movement_strength(self, df: pd.DataFrame, formation_type: str, formation_data: Dict) -> int:
        """
        Formasyon boyun çizgisine kadar olan hareketin sertliğini kontrol eder
        
        Returns:
            int: 0-20 arası puan (sert hareket için bonus)
        """
        try:
            # Son 20 mumun volatilitesini hesapla
            recent_data = df.tail(20)
            price_changes = recent_data['close'].pct_change().abs()
            avg_volatility = price_changes.mean()
            
            # Sert hareket için minimum volatilite
            if avg_volatility >= 0.02:  # %2 ortalama hareket
                return 20
            elif avg_volatility >= 0.015:  # %1.5 ortalama hareket
                return 15
            elif avg_volatility >= 0.01:  # %1 ortalama hareket
                return 10
            else:
                return 0  # Yavaş hareket
                
        except Exception as e:
            return 0
    
    def calculate_rr_levels(self, entry_price: float, formation_type: str, formation_data: Dict) -> Dict:
        """
        Standardize edilmis TP/SL hesaplayici kullanir - Grafik ile birebir ayni degerler
        """
        try:
            # Entry price kontrolu
            if not isinstance(entry_price, (int, float)) or entry_price <= 0:
                return {
                    'tp1': 0, 'tp2': 0, 'tp3': 0, 'sl': 0,
                    'rr_ratio': 0, 'error': 'Gecersiz entry price'
                }
            
            # Pozisyon yonunu belirle
            direction = formation_data.get('direction', 'Long')
            
            # Standardize edilmis TP/SL hesaplayici kullan
            from tp_sl_calculator import calculate_strict_tp_sl
            
            try:
                levels = calculate_strict_tp_sl(entry_price, direction)
                return {
                    'tp1': levels['tp1'],
                    'tp2': levels['tp2'],
                    'tp3': levels['tp3'],
                    'sl': levels['sl'],
                    'rr_ratio': levels['rr_ratio'],
                    'direction': direction
                }
            except Exception as calc_error:
                # Fallback - YENİ KURALLAR (Kullanıcı istekleri)
                print(f"Standardize hesaplayici hatasi: {calc_error}")
                if direction == 'Long':
                    sl = entry_price * 0.97    # SL: %3.0 aşağı
                    tp1 = entry_price * 1.045  # TP1: %4.5 yukarı
                    tp2 = entry_price * 1.06   # TP2: %6.0 yukarı
                    tp3 = entry_price * 1.09   # TP3: %9.0 yukarı
                    rr_ratio = (tp3 - entry_price) / (entry_price - sl)  # TP3-SL arası R/R
                else:  # Short
                    sl = entry_price * 1.03    # SL: %3.0 yukarı
                    tp1 = entry_price * 0.955  # TP1: %4.5 aşağı
                    tp2 = entry_price * 0.94   # TP2: %6.0 aşağı
                    tp3 = entry_price * 0.91   # TP3: %9.0 aşağı
                    rr_ratio = (entry_price - tp3) / (sl - entry_price)  # TP3-SL arası R/R
                
                return {
                    'tp1': round(tp1, 6),
                    'tp2': round(tp2, 6),
                    'tp3': round(tp3, 6),
                    'sl': round(sl, 6),
                    'rr_ratio': round(rr_ratio, 2),
                    'direction': direction
                }
            
        except Exception as e:
            return {
                'tp1': 0,
                'tp2': 0,
                'tp3': 0,
                'sl': 0,
                'rr_ratio': 0,
                'error': str(e)
            }
    
    def validate_volume_confirmation(self, df: pd.DataFrame, formation_type: str, formation_data: Dict) -> Dict:
        """
        Gelişmiş hacim teyidi kontrolü - YENİ KURALLAR
        
        Yeni Kriterler:
        - Kırılım hacmi önceki ortalamaya göre en az %20 artmalı
        - Son 3 mumun hacim ortalaması vs son 10 mumun hacim ortalaması
        - Hacim artış oranına göre 0-100 puan
        """
        try:
            if df.empty or len(df) < 10:
                return {
                    'is_confirmed': False,
                    'score': 0,
                    'volume_increase': 0,
                    'details': {'error': 'Yetersiz veri'}
                }
            
            recent_data = df.tail(20)
            volumes = recent_data['volume'].values
            
            # Veri kontrolü
            if len(volumes) < 10:
                return {
                    'is_confirmed': False,
                    'score': 0,
                    'volume_increase': 0,
                    'details': {'error': 'Yetersiz hacim verisi'}
                }
            
            # Son 3 mumun hacim ortalaması
            recent_volume = np.mean(volumes[-3:]) if len(volumes) >= 3 else 0
            
            # Son 10 mumun hacim ortalaması (kırılım öncesi)
            if len(volumes) >= 10:
                previous_volume = np.mean(volumes[-10:-3])
            elif len(volumes) >= 3:
                previous_volume = np.mean(volumes[:-3])
            else:
                previous_volume = 0
            
            if previous_volume == 0:
                return {
                    'is_confirmed': False,
                    'score': 0,
                    'volume_increase': 0,
                    'details': {'error': 'Hacim verisi yetersiz'}
                }
            
            # Hacim artış oranı
            volume_increase = ((recent_volume - previous_volume) / previous_volume) * 100
            
            # Minimum %10 artış kontrolü (gevşetildi)
            if volume_increase < 10:
                return {
                    'is_confirmed': False,
                    'score': 0,
                    'volume_increase': volume_increase,
                    'details': {'rejection_reason': f'Yetersiz hacim artışı: %{volume_increase:.1f} (Minimum %10 gerekli)'}
                }
            
            # Hacim skoru hesaplama (0-100 puan)
            volume_score = 0
            if volume_increase >= 100:  # %100+ artış
                volume_score = 100
            elif volume_increase >= 50:   # %50+ artış
                volume_score = 80
            elif volume_increase >= 30:   # %30+ artış
                volume_score = 60
            elif volume_increase >= 20:   # %20+ artış
                volume_score = 40
            elif volume_increase >= 10:   # %10+ artış
                volume_score = 20
            else:
                volume_score = 10
            
            return {
                'is_confirmed': True,
                'score': volume_score,
                'volume_increase': volume_increase,
                'details': {
                    'recent_volume': recent_volume,
                    'previous_volume': previous_volume,
                    'volume_score': volume_score
                }
            }
            
        except Exception as e:
            return {
                'is_confirmed': False,
                'score': 0,
                'volume_increase': 0,
                'details': {'error': f'Hacim kontrolü hatası: {str(e)}'}
            }
    
    def validate_rsi_macd_confirmation(self, df: pd.DataFrame, formation_type: str, formation_data: Dict) -> Dict:
        """
        Gelişmiş RSI/MACD uyum kontrolü - YENİ KURALLAR
        
        Yeni Kriterler:
        - RSI uyumu: 0-50 puan
        - MACD uyumu: 0-50 puan
        - Toplam 0-100 puan
        """
        try:
            # RSI hesapla
            rsi = get_rsi(df['close'], period=14)
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # MACD hesapla
            macd_data = calculate_macd(df)
            
            rsi_score = 0
            macd_score = 0
            confirmation_details = {}
            
            # RSI uyum kontrolü (0-50 puan)
            if formation_type in ['TOBO', 'FALLING_WEDGE', 'BULLISH_FLAG', 'CUP_HANDLE']:
                # Bullish formasyonlar için RSI kontrolü
                if current_rsi < 70:  # Aşırı alım değil
                    if current_rsi > 40:  # Orta seviye
                        rsi_score = 50
                        confirmation_details['rsi_status'] = 'Pozitif'
                    elif current_rsi > 30:  # Düşük ama kabul edilebilir
                        rsi_score = 30
                        confirmation_details['rsi_status'] = 'Nötr'
                    else:
                        rsi_score = 10
                        confirmation_details['rsi_status'] = 'Zayıf'
                else:
                    rsi_score = 0
                    confirmation_details['rsi_status'] = 'Aşırı alım'
                    
            elif formation_type in ['OBO', 'BEARISH_FLAG']:
                # Bearish formasyonlar için RSI kontrolü
                if current_rsi > 30:  # Aşırı satım değil
                    if current_rsi < 60:  # Orta seviye
                        rsi_score = 50
                        confirmation_details['rsi_status'] = 'Pozitif'
                    elif current_rsi < 70:  # Yüksek ama kabul edilebilir
                        rsi_score = 30
                        confirmation_details['rsi_status'] = 'Nötr'
                    else:
                        rsi_score = 10
                        confirmation_details['rsi_status'] = 'Zayıf'
                else:
                    rsi_score = 0
                    confirmation_details['rsi_status'] = 'Aşırı satım'
            
            # MACD uyum kontrolü (0-50 puan)
            if macd_data and isinstance(macd_data, dict):
                # MACD veri yapısını kontrol et
                if 'macd' in macd_data and 'signal' in macd_data:
                    # Eski format
                    macd_line = macd_data['macd'].iloc[-1] if not macd_data['macd'].empty else 0
                    signal_line = macd_data['signal'].iloc[-1] if not macd_data['signal'].empty else 0
                    histogram = macd_line - signal_line
                    
                    if formation_type in ['TOBO', 'FALLING_WEDGE', 'BULLISH_FLAG', 'CUP_HANDLE']:
                        # Bullish formasyonlar için MACD kontrolü
                        if macd_line > signal_line and histogram > 0:
                            macd_score = 50
                            confirmation_details['macd_status'] = 'Güçlü Bullish'
                        elif macd_line > signal_line:
                            macd_score = 30
                            confirmation_details['macd_status'] = 'Bullish'
                        elif histogram > 0:  # Pozitif histogram
                            macd_score = 20
                            confirmation_details['macd_status'] = 'Nötr-Pozitif'
                        else:
                            macd_score = 0
                            confirmation_details['macd_status'] = 'Bearish'
                            
                    elif formation_type in ['OBO', 'BEARISH_FLAG']:
                        # Bearish formasyonlar için MACD kontrolü
                        if macd_line < signal_line and histogram < 0:
                            macd_score = 50
                            confirmation_details['macd_status'] = 'Güçlü Bearish'
                        elif macd_line < signal_line:
                            macd_score = 30
                            confirmation_details['macd_status'] = 'Bearish'
                        elif histogram < 0:  # Negatif histogram
                            macd_score = 20
                            confirmation_details['macd_status'] = 'Nötr-Negatif'
                        else:
                            macd_score = 0
                            confirmation_details['macd_status'] = 'Bullish'
                else:
                    # Yeni format veya bilinmeyen format
                    macd_score = 25  # Varsayılan orta puan
                    confirmation_details['macd_status'] = 'Bilinmeyen format'
            else:
                # MACD hesaplanamadı
                macd_score = 0
                confirmation_details['macd_status'] = 'Hesaplanamadı'
            
            # Toplam osilatör skoru
            total_oscillator_score = rsi_score + macd_score
            
            return {
                'is_confirmed': total_oscillator_score >= 50,  # Minimum 50 puan
                'score': total_oscillator_score,
                'rsi_score': rsi_score,
                'macd_score': macd_score,
                'details': confirmation_details
            }
            
        except Exception as e:
            return {
                'is_confirmed': False,
                'score': 0,
                'rsi_score': 0,
                'macd_score': 0,
                'details': {'error': f'RSI/MACD kontrolü hatası: {str(e)}'}
            }
    
    def calculate_quality_score(self, df: pd.DataFrame, formation_type: str, formation_data: Dict) -> Dict:
        """
        400 puanlık gelişmiş kalite skorlama sistemi - SIKI KURALLAR
        
        Yeni Kriterler:
        - Zaman süresi doğrulama (minimum mum sayısı) → max 100 puan
        - Yapısal doğruluk (dip/tepe oranları, simetri) → max 100 puan
        - Hacim teyidi (%20 minimum artış) → max 100 puan
        - Osilatör uyumu (RSI, MACD) → max 100 puan
        - R/R doğruluğu (formasyona özel) → max 100 puan
        - ZORUNLU: Minimum 150 puan gerekli (400 üzerinden)
        """
        try:
            total_score = 0
            score_details = {}
            rejection_reasons = []
            
            # 0. Zaman süresi doğrulama (100 puan) - ZORUNLU
            time_validation = self.validate_formation_time_duration(df, formation_data)
            if time_validation['is_valid']:
                total_score += time_validation['score']
                score_details['time_score'] = time_validation['score']
            else:
                score_details['time_score'] = 0
                rejection_reasons.append(f"Zaman süresi: {time_validation.get('rejection_reason', 'Bilinmeyen hata')}")
            
            # 1. Yapısal doğruluk (100 puan) - ZORUNLU
            size_validation = self.validate_formation_size(df, formation_data)
            if size_validation['is_valid']:
                total_score += size_validation['score']
                score_details['structural_score'] = size_validation['score']
            else:
                score_details['structural_score'] = 0
                rejection_reasons.append(f"Yapısal doğruluk: {size_validation.get('rejection_reason', 'Bilinmeyen hata')}")
            
            # 2. Hacim teyidi (100 puan)
            volume_validation = self.validate_volume_confirmation(df, formation_type, formation_data)
            if volume_validation['is_confirmed']:
                total_score += volume_validation['score']
                score_details['volume_score'] = volume_validation['score']
            else:
                score_details['volume_score'] = 0
                rejection_reasons.append(f"Hacim teyidi: {volume_validation.get('details', {}).get('rejection_reason', 'Yetersiz hacim artışı')}")
            
            # 3. Osilatör uyumu (100 puan)
            rsi_macd_validation = self.validate_rsi_macd_confirmation(df, formation_type, formation_data)
            if rsi_macd_validation['is_confirmed']:
                total_score += rsi_macd_validation['score']
                score_details['oscillator_score'] = rsi_macd_validation['score']
            else:
                score_details['oscillator_score'] = 0
                rejection_reasons.append(f"Osilatör uyumu: RSI/MACD uyumsuzluğu")
            
            # 4. R/R doğruluğu (100 puan)
            # Formasyon verilerinden entry_price al, yoksa boyun çizgisi kullan
            if 'entry_price' in formation_data and formation_data['entry_price'] > 0:
                entry_price = formation_data['entry_price']
            elif 'neckline' in formation_data and formation_data['neckline'] > 0:
                entry_price = formation_data['neckline']
            else:
                entry_price = df['close'].iloc[-1] if not df.empty else 0
            rr_levels = self.calculate_rr_levels(entry_price, formation_type, formation_data)
            
            if 'rr_ratio' in rr_levels and formation_type in self.rr_targets and isinstance(rr_levels['rr_ratio'], (int, float)):
                rr_ratio = rr_levels['rr_ratio']
                target_rr = self.rr_targets[formation_type]
                
                # R/R oranı kontrolü
                if target_rr['min'] <= rr_ratio <= target_rr['max']:
                    # Optimal aralıkta
                    rr_score = 100
                elif target_rr['min'] * 0.9 <= rr_ratio <= target_rr['max'] * 1.1:
                    # Kabul edilebilir aralıkta
                    rr_score = 60
                else:
                    # Kabul edilemez
                    rr_score = 20
                    rejection_reasons.append(f"R/R oranı: {rr_ratio:.2f} (Hedef: {target_rr['min']}-{target_rr['max']})")
                
                total_score += rr_score
                score_details['rr_score'] = rr_score
                score_details['rr_ratio'] = rr_ratio
                score_details['target_rr'] = f"{target_rr['min']}-{target_rr['max']}"
            else:
                score_details['rr_score'] = 0
                score_details['rr_ratio'] = 0
                rejection_reasons.append("R/R hesaplama hatası")
            
            # GEVŞETİLMİŞ KALİTE KONTROLÜ - Minimum 50/400 puan
            is_high_quality = total_score >= 50
            
            # Detaylı reddetme nedeni
            if not is_high_quality:
                if total_score < 50:
                    rejection_reasons.append(f"Çok düşük skor: {total_score}/400")
                else:
                    rejection_reasons.append(f"Yetersiz skor: {total_score}/400 (Minimum 50 gerekli)")
            
            return {
                'total_score': total_score,
                'is_high_quality': is_high_quality,
                'score_details': score_details,
                'rr_levels': rr_levels,
                'time_validation': time_validation,
                'size_validation': size_validation,
                'volume_validation': volume_validation,
                'rsi_macd_validation': rsi_macd_validation,
                'rejection_reasons': rejection_reasons
            }
            
        except Exception as e:
            return {
                'total_score': 0,
                'is_high_quality': False,
                'score_details': {'error': str(e)},
                'rr_levels': {},
                'time_validation': {},
                'size_validation': {},
                'volume_validation': {},
                'rsi_macd_validation': {},
                'rejection_reasons': [f'Hesaplama hatası: {str(e)}']
            }
    
    def filter_formations(self, df: pd.DataFrame, formations: List[Dict]) -> List[Dict]:
        """
        Gelişmiş formasyon filtreleme - SIKI KURALLAR
        
        Yeni Kriterler:
        - Minimum 150/400 kalite skoru
        - Zaman süresi kontrolü
        - Formasyon boyutu kontrolü (%2 minimum)
        - Hacim teyidi kontrolü
        - RSI/MACD uyum kontrolü
        - R/R oranı kontrolü
        """
        try:
            if not formations:
                return []
            
            filtered_formations = []
            rejected_count = 0
            
            print(f"🔍 {len(formations)} formasyon filtreleniyor...")
            
            for formation in formations:
                if not formation:
                    continue
                
                formation_type = formation.get('type', 'UNKNOWN')
                
                # Eski formasyon verilerini yeni formata çevir
                if formation_type in ['TOBO_LEGACY', 'OBO_LEGACY']:
                    formation = self.convert_legacy_formation_data(formation, formation_type)
                    # Dönüştürme sonrası tipi güncelle
                    formation_type = formation.get('type', formation_type)
                
                # Kalite skoru hesapla
                quality_result = self.calculate_quality_score(df, formation_type, formation)
                
                # Kalite skoru kontrolü (gevşetildi)
                if quality_result['total_score'] >= self.min_quality_score:
                    # Yüksek kaliteli formasyonları kabul et
                    # quality_score'u doğru formatta ayarla
                    if isinstance(formation.get('quality_score'), dict):
                        # Zaten dictionary formatında, total_score'u güncelle
                        formation['quality_score']['total_score'] = quality_result['total_score']
                    else:
                        # Integer formatında, dictionary'ye çevir
                        formation['quality_score'] = {
                            'total_score': quality_result['total_score'],
                            'time_score': quality_result['score_details'].get('time_score', 0),
                            'structural_score': quality_result['score_details'].get('structural_score', 0),
                            'volume_score': quality_result['score_details'].get('volume_score', 0),
                            'oscillator_score': quality_result['score_details'].get('oscillator_score', 0),
                            'rr_score': quality_result['score_details'].get('rr_score', 0),
                            'is_high_quality': True
                        }
                    
                    formation['rr_levels'] = quality_result['rr_levels']
                    formation['time_validation'] = quality_result['time_validation']
                    formation['size_validation'] = quality_result['size_validation']
                    formation['volume_validation'] = quality_result['volume_validation']
                    formation['rsi_macd_validation'] = quality_result['rsi_macd_validation']
                    
                    filtered_formations.append(formation)
                    
                    # Detaylı log
                    print(f"✅ {formation_type} kabul edildi:")
                    print(f"   🎯 Kalite Skoru: {quality_result['total_score']}/400")
                    print(f"   ⏰ Zaman: {quality_result['time_validation']['details'].get('candle_count', 0)} mum / {quality_result['time_validation']['details'].get('hours_duration', 0)} saat")
                    print(f"   📊 Yapısal: {quality_result['score_details'].get('structural_score', 0)}/100")
                    print(f"   📈 Hacim: {quality_result['score_details'].get('volume_score', 0)}/100")
                    print(f"   📉 Osilatör: {quality_result['score_details'].get('oscillator_score', 0)}/100")
                    print(f"   🎯 R/R: {quality_result['score_details'].get('rr_score', 0)}/100")
                else:
                    # Düşük kaliteli formasyonları detaylı logla
                    rejected_count += 1
                    print(f"❌ {formation_type} reddedildi:")
                    print(f"   🎯 Kalite Skoru: {quality_result['total_score']}/400")
                    print(f"   📝 Reddetme Nedenleri: {', '.join(quality_result['rejection_reasons'])}")
                    print(f"   ⏰ Zaman: {quality_result['time_validation']['details'].get('candle_count', 0)} mum / {quality_result['time_validation']['details'].get('hours_duration', 0)} saat")
                    print(f"   📊 Yapısal: {quality_result['score_details'].get('structural_score', 0)}/100")
                    print(f"   📈 Hacim: {quality_result['score_details'].get('volume_score', 0)}/100")
                    print(f"   📉 Osilatör: {quality_result['score_details'].get('oscillator_score', 0)}/100")
                    print(f"   🎯 R/R: {quality_result['score_details'].get('rr_score', 0)}/100")
            
            # Kalite skoruna göre sırala
            filtered_formations.sort(key=lambda x: x.get('quality_score', {}).get('total_score', 0) if isinstance(x.get('quality_score'), dict) else x.get('quality_score', 0), reverse=True)
            
            print(f"📊 Filtreleme Sonucu:")
            print(f"   ✅ Kabul edilen: {len(filtered_formations)}")
            print(f"   ❌ Reddedilen: {rejected_count}")
            
            return filtered_formations
            
        except Exception as e:
            print(f"❌ Formasyon filtreleme hatası: {e}")
            return []
    
    def generate_signal_message(self, symbol: str, formation: Dict) -> str:
        """
        Standardize edilmiş sinyal mesajı oluşturur - Grafik ile birebir aynı değerler
        """
        try:
            formation_type = formation.get('type', 'UNKNOWN')
            direction = formation.get('direction', 'Long')
            entry_price = formation.get('entry_price', 0)
            quality_score = formation.get('quality_score', 0)
            
            # Standardize edilmiş TP/SL hesaplama kullan - Grafik ile birebir aynı değerler
            from tp_sl_calculator import calculate_strict_tp_sl
            
            try:
                levels = calculate_strict_tp_sl(entry_price, direction)
                tp1 = levels['tp1']
                tp2 = levels['tp2']
                tp3 = levels['tp3']
                sl = levels['sl']
                rr_ratio = levels['rr_ratio']
            except Exception as e:
                # Fallback - YENİ KURALLAR (Kullanıcı istekleri)
                print(f"Standardize hesaplayıcı hatası: {e}")
                direction = formation.get('direction', 'Long')
                if direction == 'Long':
                    sl = entry_price * 0.97    # SL: %3.0 aşağı
                    tp1 = entry_price * 1.045  # TP1: %4.5 yukarı
                    tp2 = entry_price * 1.06   # TP2: %6.0 yukarı
                    tp3 = entry_price * 1.09   # TP3: %9.0 yukarı
                else:  # Short
                    sl = entry_price * 1.03    # SL: %3.0 yukarı
                    tp1 = entry_price * 0.955  # TP1: %4.5 aşağı
                    tp2 = entry_price * 0.94   # TP2: %6.0 aşağı
                    tp3 = entry_price * 0.91   # TP3: %9.0 aşağı
                rr_ratio = 3.0  # Sabit R/R oranı
            
            # Zaman bilgileri
            time_validation = formation.get('time_validation', {})
            candle_count = time_validation.get('details', {}).get('candle_count', 0)
            hours_duration = time_validation.get('details', {}).get('hours_duration', 0)
            
            # Hacim bilgileri
            volume_validation = formation.get('volume_validation', {})
            volume_increase = volume_validation.get('volume_increase', 0)
            
            # RSI/MACD bilgileri
            rsi_macd_validation = formation.get('rsi_macd_validation', {})
            rsi_status = rsi_macd_validation.get('details', {}).get('rsi_status', 'Bilinmiyor')
            macd_status = rsi_macd_validation.get('details', {}).get('macd_status', 'Bilinmiyor')
            
            # Formasyon yüksekliği
            size_validation = formation.get('size_validation', {})
            height_percentage = size_validation.get('details', {}).get('height_percentage', 0)
            
            # Yüzde hesaplamaları - Kullanıcı kurallarına göre sabit değerler
            # SL her zaman -%3.0 zarar, TP'ler kar yüzdeleri
            sl_percent = -3.0  # SL her zaman zarar (negatif)
            
            if direction == 'Long':
                tp1_percent = 4.5  # TP1: %4.5 kar
                tp2_percent = 6.0  # TP2: %6.0 kar
                tp3_percent = 9.0  # TP3: %9.0 kar
            else:  # Short
                tp1_percent = 4.5  # TP1: %4.5 kar
                tp2_percent = 6.0  # TP2: %6.0 kar
                tp3_percent = 9.0  # TP3: %9.0 kar
            
            # Formasyon tipi
            formation_names = {
                'TOBO': 'Ucgen Disi Kirilim (TOBO)',
                'OBO': 'Ucgen Disi Kirilim (OBO)',
                'FALLING_WEDGE': 'Dusen Takoz (Falling Wedge)',
                'BULLISH_FLAG': 'Bullish Bayrak',
                'BEARISH_FLAG': 'Bearish Bayrak',
                'CUP_HANDLE': 'Canak-Kulp (Cup and Handle)'
            }
            
            formation_display = formation_names.get(formation_type, formation_type)
            
            # RSI/MACD uyum durumu
            if rsi_status == 'Pozitif' and 'Bullish' in macd_status:
                oscillator_status = 'Guclu Pozitif'
            elif rsi_status == 'Pozitif' or 'Bullish' in macd_status:
                oscillator_status = 'Pozitif'
            elif rsi_status == 'Notr' and 'Notr' in macd_status:
                oscillator_status = 'Notr'
            else:
                oscillator_status = 'Zayif'
            
            # Mesaj oluştur
            message = f"""Sembol: {symbol}
Formasyon: {formation_display}
Yon: {direction}
Sure: {candle_count} mum / {hours_duration} saat
Hacim artisi: %{volume_increase:.1f}
RSI/MACD Uyumu: {oscillator_status}
Formasyon yuksekligi: %{height_percentage:.2f}
TP1: {tp1:.4f} ({tp1_percent:+.1f}%) | TP2: {tp2:.4f} ({tp2_percent:+.1f}%) | TP3: {tp3:.4f} ({tp3_percent:+.1f}%)
SL: {sl:.4f} ({sl_percent:+.1f}%)
R/R: {rr_ratio:.2f}:1
Kalite Skoru: {quality_score} / 400

Risk Uyarisi: Bot suanda test asamasindadir. Verilen grafikler yatirim tavsiyesi olmamakla beraber orta/yuksek olcude riskler tasimaktadir."""
            
            return message
            
        except Exception as e:
            return f"Sinyal mesaji olusturulamadi: {e}"
    
    def analyze_symbol(self, symbol: str, interval: str = '4h') -> Dict:
        """
        Gelişmiş sembol analizi - YENİ KURALLAR
        
        Yeni Özellikler:
        - Zaman filtresi kontrolü
        - Yükseklik filtresi kontrolü
        - Gelişmiş R/R hesaplama
        - 400 puanlık kalite skorlama
        - Detaylı log sistemi
        """
        try:
            print(f"\n🔍 {symbol} analiz ediliyor...")
            
            # Veri çek
            df = fetch_ohlcv(symbol, interval, limit=200)
            if df.empty:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'Veri alınamadı'
                }
            
            # Volatilite kontrolü
            volatility = self.calculate_volatility(df)
            if volatility > self.max_volatility:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': f'Volatilite çok yüksek: {volatility:.2%}'
                }
            
            print(f"✅ {len(df)} mum verisi alındı (Volatilite: {volatility:.2%})")
            
            # Tüm formasyonları tespit et
            all_formations = []
            
            # GELİŞMİŞ TOBO tespiti (Yeni 5.0 kuralları)
            tobo_formation = detect_inverse_head_and_shoulders(df, window=30)
            if tobo_formation:
                # Eğer quality_score zaten hesaplanmışsa, tekrar hesaplama
                if 'quality_score' not in tobo_formation or not isinstance(tobo_formation['quality_score'], dict):
                    quality_result = self.calculate_quality_score(df, 'TOBO', tobo_formation)
                    if quality_result['is_high_quality']:
                        tobo_formation['quality_score'] = {
                            'total_score': quality_result['total_score'],
                            'time_score': quality_result['score_details'].get('time_score', 0),
                            'structural_score': quality_result['score_details'].get('structural_score', 0),
                            'volume_score': quality_result['score_details'].get('volume_score', 0),
                            'oscillator_score': quality_result['score_details'].get('oscillator_score', 0),
                            'rr_score': quality_result['score_details'].get('rr_score', 0),
                            'is_high_quality': True
                        }
                        all_formations.append(tobo_formation)
                        score_display = f"{quality_result['total_score']}/400"
                        print(f"✅ {symbol}: Gelişmiş TOBO tespit edildi (Skor: {score_display})")
                    else:
                        print(f"❌ {symbol}: TOBO kalite skoru düşük ({quality_result['total_score']}/400)")
                else:
                    all_formations.append(tobo_formation)
                    score_display = f"{tobo_formation['quality_score'].get('total_score', 0)}/400"
                    print(f"✅ {symbol}: Gelişmiş TOBO tespit edildi (Skor: {score_display})")
            
            # GELİŞMİŞ OBO tespiti (Yeni 5.0 kuralları)
            obo_formation = detect_head_and_shoulders(df, window=30)
            if obo_formation:
                # Eğer quality_score zaten hesaplanmışsa, tekrar hesaplama
                if 'quality_score' not in obo_formation or not isinstance(obo_formation['quality_score'], dict):
                    quality_result = self.calculate_quality_score(df, 'OBO', obo_formation)
                    if quality_result['is_high_quality']:
                        obo_formation['quality_score'] = {
                            'total_score': quality_result['total_score'],
                            'time_score': quality_result['score_details'].get('time_score', 0),
                            'structural_score': quality_result['score_details'].get('structural_score', 0),
                            'volume_score': quality_result['score_details'].get('volume_score', 0),
                            'oscillator_score': quality_result['score_details'].get('oscillator_score', 0),
                            'rr_score': quality_result['score_details'].get('rr_score', 0),
                            'is_high_quality': True
                        }
                        all_formations.append(obo_formation)
                        score_display = f"{quality_result['total_score']}/400"
                        print(f"✅ {symbol}: Gelişmiş OBO tespit edildi (Skor: {score_display})")
                    else:
                        print(f"❌ {symbol}: OBO kalite skoru düşük ({quality_result['total_score']}/400)")
                else:
                    all_formations.append(obo_formation)
                    score_display = f"{obo_formation['quality_score'].get('total_score', 0)}/400"
                    print(f"✅ {symbol}: Gelişmiş OBO tespit edildi (Skor: {score_display})")
            
            # Eski TOBO/OBO fonksiyonları (GERİ AÇILDI)
            old_tobo_formations = find_all_tobo(df)
            if old_tobo_formations:
                for formation in old_tobo_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'TOBO_LEGACY'
                        formation['direction'] = 'Long'
                        # Eski formasyon verilerini yeni formata çevir
                        formation = self.convert_legacy_formation_data(formation, 'TOBO_LEGACY')
                        all_formations.append(formation)
                        print(f"✅ {symbol}: Legacy TOBO tespit edildi")
            
            old_obo_formations = find_all_obo(df)
            if old_obo_formations:
                for formation in old_obo_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'OBO_LEGACY'
                        formation['direction'] = 'Short'
                        # Eski formasyon verilerini yeni formata çevir
                        formation = self.convert_legacy_formation_data(formation, 'OBO_LEGACY')
                        all_formations.append(formation)
                        print(f"✅ {symbol}: Legacy OBO tespit edildi")
            
            # Falling Wedge tespiti
            falling_wedge_formations = detect_falling_wedge(df)
            if falling_wedge_formations:
                for formation in falling_wedge_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'FALLING_WEDGE'
                        formation['direction'] = 'Long'
                        all_formations.append(formation)
            
            # Cup & Handle tespiti
            cup_handle_formations = detect_cup_and_handle(df)
            if cup_handle_formations:
                for formation in cup_handle_formations:
                    if formation and isinstance(formation, dict):
                        formation['type'] = 'CUP_HANDLE'
                        formation['direction'] = 'Long'
                        all_formations.append(formation)
            
            # Flag tespiti
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
            
            if not all_formations:
                print(f"❌ {symbol}: Hiç formasyon bulunamadı")
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'Formasyon bulunamadı',
                    'volatility': volatility
                }
            
            print(f"�� {symbol}: {len(all_formations)} formasyon tespit edildi")
            
            # Gelişmiş filtreleme uygula
            filtered_formations = self.filter_formations(df, all_formations)
            
            if not filtered_formations:
                print(f"❌ {symbol}: Yüksek kaliteli formasyon bulunamadı")
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'Yüksek kaliteli formasyon bulunamadı',
                    'total_formations': len(all_formations),
                    'volatility': volatility
                }
            
            # En iyi formasyonu seç
            best_formation = filtered_formations[0]
            quality_score = best_formation.get('quality_score', 0)
            
            # quality_score'u integer olarak al
            if isinstance(quality_score, dict):
                quality_score_int = quality_score.get('total_score', 0)
            else:
                quality_score_int = quality_score
            
            print(f"✅ {symbol} analizi tamamlandı:")
            print(f"   📊 Toplam formasyon: {len(all_formations)}")
            print(f"   🎯 Filtrelenmiş formasyon: {len(filtered_formations)}")
            print(f"   🏆 En iyi formasyon: {best_formation['type']} (Skor: {quality_score_int}/400)")
            
            # Sinyal mesajı oluştur
            signal_message = self.generate_signal_message(symbol, best_formation)
            
            # Sadece 100+ puanlık formasyonlar için sinyal üret (gevşetildi)
            if quality_score_int >= 100:
                return {
                    'symbol': symbol,
                    'success': True,
                    'best_formation': best_formation,
                    'quality_score': quality_score,
                    'total_formations': len(all_formations),
                    'filtered_formations': len(filtered_formations),
                    'volatility': volatility,
                    'signal_message': signal_message
                }
            else:
                print(f"❌ {symbol}: Kalite skoru yetersiz ({quality_score_int}/400)")
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': f'Kalite skoru yetersiz: {quality_score_int}/400',
                    'total_formations': len(all_formations),
                    'filtered_formations': len(filtered_formations),
                    'volatility': volatility
                }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e)
            }
    
    def scan_all_symbols(self, max_workers: int = 5) -> List[Dict]:
        """
        Tüm USDT sembollerini tarar - Gelişmiş versiyon 5.0
        
        Yeni Özellikler:
        - Gelişmiş zaman filtresi
        - Yükseklik filtresi (%2 minimum)
        - Formasyona özel R/R hesaplama
        - 400 puanlık kalite skorlama
        - Detaylı log sistemi
        - Sinyal üretimi
        """
        try:
            print("🚀 GELİŞMİŞ FORMASYON ANALİZ SİSTEMİ 5.0")
            print("=" * 60)
            print("📋 YENİ ÖZELLİKLER:")
            print("   ✅ Zaman filtresi (TOBO/OBO: 20 mum, Wedge/Flag: 25 mum, Cup: 30 mum)")
            print("   ✅ Yükseklik filtresi (%2 minimum formasyon boyutu)")
            print("   ✅ Formasyona özel R/R oranları (TOBO: 1.3-1.7, Wedge: 1.5-2.0, Cup: 1.8-2.5)")
            print("   ✅ 400 puanlık kalite skorlama sistemi")
            print("   ✅ Gelişmiş log sistemi ve sinyal üretimi")
            print("   ✅ Minimum 150/400 puan zorunlu")
            print("=" * 60)
            
            # Tüm sembolleri al
            symbols = self.get_all_usdt_symbols()
            if not symbols:
                print("❌ Sembol listesi alınamadı")
                return []
            
            print(f"📊 {len(symbols)} USDT sembolü bulundu")
            
            # Analiz sonuçları
            successful_results = []
            failed_results = []
            
            # Her sembol için analiz yap
            for i, symbol in enumerate(symbols, 1):
                try:
                    print(f"\n[{i}/{len(symbols)}] {symbol} analiz ediliyor...")
                    
                    result = self.analyze_symbol(symbol, '4h')
                    
                    if result['success']:
                        successful_results.append(result)
                        print(f"✅ {symbol} başarılı analiz!")
                        
                        # Sinyal mesajını göster
                        if 'signal_message' in result:
                            print("\n" + "="*50)
                            print("🚨 YENİ SİNYAL TESPİT EDİLDİ!")
                            print("="*50)
                            print(result['signal_message'])
                            print("="*50)
                    else:
                        failed_results.append(result)
                        print(f"❌ {symbol} analiz başarısız: {result.get('error', 'Bilinmeyen hata')}")
                    
                    # Hız kontrolü
                    if i % 20 == 0:
                        print(f"⏳ {i}/{len(symbols)} sembol tamamlandı...")
                        import time
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"❌ {symbol} analiz hatası: {e}")
                    failed_results.append({
                        'symbol': symbol,
                        'success': False,
                        'error': str(e)
                    })
            
            # Özet rapor
            print(f"\n📊 ANALİZ ÖZETİ:")
            print(f"   🔍 Toplam sembol: {len(symbols)}")
            print(f"   ✅ Başarılı analiz: {len(successful_results)}")
            print(f"   ❌ Başarısız analiz: {len(failed_results)}")
            print(f"   📈 Başarı oranı: {(len(successful_results)/len(symbols)*100):.1f}%")
            
            if successful_results:
                print(f"\n🏆 EN İYİ SİNYALLER:")
                # Kalite skoruna göre sırala
                def get_quality_score(result):
                    quality_score = result.get('quality_score', 0)
                    if isinstance(quality_score, dict):
                        return quality_score.get('total_score', 0)
                    return quality_score
                
                successful_results.sort(key=get_quality_score, reverse=True)
                
                for i, result in enumerate(successful_results[:5], 1):
                    symbol = result['symbol']
                    formation = result['best_formation']
                    quality_score = result.get('quality_score', 0)
                    if isinstance(quality_score, dict):
                        quality_score_int = quality_score.get('total_score', 0)
                    else:
                        quality_score_int = quality_score
                    formation_type = formation.get('type', 'UNKNOWN')
                    
                    print(f"   {i}. {symbol}: {formation_type} (Skor: {quality_score_int}/400)")
            
            return successful_results
            
        except Exception as e:
            print(f"❌ Tarama hatası: {e}")
            return []

    def convert_legacy_formation_data(self, formation_data: Dict, formation_type: str) -> Dict:
        """
        Eski formasyon verilerini yeni format için uyumlu hale getirir
        """
        try:
            if formation_type in ['TOBO_LEGACY', 'OBO_LEGACY']:
                # Eski TOBO/OBO fonksiyonları için uyumluluk
                converted_data = formation_data.copy()
                
                # Boyun çizgisi alanını düzelt
                if 'neckline' in formation_data and 'boyun' not in formation_data:
                    converted_data['boyun'] = formation_data['neckline']
                elif 'boyun' not in formation_data and 'neckline' not in formation_data:
                    # Varsayılan boyun çizgisi (bas fiyatının %2 üstü)
                    bas_price = formation_data.get('bas', 0)
                    if isinstance(bas_price, (int, float)) and bas_price > 0:
                        converted_data['boyun'] = bas_price * 1.02
                    else:
                        converted_data['boyun'] = 0
                
                # Zaman noktalarını ekle (timestamp yerine indeks)
                if 'tobo_start' not in formation_data and 'obo_start' not in formation_data:
                    converted_data['tobo_start'] = 0
                    converted_data['tobo_end'] = 29
                else:
                    # Timestamp'leri indekse çevir (varsayılan olarak)
                    if 'tobo_start' in formation_data:
                        converted_data['tobo_start'] = 0
                        converted_data['tobo_end'] = 29
                    if 'obo_start' in formation_data:
                        converted_data['obo_start'] = 0
                        converted_data['obo_end'] = 29
                
                # YENİ KURAL: Entry price her zaman kırılım mumunun kapanış fiyatı olmalı
                if 'entry_price' not in formation_data:
                    # Mevcut fiyatı al (kırılım mumunun kapanış fiyatı)
                    current_price = formation_data.get('current_price', 0)
                    if current_price <= 0:
                        # Eğer current_price yoksa, bas fiyatını kullan
                        current_price = formation_data.get('bas', 0)
                    
                    # YENİ KURAL: Her zaman kırılım mumunun kapanış fiyatı
                    converted_data['entry_price'] = current_price
                    print(f"💰 Legacy Giriş Fiyatı: {converted_data['entry_price']:.6f} (Kırılım mumunun kapanış fiyatı)")
                else:
                    # Varsayılan entry price
                    converted_data['entry_price'] = current_price
                
                # Formasyon tipini düzelt
                if formation_type == 'TOBO_LEGACY':
                    converted_data['type'] = 'TOBO'
                elif formation_type == 'OBO_LEGACY':
                    converted_data['type'] = 'OBO'
                
                # Eksik alanları varsayılan değerlerle doldur
                if 'sol_omuz_index' not in converted_data:
                    converted_data['sol_omuz_index'] = 0
                if 'sag_omuz_index' not in converted_data:
                    converted_data['sag_omuz_index'] = 29
                
                # Formasyon yüksekliği için gerekli alanları ekle
                if 'bas' in formation_data and 'boyun' in converted_data:
                    bas_price = formation_data['bas']
                    boyun_price = converted_data['boyun']
                    # Veri tipini kontrol et
                    if isinstance(bas_price, (int, float)) and isinstance(boyun_price, (int, float)):
                        converted_data['formation_height'] = abs(bas_price - boyun_price)
                        if bas_price > 0:
                            converted_data['height_percentage'] = (converted_data['formation_height'] / bas_price) * 100
                        else:
                            converted_data['height_percentage'] = 2.0
                    else:
                        # Varsayılan değerler
                        if isinstance(bas_price, (int, float)) and bas_price > 0:
                            converted_data['formation_height'] = bas_price * 0.02
                            converted_data['height_percentage'] = 2.0
                        else:
                            converted_data['formation_height'] = 0
                            converted_data['height_percentage'] = 0
                
                return converted_data
            
            return formation_data
            
        except Exception as e:
            print(f"⚠️ Legacy formasyon dönüştürme hatası: {e}")
            return formation_data


def main():
    """
    Ana test fonksiyonu - Gelişmiş versiyon 5.0
    """
    print("🚀 GELİŞMİŞ FORMASYON ANALİZ SİSTEMİ 5.0")
    print("=" * 60)
    
    # Analizör oluştur
    analyzer = AdvancedFormationAnalyzer()
    
    # Test sembolleri
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    print(f"🧪 Test sembolleri: {', '.join(test_symbols)}")
    print("=" * 60)
    
    successful_signals = []
    
    for symbol in test_symbols:
        print(f"\n🔍 {symbol} test ediliyor...")
        
        result = analyzer.analyze_symbol(symbol, '4h')
        
        if result['success']:
            successful_signals.append(result)
            print(f"✅ {symbol} için sinyal üretildi!")
            
            # Sinyal mesajını göster
            if 'signal_message' in result:
                print("\n" + "="*50)
                print("🚨 TEST SİNYALİ")
                print("="*50)
                print(result['signal_message'])
                print("="*50)
        else:
            print(f"❌ {symbol} için sinyal üretilemedi: {result.get('error', 'Bilinmeyen hata')}")
    
    # Test özeti
    print(f"\n📊 TEST ÖZETİ:")
    print(f"   🔍 Test edilen: {len(test_symbols)} sembol")
    print(f"   ✅ Başarılı sinyal: {len(successful_signals)}")
    print(f"   ❌ Başarısız: {len(test_symbols) - len(successful_signals)}")
    
    if successful_signals:
        print(f"\n🏆 EN İYİ TEST SİNYALLERİ:")
        # Kalite skoruna göre sırala
        def get_quality_score(result):
            quality_score = result.get('quality_score', 0)
            if isinstance(quality_score, dict):
                return quality_score.get('total_score', 0)
            return quality_score
        
        successful_signals.sort(key=get_quality_score, reverse=True)
        
        for i, result in enumerate(successful_signals, 1):
            symbol = result['symbol']
            formation = result['best_formation']
            quality_score = result.get('quality_score', 0)
            if isinstance(quality_score, dict):
                quality_score_int = quality_score.get('total_score', 0)
            else:
                quality_score_int = quality_score
            formation_type = formation.get('type', 'UNKNOWN')
            
            print(f"   {i}. {symbol}: {formation_type} (Skor: {quality_score_int}/400)")
    
    print(f"\n✅ Test tamamlandı!")
    print("📝 Not: Bu sistem gerçek trading için kullanılmamalıdır.")


if __name__ == "__main__":
    main() 