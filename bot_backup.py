# bot.py

from data_fetcher import fetch_ohlcv
from formation_detector import detect_formations, calculate_fibonacci_levels, detect_rsi_divergence, find_all_tobo, find_all_obo, detect_cup_and_handle, detect_falling_wedge, calculate_macd, calculate_bollinger_bands, calculate_stochastic, calculate_adx, analyze_all_formations, analyze_all_formations_advanced
from rsi_detector import check_rsi
from telegram_notifier import send_telegram_message
from user_manager import generate_user_key, check_key_validity
import requests
import msvcrt
import pandas as pd


def get_current_price(symbol):
    """
    Binance Futures API'dan anlık fiyatı çeker.
    """
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['price']) if 'price' in data else None


def format_price(price):
    if price == 0:
        return '0'
    elif price < 0.0001:
        return f"{price:.8f}"
    elif price < 1:
        return f"{price:.6f}"
    elif price < 10:
        return f"{price:.4f}"
    elif price < 100:
        return f"{price:.3f}"
    else:
        return f"{price:.2f}"


def check_neckline_breakout(symbol, neckline_price, direction, timeframes=['4h', '1d']):
    """
    4H ve 1D grafiklerde boyun çizgisi kırılımını kontrol eder
    """
    breakout_info = {}
    
    for timeframe in timeframes:
        try:
            df = fetch_ohlcv(symbol, timeframe)
            if df is None or df.empty:
                continue
                
            # Son 5 mumu kontrol et
            recent_candles = df.tail(5) if hasattr(df, 'tail') else df[-5:]
            current_price = df['close'].iloc[-1] if hasattr(df['close'], 'iloc') else df['close'][-1]
            
            # Hacim analizi
            avg_volume = df['volume'].tail(20).mean() if hasattr(df['volume'], 'tail') else df['volume'][-20:].mean()
            current_volume = df['volume'].iloc[-1] if hasattr(df['volume'], 'iloc') else df['volume'][-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Kırılım kontrolü
            breakout_confirmed = False
            breakout_strength = 0
            
            if direction == 'Long':  # TOBO - yukarı kırılım
                # Fiyat boyun çizgisinin üstünde mi?
                if current_price > neckline_price:
                    # Son 3 mumda kırılım var mı?
                    candles_above = sum(1 for price in recent_candles['close'] if price > neckline_price)
                    if candles_above >= 2:  # En az 2 mum üstte
                        breakout_confirmed = True
                        breakout_strength = (current_price - neckline_price) / neckline_price * 100
            else:  # OBO - aşağı kırılım
                # Fiyat boyun çizgisinin altında mı?
                if current_price < neckline_price:
                    # Son 3 mumda kırılım var mı?
                    candles_below = sum(1 for price in recent_candles['close'] if price < neckline_price)
                    if candles_below >= 2:  # En az 2 mum altta
                        breakout_confirmed = True
                        breakout_strength = (neckline_price - current_price) / neckline_price * 100
            
            breakout_info[timeframe] = {
                'confirmed': breakout_confirmed,
                'strength': breakout_strength,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_confirmed': volume_ratio > 1.5,  # Hacim 1.5x üstünde
                'neckline_price': neckline_price
            }
            
        except Exception as e:
            print(f"❌ {timeframe} analizi hatası: {e}")
            continue
    
    return breakout_info


def analyze_volume_confirmation(symbol, timeframes=['4h', '1d']):
    """
    Hacim teyidi analizi
    """
    volume_analysis = {}
    
    for timeframe in timeframes:
        try:
            df = fetch_ohlcv(symbol, timeframe)
            if df is None or df.empty:
                continue
            
            # Son 20 mumun ortalama hacmi
            avg_volume = df['volume'].tail(20).mean() if hasattr(df['volume'], 'tail') else df['volume'][-20:].mean()
            current_volume = df['volume'].iloc[-1] if hasattr(df['volume'], 'iloc') else df['volume'][-1]
            
            # Hacim trendi (son 5 mum)
            recent_volumes = df['volume'].tail(5) if hasattr(df['volume'], 'tail') else df['volume'][-5:]
            try:
                volume_trend = 'Yükselen' if recent_volumes.iloc[-1] > recent_volumes.iloc[0] else 'Düşen'
            except:
                volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
            
            # Hacim teyidi
            volume_confirmed = current_volume > avg_volume * 1.5  # 1.5x üstünde
            
            volume_analysis[timeframe] = {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                'volume_trend': volume_trend,
                'confirmed': volume_confirmed
            }
            
        except Exception as e:
            print(f"❌ {timeframe} hacim analizi hatası: {e}")
            continue
    
    return volume_analysis


def calculate_optimal_risk(symbol, current_price, tp, sl, direction):
    """ISOLATED işlemler için sabit 5x kaldıraç ile risk seviyesini hesapla"""
    
    # Pozisyon geçerliliği kontrolü
    if direction == 'Long':
        # Long pozisyon için: TP > Entry > SL
        if not (tp > current_price > sl):
            return {
                'risk_level': 'Geçersiz',
                'leverage': '5x',
                'position_size': 'Kasanın %5\'i',
                'risk_reward': '0.0:1',
                'potential_gain': '%0.0',
                'margin_type': 'ISOLATED',
                'risk_amount': '%0.0',
                'max_loss': '%0.0',
                'valid': False,
                'reason': 'Geçersiz pozisyon: Long için TP > Entry > SL olmalı'
            }
        # R/R = (TP - Entry) / (Entry - SL)
        risk_reward_ratio = (tp - current_price) / (current_price - sl) if (current_price - sl) > 0 else 0
        risk_percent = (current_price - sl) / current_price
        reward_percent = (tp - current_price) / current_price
    else:
        # Short pozisyon için: TP < Entry < SL
        if not (tp < current_price < sl):
            return {
                'risk_level': 'Geçersiz',
                'leverage': '5x',
                'position_size': 'Kasanın %5\'i',
                'risk_reward': '0.0:1',
                'potential_gain': '%0.0',
                'margin_type': 'ISOLATED',
                'risk_amount': '%0.0',
                'max_loss': '%0.0',
                'valid': False,
                'reason': 'Geçersiz pozisyon: Short için TP < Entry < SL olmalı'
            }
        # R/R = (Entry - TP) / (SL - Entry)
        risk_reward_ratio = (current_price - tp) / (sl - current_price) if (sl - current_price) > 0 else 0
        risk_percent = (sl - current_price) / current_price
        reward_percent = (current_price - tp) / current_price
    
    # R/R oranı kontrolü - Daha esnek (botanlik.py gibi)
    if risk_reward_ratio < 0.8:
        return {
            'risk_level': 'Yetersiz R/R',
            'leverage': '5x',
            'position_size': 'Kasanın %5\'i',
            'risk_reward': f'{risk_reward_ratio:.2f}:1',
            'potential_gain': f'%{reward_percent*5*100:.1f}',
            'margin_type': 'ISOLATED',
            'risk_amount': f'%{risk_percent*5*100:.1f}',
            'max_loss': f'%{risk_percent*5*100:.1f}',
            'valid': False,
            'reason': f'Yetersiz Risk/Ödül oranı: {risk_reward_ratio:.2f}:1 (Minimum 0.8:1 gerekli)'
        }
    
    return {
        'risk_level': 'Sabit 5x',
        'leverage': '5x',
        'position_size': 'Kasanın %5\'i',
        'risk_reward': f'{risk_reward_ratio:.2f}:1',
        'potential_gain': f'%{reward_percent*5*100:.1f}',
        'margin_type': 'ISOLATED',
        'risk_amount': f'%{risk_percent*5*100:.1f}',
        'max_loss': f'%{risk_percent*5*100:.1f}',
        'valid': True,
        'reason': f'Geçerli sinyal: R/R = {risk_reward_ratio:.2f}:1'
    }

def determine_best_signal(tobo_signal, obo_signal, cup_handle_signal, falling_wedge_signal, rsi_signal, current_price):
    """En iyi sinyali belirle"""
    signals = []
    
    # TOBO sinyali varsa ekle
    if tobo_signal and tobo_signal.get('valid', False):
        # Risk/Ödül oranını hesapla
        entry = tobo_signal['entry']
        tp = tobo_signal['tp']
        sl = tobo_signal['sl']
        # Long için: R/R = (TP - Entry) / (Entry - SL)
        risk_reward_ratio = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
        
        signals.append({
            'type': 'TOBO',
            'direction': 'Long',
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'risk_analysis': tobo_signal['risk_analysis'],
            'score': risk_reward_ratio
        })
    
    # OBO sinyali varsa ekle
    if obo_signal and obo_signal.get('valid', False):
        # Risk/Ödül oranını hesapla
        entry = obo_signal['entry']
        tp = obo_signal['tp']
        sl = obo_signal['sl']
        # Short için: R/R = (Entry - TP) / (SL - Entry)
        risk_reward_ratio = (entry - tp) / (sl - entry) if (sl - entry) > 0 else 0
        
        signals.append({
            'type': 'OBO',
            'direction': 'Short',
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'risk_analysis': obo_signal['risk_analysis'],
            'score': risk_reward_ratio
        })
    
    # Cup and Handle sinyali varsa ekle
    if cup_handle_signal and cup_handle_signal.get('valid', False):
        # Risk/Ödül oranını hesapla
        entry = cup_handle_signal['entry']
        tp = cup_handle_signal['tp']
        sl = cup_handle_signal['sl']
        # Long için: R/R = (TP - Entry) / (Entry - SL)
        risk_reward_ratio = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
        
        signals.append({
            'type': 'CUP_HANDLE',
            'direction': 'Long',
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'risk_analysis': cup_handle_signal['risk_analysis'],
            'score': risk_reward_ratio
        })
    
    # Falling Wedge sinyali varsa ekle
    if falling_wedge_signal and falling_wedge_signal.get('valid', False):
        # Risk/Ödül oranını hesapla
        entry = falling_wedge_signal['entry']
        tp = falling_wedge_signal['tp']
        sl = falling_wedge_signal['sl']
        # Long için: R/R = (TP - Entry) / (Entry - SL)
        risk_reward_ratio = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
        
        signals.append({
            'type': 'FALLING_WEDGE',
            'direction': 'Long',
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'risk_analysis': falling_wedge_signal['risk_analysis'],
            'score': risk_reward_ratio
        })
    
    # RSI sinyali varsa ekle
    if rsi_signal and rsi_signal.get('valid', False):
        # Risk/Ödül oranını hesapla
        entry = rsi_signal['entry']
        tp = rsi_signal['tp']
        sl = rsi_signal['sl']
        # Long için: R/R = (TP - Entry) / (Entry - SL)
        risk_reward_ratio = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
        
        signals.append({
            'type': 'RSI',
            'direction': 'Long',
            'entry': entry,
            'tp': tp,
            'sl': sl,
            'risk_analysis': rsi_signal['risk_analysis'],
            'score': risk_reward_ratio
        })
    
    if not signals:
        return None
    
    # En yüksek skora sahip sinyali seç (Daha esnek - botanlik.py gibi)
    # R/R 0.8:1'den yüksek olanları filtrele
    valid_signals = [s for s in signals if s['score'] >= 0.8]
    
    if not valid_signals:
        # Eğer 0.8:1'den yüksek sinyal yoksa, en yüksek skorlu sinyali al
        valid_signals = signals
    
    best_signal = max(valid_signals, key=lambda x: x['score'])
    
    # Sebep açıklaması
    if best_signal['type'] == 'TOBO':
        reason = "En iyi risk/ödül oranı ve yükseliş trendi"
    elif best_signal['type'] == 'OBO':
        reason = "En iyi risk/ödül oranı ve düşüş trendi"
    elif best_signal['type'] == 'CUP_HANDLE':
        reason = "Cup and Handle formasyonu kırılımı"
    elif best_signal['type'] == 'FALLING_WEDGE':
        reason = "Falling Wedge formasyonu kırılımı"
    else:
        reason = "RSI aşırı satım sinyali"
    
    return {
        'type': best_signal['type'],
        'direction': best_signal['direction'],
        'entry': best_signal['entry'],
        'tp': best_signal['tp'],
        'sl': best_signal['sl'],
        'risk_level': best_signal['risk_analysis']['risk_level'],
        'leverage': best_signal['risk_analysis']['leverage'],
        'position_size': best_signal['risk_analysis']['position_size'],
        'risk_reward': best_signal['risk_analysis']['risk_reward'],
        'potential_gain': best_signal['risk_analysis']['potential_gain'],
        'margin_type': best_signal['risk_analysis']['margin_type'],
        'risk_amount': best_signal['risk_analysis']['risk_amount'],
        'max_loss': best_signal['risk_analysis']['max_loss'],
        'reason': reason
    }


def calculate_signal_score(df, formation_type, formation_data, macd_data, bb_data, stoch_data, adx_data, ma_trend):
    """
    Sinyal ağırlıklandırma sistemi - Çelişkileri çözer (botanlik.py ile aynı)
    """
    total_score = 0
    max_score = 100
    signals = []

    # 1. Formasyon Ağırlığı (40 puan)
    if formation_type == 'TOBO':
        formation_score = 40
        signals.append(f"TOBO Formasyonu: +{formation_score}")
    elif formation_type == 'OBO':
        formation_score = 40
        signals.append(f"OBO Formasyonu: +{formation_score}")
    else:
        formation_score = 0
    total_score += formation_score

    # 2. MA Trend Ağırlığı (20 puan)
    if 'Yükseliş' in ma_trend:
        ma_score = 20
        ma_signal = 'Long'
        signals.append(f"MA Trend (Yükseliş): +{ma_score}")
    elif 'Düşüş' in ma_trend:
        ma_score = 20
        ma_signal = 'Short'
        signals.append(f"MA Trend (Düşüş): +{ma_score}")
    else:
        ma_score = 0
        ma_signal = 'Neutral'
    total_score += ma_score

    # 3. MACD Ağırlığı (15 puan)
    if macd_data:
        if macd_data['trend'] == 'Bullish':
            macd_score = 15
            macd_signal = 'Long'
            signals.append(f"MACD (Bullish): +{macd_score}")
        else:
            macd_score = 15
            macd_signal = 'Short'
            signals.append(f"MACD (Bearish): +{macd_score}")
    else:
        macd_score = 0
        macd_signal = 'Neutral'
    total_score += macd_score

    # 4. ADX Ağırlığı (10 puan)
    if adx_data:
        if adx_data['trend_direction'] == 'Bullish':
            adx_score = 10
            adx_signal = 'Long'
            signals.append(f"ADX (Bullish): +{adx_score}")
        else:
            adx_score = 10
            adx_signal = 'Short'
            signals.append(f"ADX (Bearish): +{adx_score}")
    else:
        adx_score = 0
        adx_signal = 'Neutral'
    total_score += adx_score

    # 5. Bollinger Bands Ağırlığı (10 puan)
    if bb_data:
        if bb_data['signal'] == 'Oversold':
            bb_score = 10
            bb_signal = 'Long'
            signals.append(f"Bollinger (Oversold): +{bb_score}")
        elif bb_data['signal'] == 'Overbought':
            bb_score = 10
            bb_signal = 'Short'
            signals.append(f"Bollinger (Overbought): +{bb_score}")
        else:
            bb_score = 0
            bb_signal = 'Neutral'
    else:
        bb_score = 0
        bb_signal = 'Neutral'
    total_score += bb_score

    # 6. Stochastic Ağırlığı (5 puan)
    if stoch_data:
        if stoch_data['signal'] == 'Oversold':
            stoch_score = 5
            stoch_signal = 'Long'
            signals.append(f"Stochastic (Oversold): +{stoch_score}")
        elif stoch_data['signal'] == 'Overbought':
            stoch_score = 5
            stoch_signal = 'Short'
            signals.append(f"Stochastic (Overbought): +{stoch_score}")
        else:
            stoch_score = 0
            stoch_signal = 'Neutral'
    else:
        stoch_score = 0
        stoch_signal = 'Neutral'
    total_score += stoch_score

    # Sinyal yönü belirleme
    long_signals = sum(1 for signal in [ma_signal, macd_signal, adx_signal, bb_signal, stoch_signal] if signal == 'Long')
    short_signals = sum(1 for signal in [ma_signal, macd_signal, adx_signal, bb_signal, stoch_signal] if signal == 'Short')

    # Formasyon yönü
    formation_signal = 'Long' if formation_type == 'TOBO' else 'Short' if formation_type == 'OBO' else 'Neutral'

    # Genel sinyal yönü
    if formation_signal == 'Long':
        long_signals += 1
    elif formation_signal == 'Short':
        short_signals += 1

    # Çelişki analizi
    total_indicators = 6  # Formasyon + 5 indikatör
    long_percentage = (long_signals / total_indicators) * 100
    short_percentage = (short_signals / total_indicators) * 100

    # Final sinyal belirleme (botanlik.py ile aynı)
    if long_percentage >= 70:
        final_signal = 'Long'
        confidence = 'Yüksek'
    elif short_percentage >= 70:
        final_signal = 'Short'
        confidence = 'Yüksek'
    elif long_percentage >= 60:
        final_signal = 'Long'
        confidence = 'Orta'
    elif short_percentage >= 60:
        final_signal = 'Short'
        confidence = 'Orta'
    else:
        final_signal = 'Bekleme'
        confidence = 'Düşük'

    # Çelişki durumu
    if abs(long_percentage - short_percentage) < 20:
        conflict = 'Yüksek Çelişki'
    elif abs(long_percentage - short_percentage) < 40:
        conflict = 'Orta Çelişki'
    else:
        conflict = 'Düşük Çelişki'

    return {
        'total_score': total_score,
        'max_score': max_score,
        'long_percentage': long_percentage,
        'short_percentage': short_percentage,
        'final_signal': final_signal,
        'confidence': confidence,
        'conflict': conflict,
        'signals': signals,
        'formation_signal': formation_signal,
        'indicator_signals': {
            'ma': ma_signal,
            'macd': macd_signal,
            'adx': adx_signal,
            'bb': bb_signal,
            'stoch': stoch_signal
        }
    }


def analyze_trading_scenarios(df, formation_type, formation_data, current_price, fibo_levels, bb_data, signal_score):
    """
    Kapsamlı trading senaryoları analizi
    """
    scenarios = []
    action_plan = {}
    
    # Senaryo 1: Formasyon kırılımı
    if formation_type == 'OBO':
        neckline = formation_data['neckline']
        if current_price > neckline:
            scenarios.append({
                'type': 'OBO Short Fırsatı',
                'condition': f'Fiyat {format_price(neckline)} altına düşerse',
                'entry': current_price,
                'tp': fibo_levels.get('0.618', current_price * 0.95),
                'sl': fibo_levels.get('0.382', current_price * 1.02),
                'probability': 'Orta',
                'risk': 'Yüksek (Trend boğa)',
                'volume_requirement': '1.5x+ hacim artışı gerekli'
            })
        else:
            scenarios.append({
                'type': 'OBO Short Aktif',
                'condition': 'Formasyon tamamlandı',
                'entry': current_price,
                'tp': fibo_levels.get('0.618', current_price * 0.95),
                'sl': fibo_levels.get('0.382', current_price * 1.02),
                'probability': 'Yüksek',
                'risk': 'Orta',
                'volume_requirement': 'Mevcut hacim yeterli'
            })
    
    elif formation_type == 'TOBO':
        neckline = formation_data['neckline']
        if current_price < neckline:
            scenarios.append({
                'type': 'TOBO Long Fırsatı',
                'condition': f'Fiyat {format_price(neckline)} üstüne çıkarsa',
                'entry': current_price,
                'tp': fibo_levels.get('0.382', current_price * 1.05),
                'sl': fibo_levels.get('0.618', current_price * 0.98),
                'probability': 'Orta',
                'risk': 'Yüksek (Trend ayı)',
                'volume_requirement': '1.5x+ hacim artışı gerekli'
            })
        else:
            scenarios.append({
                'type': 'TOBO Long Aktif',
                'condition': 'Formasyon tamamlandı',
                'entry': current_price,
                'tp': fibo_levels.get('0.382', current_price * 1.05),
                'sl': fibo_levels.get('0.618', current_price * 0.98),
                'probability': 'Yüksek',
                'risk': 'Orta',
                'volume_requirement': 'Mevcut hacim yeterli'
            })
    
    # Senaryo 2: Bollinger Bands kırılımı
    if bb_data:
        if bb_data['signal'] == 'Overbought':
            scenarios.append({
                'type': 'Bollinger Short',
                'condition': f'Fiyat {format_price(bb_data["upper_band"])} altına düşerse',
                'entry': current_price,
                'tp': bb_data['middle_band'],
                'sl': bb_data['upper_band'] * 1.01,
                'probability': 'Düşük',
                'risk': 'Orta',
                'volume_requirement': 'Normal hacim'
            })
        elif bb_data['signal'] == 'Oversold':
            scenarios.append({
                'type': 'Bollinger Long',
                'condition': f'Fiyat {format_price(bb_data["lower_band"])} üstüne çıkarsa',
                'entry': current_price,
                'tp': bb_data['middle_band'],
                'sl': bb_data['lower_band'] * 0.99,
                'probability': 'Düşük',
                'risk': 'Orta',
                'volume_requirement': 'Normal hacim'
            })
    
    # Senaryo 3: Fibonacci seviyeleri
    fibo_scenarios = []
    for level, price in fibo_levels.items():
        if abs(current_price - price) / current_price < 0.02:  # %2 yakınlık
            if current_price > price:
                fibo_scenarios.append({
                    'type': f'Fibonacci {level} Direnç',
                    'condition': f'Fiyat {format_price(price)} altına düşerse',
                    'entry': current_price,
                    'tp': price * 0.98,
                    'sl': price * 1.02,
                    'probability': 'Orta',
                    'risk': 'Düşük',
                    'volume_requirement': 'Normal hacim'
                })
            else:
                fibo_scenarios.append({
                    'type': f'Fibonacci {level} Destek',
                    'condition': f'Fiyat {format_price(price)} üstüne çıkarsa',
                    'entry': current_price,
                    'tp': price * 1.02,
                    'sl': price * 0.98,
                    'probability': 'Orta',
                    'risk': 'Düşük',
                    'volume_requirement': 'Normal hacim'
                })
    
    scenarios.extend(fibo_scenarios)
    
    # Aksiyon planı belirleme - DÜZELTİLMİŞ
    if signal_score['final_signal'] == 'Bekleme':
        action_plan = {
            'immediate_action': 'BEKLEME MODU',
            'reason': f'Çelişkili sinyaller: {signal_score["conflict"]}',
            'watch_levels': [
                f'Boyun çizgisi: {format_price(formation_data["neckline"]) if formation_data else "N/A"}',
                f'Bollinger üst: {format_price(bb_data["upper_band"]) if bb_data else "N/A"}',
                f'Bollinger alt: {format_price(bb_data["lower_band"]) if bb_data else "N/A"}'
            ],
            'entry_criteria': 'Daha net sinyal bekleyin',
            'risk_level': 'Yüksek (çelişkili sinyaller)'
        }
    elif signal_score['final_signal'] == 'Long':
        # Long için doğru TP/SL hesaplama
        if formation_type == 'TOBO' and formation_data:
            neckline = formation_data['neckline']
            if current_price < neckline:
                # Kırılım bekleniyor
                entry_price = neckline
                tp_price = neckline + (neckline - current_price) * 1.5  # 1.5x hedef
                sl_price = current_price * 0.98  # %2 altında
            else:
                # Kırılım gerçekleşti
                entry_price = current_price
                tp_price = current_price * 1.05  # %5 üstünde
                sl_price = neckline * 0.98  # Boyun çizgisinin altında
        else:
            # Genel long stratejisi
            entry_price = current_price
            tp_price = current_price * 1.05  # %5 üstünde
            sl_price = current_price * 0.98  # %2 altında
        
        action_plan = {
            'immediate_action': 'LONG GİR',
            'reason': f'Güçlü long sinyali: %{signal_score["long_percentage"]:.1f}',
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'watch_levels': [
                f'TP: {format_price(tp_price)}',
                f'SL: {format_price(sl_price)}'
            ],
            'entry_criteria': 'Anlık fiyattan giriş',
            'risk_level': signal_score['confidence']
        }
    else:  # Short
        # Short için doğru TP/SL hesaplama
        if formation_type == 'OBO' and formation_data:
            neckline = formation_data['neckline']
            if current_price > neckline:
                # Kırılım bekleniyor
                entry_price = neckline
                tp_price = neckline - (current_price - neckline) * 1.5  # 1.5x hedef
                sl_price = current_price * 1.02  # %2 üstünde
            else:
                # Kırılım gerçekleşti
                entry_price = current_price
                tp_price = current_price * 0.95  # %5 altında
                sl_price = neckline * 1.02  # Boyun çizgisinin üstünde
        else:
            # Genel short stratejisi
            entry_price = current_price
            tp_price = current_price * 0.95  # %5 altında
            sl_price = current_price * 1.02  # %2 üstünde
        
        action_plan = {
            'immediate_action': 'SHORT GİR',
            'reason': f'Güçlü short sinyali: %{signal_score["short_percentage"]:.1f}',
            'entry_price': entry_price,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'watch_levels': [
                f'TP: {format_price(tp_price)}',
                f'SL: {format_price(sl_price)}'
            ],
            'entry_criteria': 'Anlık fiyattan giriş',
            'risk_level': signal_score['confidence']
        }
    
    return scenarios, action_plan


def print_trading_summary(action_plan, scenarios, signal_score):
    """
    Trading özeti yazdırma
    """
    print(f"\n🎯 TRADING ÖZETİ:")
    print(f"   📊 Aksiyon: {action_plan['immediate_action']}")
    print(f"   📊 Sebep: {action_plan['reason']}")
    print(f"   📊 Risk Seviyesi: {action_plan['risk_level']}")
    
    if action_plan['immediate_action'] != 'BEKLE':
        print(f"\n💰 İŞLEM DETAYLARI:")
        if 'entry_price' in action_plan:
            print(f"   🎯 Giriş: {format_price(action_plan['entry_price'])}")
        else:
            print(f"   🎯 Giriş: Bilgi yok")
        if 'tp_price' in action_plan:
            print(f"   🎯 TP: {format_price(action_plan['tp_price'])}")
        else:
            print(f"   🎯 TP: Bilgi yok")
        if 'sl_price' in action_plan:
            print(f"   🛑 SL: {format_price(action_plan['sl_price'])}")
        else:
            print(f"   🛑 SL: Bilgi yok")
        # Risk/Ödül hesaplama - DÜZELTİLMİŞ
        if 'entry_price' in action_plan and 'sl_price' in action_plan and 'tp_price' in action_plan:
            if action_plan['immediate_action'] == 'LONG GİR':
                risk = (action_plan['entry_price'] - action_plan['sl_price']) / action_plan['entry_price']
                reward = (action_plan['tp_price'] - action_plan['entry_price']) / action_plan['entry_price']
            else:  # Short
                risk = (action_plan['sl_price'] - action_plan['entry_price']) / action_plan['entry_price']
                reward = (action_plan['entry_price'] - action_plan['tp_price']) / action_plan['entry_price']
            # R/R oranı kontrolü
            if risk > 0 and reward > 0:
                rr_ratio = reward / risk
                print(f"   📊 R/R Oranı: {rr_ratio:.2f}:1")
                print(f"   📊 Risk: %{risk*100:.2f} | Ödül: %{reward*100:.2f}")
            else:
                print(f"   📊 R/R Oranı: Geçersiz")
                print(f"   📊 Risk: %{risk*100:.2f} | Ödül: %{reward*100:.2f}")
                print(f"   ⚠️  UYARI: Geçersiz R/R oranı - İşlem önerilmez!")
        else:
            print(f"   📊 R/R Oranı: Hesaplanamadı (Eksik veri)")
    
    print(f"\n👀 İZLENECEK SEVİYELER:")
    for level in action_plan['watch_levels']:
        print(f"   📍 {level}")
    
    print(f"\n📋 SENARYOLAR:")
    for i, scenario in enumerate(scenarios[:3], 1):  # İlk 3 senaryo
        print(f"   {i}. {scenario['type']}")
        print(f"      📊 Koşul: {scenario['condition']}")
        print(f"      📊 Olasılık: {scenario['probability']} | Risk: {scenario['risk']}")
        print(f"      📊 Hacim: {scenario['volume_requirement']}")


def calculate_three_tp_levels(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None, formation_type=None):
    """
    3 farklı TP seviyesi hesaplar ve kâr yüzdesine göre küçükten büyüğe sıralar.
    - TP1: En düşük kâr (ana TP'den düşük olamaz)
    - TP2: Orta kâr
    - TP3: Maksimum kâr
    """
    tp_candidates = []
    
    # Ana TP'yi mutlaka ekle (en önemli)
    if direction == 'Long':
        if current_tp > entry_price:
            main_gain = (current_tp - entry_price) / entry_price * 100
            tp_candidates.append({'price': current_tp, 'level': 'Ana TP', 'gain': main_gain})
    else:  # Short
        if current_tp < entry_price:
            main_gain = (entry_price - current_tp) / entry_price * 100
            tp_candidates.append({'price': current_tp, 'level': 'Ana TP', 'gain': main_gain})
    
    if direction == 'Long':
        # TP adaylarını topla (sadece ana TP'den yüksek olanları)
        for level in ['0.382', '0.5', '0.618', '0.786']:
            if level in fibo_levels and fibo_levels[level] > entry_price and fibo_levels[level] > current_tp:
                gain = (fibo_levels[level] - entry_price) / entry_price * 100
                tp_candidates.append({'price': fibo_levels[level], 'level': level, 'gain': gain})
        
        # Formasyon hedefi (ana TP'den yüksek olmalı)
        if formation_type == 'TOBO' or formation_type == 'CUP_HANDLE':
            tp3_price = entry_price * 1.30
            if tp3_price > current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Formasyon Hedefi', 'gain': (tp3_price - entry_price) / entry_price * 100})
        elif formation_type == 'FALLING_WEDGE':
            tp3_price = entry_price * 1.25
            if tp3_price > current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Formasyon Hedefi', 'gain': (tp3_price - entry_price) / entry_price * 100})
        else:
            tp3_price = entry_price * 1.50
            if tp3_price > current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Genel Hedef', 'gain': (tp3_price - entry_price) / entry_price * 100})
        
        # Bollinger üst bandı (ana TP'den yüksek olmalı)
        if bb_data and bb_data['upper_band'] > entry_price and bb_data['upper_band'] > current_tp:
            gain = (bb_data['upper_band'] - entry_price) / entry_price * 100
            tp_candidates.append({'price': bb_data['upper_band'], 'level': 'Bollinger Üst', 'gain': gain})
    
    else:  # Short
        # TP adaylarını topla (sadece ana TP'den düşük olanları)
        for level in ['0.618', '0.5', '0.382', '0.236']:
            if level in fibo_levels and fibo_levels[level] < entry_price and fibo_levels[level] < current_tp:
                gain = (entry_price - fibo_levels[level]) / entry_price * 100
                tp_candidates.append({'price': fibo_levels[level], 'level': level, 'gain': gain})
        
        if formation_type == 'OBO':
            tp3_price = entry_price * 0.70
            if tp3_price < current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Formasyon Hedefi', 'gain': (entry_price - tp3_price) / entry_price * 100})
        else:
            tp3_price = entry_price * 0.50
            if tp3_price < current_tp:
                tp_candidates.append({'price': tp3_price, 'level': 'Genel Hedef', 'gain': (entry_price - tp3_price) / entry_price * 100})
        
        if bb_data and bb_data['lower_band'] < entry_price and bb_data['lower_band'] < current_tp:
            gain = (entry_price - bb_data['lower_band']) / entry_price * 100
            tp_candidates.append({'price': bb_data['lower_band'], 'level': 'Bollinger Alt', 'gain': gain})
    
    # Kâr yüzdesine göre sırala
    tp_candidates = sorted(tp_candidates, key=lambda x: x['gain'])
    
    # En iyi 3 TP'yi seç (ana TP mutlaka dahil olmalı)
    if len(tp_candidates) >= 3:
        tp1 = tp_candidates[0]  # En düşük kâr
        tp2 = tp_candidates[1]  # Orta kâr
        tp3 = tp_candidates[-1]  # En yüksek kâr
    elif len(tp_candidates) == 2:
        tp1 = tp_candidates[0]
        tp2 = tp_candidates[1]
        tp3 = tp_candidates[1]  # Aynı seviye
    elif len(tp_candidates) == 1:
        tp1 = tp_candidates[0]
        tp2 = tp_candidates[0]  # Aynı seviye
        tp3 = tp_candidates[0]  # Aynı seviye
    else:
        # Hiç TP bulunamadıysa ana TP'yi kullan
        if direction == 'Long':
            gain = (current_tp - entry_price) / entry_price * 100
        else:
            gain = (entry_price - current_tp) / entry_price * 100
        
        tp1 = {'price': current_tp, 'level': 'Ana TP', 'gain': gain}
        tp2 = {'price': current_tp, 'level': 'Ana TP', 'gain': gain}
        tp3 = {'price': current_tp, 'level': 'Ana TP', 'gain': gain}
    
    return {
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3
    }


def optimize_tp_sl(entry_price, current_tp, current_sl, direction, fibo_levels, bb_data=None):
    """
    TP ve SL seviyelerini optimize eder - R/R oranını en az 1.5 yapar
    """
    if direction == 'Long':
        # Mantık kontrolü: Long için entry > SL ve TP > entry olmalı
        if entry_price <= current_sl or current_tp <= entry_price:
            print(f"   ❌ Geçersiz fiyat seviyeleri! Long için: Giriş > SL ve TP > Giriş olmalı")
            print(f"      Giriş: {format_price(entry_price)} | SL: {format_price(current_sl)} | TP: {format_price(current_tp)}")
            return entry_price, entry_price * 0.99, 0  # Geçersiz durum
        
        # Mevcut R/R hesapla
        current_reward = (current_tp - entry_price) / entry_price
        current_risk = (entry_price - current_sl) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        print(f"   📊 Mevcut R/R: {current_rr:.2f}:1 (Hedef: 1.5:1)")
        
        # R/R < 1.5 ise optimize et
        if current_rr < 1.5:
            print(f"   ⚠️  R/R oranı düşük! Optimizasyon yapılıyor...")
            
            # TP seçenekleri (Fibonacci seviyeleri) - Sadece giriş fiyatının üstündeki
            tp_options = []
            for level in ['0.236', '0.382', '0.5', '0.618']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    tp_options.append((level, fibo_levels[level]))
            
            # SL seçenekleri (daha sıkı) - Sadece giriş fiyatının altındaki
            sl_options = []
            for level in ['0.786', '0.618', '0.5']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    sl_options.append((level, fibo_levels[level]))
            
            # Bollinger alt bandı da SL seçeneği olarak ekle (sadece giriş fiyatının altındaysa)
            if bb_data and bb_data['lower_band'] < entry_price:
                sl_options.append(('BB Lower', bb_data['lower_band']))
            
            best_tp = current_tp
            best_sl = current_sl
            best_rr = current_rr
            
            # En iyi kombinasyonu bul
            for tp_level, tp_price in tp_options:
                for sl_level, sl_price in sl_options:
                    # Ekstra mantık kontrolü
                    if tp_price <= entry_price or sl_price >= entry_price:
                        continue  # Bu kombinasyonu atla
                    
                    # Minimum SL mesafesi kontrolü (%3'ten az olmasın)
                    sl_distance = (entry_price - sl_price) / entry_price
                    if sl_distance < 0.03:  # %3'ten az mesafe güvenli değil
                        continue
                    
                    reward = (tp_price - entry_price) / entry_price
                    risk = (entry_price - sl_price) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    if rr >= 1.5 and rr > best_rr:
                        best_tp = tp_price
                        best_sl = sl_price
                        best_rr = rr
                        print(f"   ✅ Daha iyi kombinasyon bulundu:")
                        print(f"      TP: {format_price(tp_price)} ({tp_level})")
                        print(f"      SL: {format_price(sl_price)} ({sl_level})")
                        print(f"      R/R: {rr:.2f}:1")
            
            if best_rr > current_rr:
                print(f"   🎯 Optimizasyon tamamlandı!")
                print(f"      Eski R/R: {current_rr:.2f}:1 → Yeni R/R: {best_rr:.2f}:1")
                return best_tp, best_sl, best_rr
            else:
                print(f"   ❌ Daha iyi kombinasyon bulunamadı")
                return current_tp, current_sl, current_rr
        else:
            print(f"   ✅ R/R oranı yeterli: {current_rr:.2f}:1")
            return current_tp, current_sl, current_rr
    
    else:  # Short
        # Mantık kontrolü: Short için entry < SL ve TP < entry olmalı
        if entry_price >= current_sl or current_tp >= entry_price:
            print(f"   ❌ Geçersiz fiyat seviyeleri! Short için: Giriş < SL ve TP < Giriş olmalı")
            print(f"      Giriş: {format_price(entry_price)} | SL: {format_price(current_sl)} | TP: {format_price(current_tp)}")
            return entry_price, entry_price * 1.01, 0  # Geçersiz durum
        
        # Mevcut R/R hesapla
        current_reward = (entry_price - current_tp) / entry_price
        current_risk = (current_sl - entry_price) / entry_price
        current_rr = current_reward / current_risk if current_risk > 0 else 0
        
        print(f"   📊 Mevcut R/R: {current_rr:.2f}:1 (Hedef: 1.5:1)")
        
        # R/R < 1.5 ise optimize et
        if current_rr < 1.5:
            print(f"   ⚠️  R/R oranı düşük! Optimizasyon yapılıyor...")
            
            # TP seçenekleri (Fibonacci seviyeleri) - Sadece giriş fiyatının altındaki
            tp_options = []
            for level in ['0.618', '0.5', '0.382', '0.236']:
                if level in fibo_levels and fibo_levels[level] < entry_price:
                    tp_options.append((level, fibo_levels[level]))
            
            # SL seçenekleri (daha sıkı) - Sadece giriş fiyatının üstündeki
            sl_options = []
            for level in ['0.236', '0.382', '0.5']:
                if level in fibo_levels and fibo_levels[level] > entry_price:
                    sl_options.append((level, fibo_levels[level]))
            
            # Bollinger üst bandı da SL seçeneği olarak ekle (sadece giriş fiyatının üstündeyse)
            if bb_data and bb_data['upper_band'] > entry_price:
                sl_options.append(('BB Upper', bb_data['upper_band']))
            
            best_tp = current_tp
            best_sl = current_sl
            best_rr = current_rr
            
            # En iyi kombinasyonu bul
            for tp_level, tp_price in tp_options:
                for sl_level, sl_price in sl_options:
                    # Ekstra mantık kontrolü
                    if tp_price >= entry_price or sl_price <= entry_price:
                        continue  # Bu kombinasyonu atla
                    
                    # Minimum SL mesafesi kontrolü (%3'ten az olmasın)
                    sl_distance = (sl_price - entry_price) / entry_price
                    if sl_distance < 0.03:  # %3'ten az mesafe güvenli değil
                        continue
                    
                    reward = (entry_price - tp_price) / entry_price
                    risk = (sl_price - entry_price) / entry_price
                    rr = reward / risk if risk > 0 else 0
                    
                    if rr >= 1.5 and rr > best_rr:
                        best_tp = tp_price
                        best_sl = sl_price
                        best_rr = rr
                        print(f"   ✅ Daha iyi kombinasyon bulundu:")
                        print(f"      TP: {format_price(tp_price)} ({tp_level})")
                        print(f"      SL: {format_price(sl_price)} ({sl_level})")
                        print(f"      R/R: {rr:.2f}:1")
            
            if best_rr > current_rr:
                print(f"   🎯 Optimizasyon tamamlandı!")
                print(f"      Eski R/R: {current_rr:.2f}:1 → Yeni R/R: {best_rr:.2f}:1")
                return best_tp, best_sl, best_rr
            else:
                print(f"   ❌ Daha iyi kombinasyon bulunamadı")
                return current_tp, current_sl, current_rr
        else:
            print(f"   ✅ R/R oranı yeterli: {current_rr:.2f}:1")
            return current_tp, current_sl, current_rr


def calculate_ichimoku(df):
    """
    Ichimoku Cloud hesaplar ve temel sinyalleri döndürür.
    Returns: dict
    """
    try:
        high_9 = df['high'].rolling(window=9).max()
        low_9 = df['low'].rolling(window=9).min()
        tenkan_sen = (high_9 + low_9) / 2
        high_26 = df['high'].rolling(window=26).max()
        low_26 = df['low'].rolling(window=26).min()
        kijun_sen = (high_26 + low_26) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        high_52 = df['high'].rolling(window=52).max()
        low_52 = df['low'].rolling(window=52).min()
        senkou_span_b = ((high_52 + low_52) / 2).shift(26)
        chikou_span = df['close'].shift(-26)
        price = df['close'].iloc[-1]
        cloud_top = max(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1])
        cloud_bottom = min(senkou_span_a.iloc[-1], senkou_span_b.iloc[-1])
        signal = 'bullish' if price > cloud_top else 'bearish' if price < cloud_bottom else 'neutral'
        tenkan_kijun_cross = 'bullish' if tenkan_sen.iloc[-1] > kijun_sen.iloc[-1] else 'bearish' if tenkan_sen.iloc[-1] < kijun_sen.iloc[-1] else 'neutral'
        return {
            'signal': signal,
            'tenkan_kijun_cross': tenkan_kijun_cross,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'price': price
        }
    except Exception as e:
        return None

def calculate_supertrend(df, period=10, multiplier=3):
    """
    Supertrend göstergesini hesaplar ve buy/sell sinyali döndürür.
    Returns: dict
    """
    try:
        hl2 = (df['high'] + df['low']) / 2
        atr = df['high'].rolling(window=period).max() - df['low'].rolling(window=period).min()
        upperband = hl2 + (multiplier * atr)
        lowerband = hl2 - (multiplier * atr)
        supertrend = [True]  # True: buy, False: sell
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upperband.iloc[i-1]:
                supertrend.append(True)
            elif df['close'].iloc[i] < lowerband.iloc[i-1]:
                supertrend.append(False)
            else:
                supertrend.append(supertrend[-1])
        signal = 'buy' if supertrend[-1] else 'sell'
        return {
            'signal': signal,
            'upperband': upperband.iloc[-1],
            'lowerband': lowerband.iloc[-1]
        }
    except Exception as e:
        return None

def calculate_vwap(df):
    """
    VWAP (Volume Weighted Average Price) hesaplar ve fiyatın üstünde/altında olup olmadığını döndürür.
    Returns: dict
    """
    try:
        vwap = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        price = df['close'].iloc[-1]
        signal = 'above' if price > vwap.iloc[-1] else 'below' if price < vwap.iloc[-1] else 'neutral'
        return {
            'signal': signal,
            'vwap': vwap.iloc[-1],
            'price': price
        }
    except Exception as e:
        return None

def calculate_obv(df):
    """
    OBV (On-Balance Volume) hesaplar ve fiyatla uyumunu kontrol eder.
    Returns: dict
    """
    try:
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        obv_series = pd.Series(obv, index=df.index)
        price_trend = 'up' if df['close'].iloc[-1] > df['close'].iloc[0] else 'down' if df['close'].iloc[-1] < df['close'].iloc[0] else 'flat'
        obv_trend = 'up' if obv_series.iloc[-1] > obv_series.iloc[0] else 'down' if obv_series.iloc[-1] < obv_series.iloc[0] else 'flat'
        divergence = price_trend != obv_trend
        return {
            'obv': obv_series.iloc[-1],
            'obv_trend': obv_trend,
            'price_trend': price_trend,
            'divergence': divergence
        }
    except Exception as e:
        return None

def calculate_heikin_ashi(df):
    """
    Heikin Ashi mumlarını hesaplar ve trendi döndürür.
    Returns: dict
    """
    try:
        ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
        for i in range(1, len(df)):
            ha_open.append((ha_open[-1] + ha_close.iloc[i-1]) / 2)
        ha_open = pd.Series(ha_open, index=df.index)
        ha_high = pd.concat([df['high'], ha_open, ha_close], axis=1).max(axis=1)
        ha_low = pd.concat([df['low'], ha_open, ha_close], axis=1).min(axis=1)
        trend = 'bullish' if ha_close.iloc[-1] > ha_open.iloc[-1] else 'bearish' if ha_close.iloc[-1] < ha_open.iloc[-1] else 'neutral'
        return {
            'ha_open': ha_open.iloc[-1],
            'ha_close': ha_close.iloc[-1],
            'ha_high': ha_high.iloc[-1],
            'ha_low': ha_low.iloc[-1],
            'trend': trend
        }
    except Exception as e:
        return None

def main():
    interval = '4h'
    print("\n🤖 Tek Coin Analiz Botu Başlatılıyor...")
    print("📊 Bot her fırsat için en uygun risk seviyesini otomatik önerecek")
    print("💰 Risk seviyesi: Kaldıraç, pozisyon büyüklüğü ve potansiyel kazanç")
    print("🎯 R/R Filtresi: 0.8:1'den yüksek risk/ödül oranına sahip sinyaller gösterilecek (Esnek)")
    
    while True:
        symbol_input = input('\n📈 Lütfen analiz etmek istediğiniz sembolü girin (örn: BTC, ETH, SOL): ').strip().upper()
        symbol = symbol_input + 'USDT'
        print(f'🔍 Analiz ediliyor: {symbol}')
        
        try:
            current_price = get_current_price(symbol)
            if current_price:
                print(f'💰 Anlık fiyat: {format_price(current_price)}')
            else:
                print('❌ Anlık fiyat alınamadı.')
                continue
                
            df = fetch_ohlcv(symbol, interval)
            if df is None or df.empty:
                print('❌ Veri alınamadı veya boş.')
                continue
            else:
                print('✅ Veri başarıyla çekildi')
                
            # Fibonacci seviyeleri
            fibo_levels, fibo_high, fibo_low = calculate_fibonacci_levels(df)
            print(f"\n📊 Fibonacci seviyeleri (son 20 mum):")
            print(f"   🔺 En Yüksek: {format_price(fibo_high)}")
            print(f"   🔻 En Düşük: {format_price(fibo_low)}")
            for k, v in fibo_levels.items():
                print(f"   {k}: {format_price(v)}")
            
            # MA hesaplamaları (MA200 çıkarıldı)
            df['MA7'] = df['close'].rolling(window=7).mean()
            df['MA25'] = df['close'].rolling(window=25).mean()
            df['MA50'] = df['close'].rolling(window=50).mean()
            df['MA99'] = df['close'].rolling(window=99).mean()
            
            print(f"\n📈 Hareketli Ortalamalar:")
            print(f"   MA7:   {format_price(df['MA7'].iloc[-1])}")
            print(f"   MA25:  {format_price(df['MA25'].iloc[-1])}")
            print(f"   MA50:  {format_price(df['MA50'].iloc[-1])}")
            print(f"   MA99:  {format_price(df['MA99'].iloc[-1])}")
            
            # MA'lara göre trend yorumu (MA99'a kadar)
            ma_trend = None
            if df['MA7'].iloc[-1] > df['MA25'].iloc[-1] > df['MA50'].iloc[-1] > df['MA99'].iloc[-1]:
                ma_trend = 'Güçlü Yükseliş (Tüm kısa MA\'lar uzun MA\'ların üstünde)'
            elif df['MA7'].iloc[-1] < df['MA25'].iloc[-1] < df['MA50'].iloc[-1] < df['MA99'].iloc[-1]:
                ma_trend = 'Güçlü Düşüş (Tüm kısa MA\'lar uzun MA\'ların altında)'
            else:
                ma_trend = 'Kararsız veya yatay trend (MA\'lar karışık)'
            print(f"\n📊 MA'lara göre trend: {ma_trend}")
            
            # Formasyon tespiti
            formations = detect_formations(df)
            
            # Genel teknik duruma göre tavsiye
            genel_tavsiye = None
            if formations and formations['kanal_var']:
                kanal_yonu = formations['kanal_yonu']
                son_fiyat = df['close'].iloc[-1]
                if kanal_yonu == 'Yükselen Kanal':
                    if son_fiyat <= fibo_levels['0.382']:
                        genel_tavsiye = 'Long fırsatı (yükselen kanal, fiyat destek bölgesinde)'
                    else:
                        genel_tavsiye = 'Long ağırlıklı (yükselen kanal)'
                elif kanal_yonu == 'Düşen Kanal':
                    if son_fiyat >= fibo_levels['0.618']:
                        genel_tavsiye = 'Short fırsatı (düşen kanal, fiyat direnç bölgesinde)'
                    else:
                        genel_tavsiye = 'Short ağırlıklı (düşen kanal)'
                else:
                    genel_tavsiye = 'Yatay kanal, net sinyal yok'
            else:
                genel_tavsiye = 'Kanal tespit edilmedi, net sinyal yok'
            
            print(f"\n🎯 Genel teknik tavsiye: {genel_tavsiye}")
            
            # Tüm gelişmiş formasyonları analiz et
            formation_signal = analyze_all_formations_advanced(df)
            
            # Yeni gelişmiş formasyonları göster
            if formation_signal and isinstance(formation_signal, dict) and 'score' in formation_signal and 'type' in formation_signal and 'confidence' in formation_signal:
                formation_type = formation_signal['type']
                formation_score = formation_signal['score']
                formation_confidence = formation_signal['confidence']
                
                print(f"\n🎯 GELİŞMİŞ FORMASYON TESPİT EDİLDİ!")
                print(f"   📊 Formasyon: {formation_type}")
                print(f"   🎯 Skor: {formation_score:.1f}")
                print(f"   🛡️  Güven: {formation_confidence}")
                
                # Formasyon tipine göre detaylı bilgi
                if 'DOUBLE_BOTTOM' in formation_type:
                    print(f"   📊 Sol Dip: {format_price(formation_signal.get('trough1_price', 0))}")
                    print(f"   📊 Sağ Dip: {format_price(formation_signal.get('trough2_price', 0))}")
                    print(f"   📊 Boyun Çizgisi: {format_price(formation_signal.get('neckline_price', 0))}")
                    print(f"   📊 Kırılım: {'✅ Teyit Edildi' if formation_signal.get('breakout_confirmed', False) else '❌ Beklemede'}")
                    print(f"   📊 Hacim: {'✅ Teyit Edildi' if formation_signal.get('volume_confirmed', False) else '❌ Düşük'}")
                
                elif 'DOUBLE_TOP' in formation_type:
                    print(f"   📊 Sol Tepe: {format_price(formation_signal.get('peak1_price', 0))}")
                    print(f"   📊 Sağ Tepe: {format_price(formation_signal.get('peak2_price', 0))}")
                    print(f"   📊 Boyun Çizgisi: {format_price(formation_signal.get('neckline_price', 0))}")
                    print(f"   📊 Kırılım: {'✅ Teyit Edildi' if formation_signal.get('breakout_confirmed', False) else '❌ Beklemede'}")
                    print(f"   📊 Hacim: {'✅ Teyit Edildi' if formation_signal.get('volume_confirmed', False) else '❌ Düşük'}")
                
                elif 'BULLISH_FLAG' in formation_type or 'BEARISH_FLAG' in formation_type:
                    print(f"   📊 Bayrak Direği: {formation_signal.get('trend_direction', 'N/A')}")
                    print(f"   📊 Üst Çizgi: {format_price(formation_signal.get('upper_line', 0))}")
                    print(f"   📊 Alt Çizgi: {format_price(formation_signal.get('lower_line', 0))}")
                    print(f"   📊 Kırılım: {'✅ Teyit Edildi' if formation_signal.get('breakout_confirmed', False) else '❌ Beklemede'}")
                    print(f"   📊 Hacim Düşüşü: {'✅ Teyit Edildi' if formation_signal.get('volume_decrease', False) else '❌ Yok'}")
                
                elif 'ASCENDING_TRIANGLE' in formation_type or 'DESCENDING_TRIANGLE' in formation_type:
                    print(f"   📊 Üst Çizgi: {format_price(formation_signal.get('upper_line', 0))}")
                    print(f"   📊 Alt Çizgi: {format_price(formation_signal.get('lower_line', 0))}")
                    print(f"   📊 Kırılım: {'✅ Teyit Edildi' if formation_signal.get('breakout_confirmed', False) else '❌ Beklemede'}")
                    print(f"   📊 Hacim: {'✅ Teyit Edildi' if formation_signal.get('volume_confirmed', False) else '❌ Düşük'}")
                
                elif 'SYMMETRICAL_TRIANGLE' in formation_type:
                    print(f"   📊 Üst Çizgi: {format_price(formation_signal.get('upper_line', 0))}")
                    print(f"   📊 Alt Çizgi: {format_price(formation_signal.get('lower_line', 0))}")
                    print(f"   📊 Kırılım Yönü: {formation_signal.get('breakout_direction', 'N/A')}")
                    print(f"   📊 Hacim: {'✅ Teyit Edildi' if formation_signal.get('volume_confirmed', False) else '❌ Düşük'}")
                
                elif 'RISING_CHANNEL' in formation_type:
                    print(f"   📊 Üst Kanal: {format_price(formation_signal.get('upper_line', 0))}")
                    print(f"   📊 Alt Kanal: {format_price(formation_signal.get('lower_line', 0))}")
                    print(f"   📊 Kanal Genişliği: {format_price(formation_signal.get('channel_width', 0))}")
                    print(f"   📊 Kırılım: {'✅ Teyit Edildi' if formation_signal.get('breakout_confirmed', False) else '❌ Beklemede'}")
                
                elif 'DIVERGENCE' in formation_type:
                    print(f"   📊 İndikatör: {formation_signal.get('indicator', 'N/A')}")
                    print(f"   📊 Güç: {formation_signal.get('strength', 'N/A')}")
                    print(f"   📊 Fiyat Değişimi: %{formation_signal.get('price_change', 0)*100:.1f}")
                    print(f"   📊 İndikatör Değişimi: %{formation_signal.get('macd_change', 0)*100:.1f}")
                
                print(f"   📊 Giriş: {format_price(formation_signal.get('entry_price', 0))}")
                print(f"   📊 TP: {format_price(formation_signal.get('tp', 0))}")
                print(f"   📊 SL: {format_price(formation_signal.get('sl', 0))}")
                print(f"   📊 Yön: {formation_signal.get('direction', 'N/A')}")
            else:
                print(f"\n❌ Gelişmiş formasyon tespit edilmedi.")
            
            # Eski formasyonları da ayrı ayrı kontrol et (geriye uyumluluk için)
            all_tobo = find_all_tobo(df)
            all_obo = find_all_obo(df)
            tobo = all_tobo[-1] if all_tobo else None
            obo = all_obo[-1] if all_obo else None
            
            # Cup and Handle formasyonu tespiti
            cup_handle = detect_cup_and_handle(df)
            
            # Falling Wedge formasyonu tespiti
            falling_wedge = detect_falling_wedge(df)
            
            # En güçlü formasyonu belirle (Botanlik.py ile aynı mantık)
            dominant_formation = None
            formation_scores = {}
            
            # TOBO ve OBO'ya öncelik ver (Botanlik.py mantığı)
            if tobo:
                tobo_strength = abs(tobo['bas'] - tobo['neckline']) / tobo['neckline']
                formation_scores['TOBO'] = tobo_strength * 100
            
            if obo:
                obo_strength = abs(obo['bas'] - obo['neckline']) / obo['neckline']
                formation_scores['OBO'] = obo_strength * 100
            
            # Diğer formasyonları da ekle
            if cup_handle and isinstance(cup_handle, dict) and 'score' in cup_handle:
                formation_scores['CUP_HANDLE'] = cup_handle['score']
            
            if falling_wedge and isinstance(falling_wedge, dict) and 'score' in falling_wedge:
                formation_scores['FALLING_WEDGE'] = falling_wedge['score']
            
            # Yeni formasyon sinyali varsa ekle (düşük öncelik)
            if formation_signal and isinstance(formation_signal, dict) and 'score' in formation_signal and 'type' in formation_signal:
                formation_scores[formation_signal['type']] = formation_signal['score'] * 0.5  # Düşük öncelik
            
            # En yüksek skora sahip formasyonu seç
            if formation_scores:
                dominant_formation = max(formation_scores, key=formation_scores.get)
                
                if dominant_formation == 'TOBO':
                    print(f"\n🔄 TOBO formasyonu tespit edildi! (Skor: {formation_scores['TOBO']:.1f})")
                elif dominant_formation == 'OBO':
                    print(f"\n🔄 OBO formasyonu tespit edildi! (Skor: {formation_scores['OBO']:.1f})")
                elif dominant_formation == 'CUP_HANDLE':
                    print(f"\n🔄 Cup and Handle formasyonu tespit edildi! (Skor: {formation_scores['CUP_HANDLE']:.1f})")
                elif dominant_formation == 'FALLING_WEDGE':
                    print(f"\n🔺 Falling Wedge formasyonu tespit edildi! (Skor: {formation_scores['FALLING_WEDGE']:.1f})")
                elif dominant_formation == 'DOUBLE_BOTTOM':
                    print(f"\n🔄 Double Bottom formasyonu tespit edildi! (Skor: {formation_scores['DOUBLE_BOTTOM']:.1f})")
                elif dominant_formation == 'DOUBLE_TOP':
                    print(f"\n🔄 Double Top formasyonu tespit edildi! (Skor: {formation_scores['DOUBLE_TOP']:.1f})")
                elif dominant_formation == 'BULLISH_FLAG':
                    print(f"\n🚩 Bullish Flag formasyonu tespit edildi! (Skor: {formation_scores['BULLISH_FLAG']:.1f})")
                elif dominant_formation == 'BEARISH_FLAG':
                    print(f"\n🚩 Bearish Flag formasyonu tespit edildi! (Skor: {formation_scores['BEARISH_FLAG']:.1f})")
                elif dominant_formation == 'ASCENDING_TRIANGLE':
                    print(f"\n🔺 Ascending Triangle formasyonu tespit edildi! (Skor: {formation_scores['ASCENDING_TRIANGLE']:.1f})")
                elif dominant_formation == 'DESCENDING_TRIANGLE':
                    print(f"\n🔻 Descending Triangle formasyonu tespit edildi! (Skor: {formation_scores['DESCENDING_TRIANGLE']:.1f})")
                elif dominant_formation == 'SYMMETRICAL_TRIANGLE':
                    print(f"\n🔺 Symmetrical Triangle formasyonu tespit edildi! (Skor: {formation_scores['SYMMETRICAL_TRIANGLE']:.1f})")
                elif dominant_formation == 'RISING_CHANNEL':
                    print(f"\n📈 Rising Channel formasyonu tespit edildi! (Skor: {formation_scores['RISING_CHANNEL']:.1f})")
                elif dominant_formation == 'FALLING_CHANNEL':
                    print(f"\n📉 Falling Channel formasyonu tespit edildi! (Skor: {formation_scores['FALLING_CHANNEL']:.1f})")
                elif dominant_formation == 'HORIZONTAL_CHANNEL':
                    print(f"\n➡️ Horizontal Channel formasyonu tespit edildi! (Skor: {formation_scores['HORIZONTAL_CHANNEL']:.1f})")
                elif 'DIVERGENCE' in dominant_formation:
                    print(f"\n📊 {dominant_formation} tespit edildi! (Skor: {formation_scores[dominant_formation]:.1f})")
                else:
                    print(f"\n🔄 {dominant_formation} formasyonu tespit edildi! (Skor: {formation_scores[dominant_formation]:.1f})")
            else:
                print(f"\n❌ Hiçbir formasyon tespit edilmedi.")
            
            # Teknik İndikatörler - Önce hesapla (bb_data için gerekli)
            macd_data = calculate_macd(df)
            bb_data = calculate_bollinger_bands(df)
            stoch_data = calculate_stochastic(df)
            adx_data = calculate_adx(df)
            
            # Sadece dominant formasyonu analiz et
            tobo_signal = None
            obo_signal = None
            
            if dominant_formation == 'TOBO':
                print(f"   📊 Sol Omuz: {format_price(tobo['sol_omuz'])}")
                print(f"   📊 Baş: {format_price(tobo['bas'])}")
                print(f"   📊 Sağ Omuz: {format_price(tobo['sag_omuz'])}")
                print(f"   📊 Boyun Çizgisi: {format_price(tobo['neckline'])}")
                
                # 4H ve 1D boyun çizgisi kırılımı kontrolü
                print(f"\n🔍 4H/1D Boyun Çizgisi Kırılımı Analizi:")
                breakout_info = check_neckline_breakout(symbol, tobo['neckline'], 'Long')
                
                for timeframe, info in breakout_info.items():
                    status = "✅ TEYİT EDİLDİ" if info['confirmed'] else "❌ TEYİT EDİLMEDİ"
                    volume_status = "✅ YÜKSEK HACİM" if info['volume_confirmed'] else "⚠️  DÜŞÜK HACİM"
                    print(f"   📊 {timeframe}: {status} | {volume_status}")
                    print(f"      💰 Fiyat: {format_price(info['current_price'])} | Boyun: {format_price(info['neckline_price'])}")
                    print(f"      📈 Kırılım Gücü: %{info['strength']:.2f} | Hacim Oranı: {info['volume_ratio']:.2f}x")
                
                # Hacim teyidi analizi
                print(f"\n📊 Hacim Teyidi Analizi:")
                volume_analysis = analyze_volume_confirmation(symbol)
                
                for timeframe, vol_info in volume_analysis.items():
                    vol_status = "✅ TEYİT EDİLDİ" if vol_info['confirmed'] else "⚠️  DÜŞÜK HACİM"
                    print(f"   📊 {timeframe}: {vol_status} | Trend: {vol_info['volume_trend']}")
                    print(f"      📈 Hacim Oranı: {vol_info['volume_ratio']:.2f}x | Ortalama: {vol_info['avg_volume']:.0f}")
                
                # TOBO için risk analizi - Daha güvenli SL
                tp = fibo_levels['0.382']
                # SL'yi daha güvenli seviyede seç - Long için SL < Giriş olmalı
                # Minimum %3 mesafe olmalı
                min_sl_distance = current_price * 0.97  # %3 altı
                
                # Önce en düşük Fibonacci seviyesini dene
                if '0.786' in fibo_levels and fibo_levels['0.786'] < min_sl_distance:
                    sl = fibo_levels['0.786']
                elif '0.618' in fibo_levels and fibo_levels['0.618'] < min_sl_distance:
                    sl = fibo_levels['0.618']
                elif '0.5' in fibo_levels and fibo_levels['0.5'] < min_sl_distance:
                    sl = fibo_levels['0.5']
                else:
                    # Hiçbir Fibonacci seviyesi yeterince aşağıda değilse, %5 altını kullan
                    sl = current_price * 0.95
                
                # Giriş fiyatını belirle
                entry = current_price
                
                # Fiyat henüz boyun çizgisini kırmamışsa, mevcut fiyattan analiz yap
                if current_price < tobo['neckline']:
                    entry = current_price
                    print(f"\n💡 TOBO Long Fırsatı (Bekleme Modu) - Erken giriş fırsatı!")
                    print(f"   📊 Boyun çizgisi: {format_price(tobo['neckline'])}")
                    print(f"   📊 Mevcut fiyat: {format_price(current_price)}")
                    print(f"   📊 Kırılması gereken seviye: {format_price(tobo['neckline'])}")
                else:
                    entry = current_price  # Formasyon tamamlandıysa anlık fiyattan giriş
                    print(f"\n💡 TOBO Long Fırsatı (Aktif) - Formasyon tamamlandı!")
                    print(f"   📊 Boyun çizgisi: {format_price(tobo['neckline'])}")
                    print(f"   📊 Mevcut fiyat: {format_price(current_price)}")
                    print(f"   📊 Formasyon tamamlandı, anlık fiyattan giriş!")
                
                # Formasyon yüksekliği bazlı TP hesaplama (daha tutarlı)
                formation_height = tobo['bas'] - tobo['neckline']
                tp_formation = entry + formation_height
                
                # Ana TP'yi formasyon yüksekliği ile güncelle
                tp = tp_formation
                
                # SL'yi düzelt - Long için SL < Giriş olmalı
                if sl >= entry:
                    # SL giriş fiyatından yüksekse, %3 altını kullan
                    sl = entry * 0.97
                
                if tp > entry > sl and (tp - entry) / entry >= 0.01:
                    # 3 TP seviyesi hesaplama
                    print(f"\n🎯 3 TP SEVİYESİ HESAPLAMA:")
                    tp_levels = calculate_three_tp_levels(entry, tp, sl, 'Long', fibo_levels, bb_data, 'TOBO')
                    
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                    
                    # TP ve SL optimizasyonu (optimize edilmiş değerleri kullanma)
                    print(f"\n🔧 TP/SL Optimizasyonu:")
                    # Optimize edilmiş değerleri kullanma, orijinal değerleri kullan
                    optimized_tp, optimized_sl, optimized_rr = tp, sl, (tp - entry) / (entry - sl) if entry > sl else 0
                    
                    # R/R oranı kontrolü - Daha esnek (botanlik.py gibi)
                    if optimized_rr >= 0.8:
                        # Optimize edilmiş değerlerle risk analizi
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                        print(f"   🎯 Giriş: {format_price(entry)}")
                        print(f"   🎯 TP: {format_price(optimized_tp)}")
                        print(f"   🛑 SL: {format_price(optimized_sl)}")
                        print(f"   ⚠️  {risk_analysis['risk_level']} | Kaldıraç: {risk_analysis['leverage']}")
                        print(f"   💵 Pozisyon: {risk_analysis['position_size']} | R/R: {risk_analysis['risk_reward']} ✅")
                        print(f"   🎯 Hedef: {risk_analysis['potential_gain']} potansiyel kazanç")
                        print(f"   🔒 Margin: {risk_analysis['margin_type']} | Risk: {risk_analysis['risk_amount']} | Max Kayıp: {risk_analysis['max_loss']}")
                        
                        # Sinyal verilerini kaydet
                        tobo_signal = {
                            'valid': True,
                            'entry': entry,
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'risk_analysis': risk_analysis,
                            'tp_levels': tp_levels
                        }
                    else:
                        print(f"   ❌ R/R oranı yetersiz: {optimized_rr:.2f}:1 (Minimum 0.8:1 gerekli)")
                        tobo_signal = {'valid': False}
                else:
                    print(f"   ❌ Risk/Ödül oranı yetersiz (TP: {format_price(tp)}, SL: {format_price(sl)})")
                    tobo_signal = {'valid': False}
            
            elif dominant_formation == 'OBO':
                print(f"   📊 Sol Omuz: {format_price(obo['sol_omuz'])}")
                print(f"   📊 Baş: {format_price(obo['bas'])}")
                print(f"   📊 Sağ Omuz: {format_price(obo['sag_omuz'])}")
                print(f"   📊 Boyun Çizgisi: {format_price(obo['neckline'])}")
                
                # 4H ve 1D boyun çizgisi kırılımı kontrolü
                print(f"\n🔍 4H/1D Boyun Çizgisi Kırılımı Analizi:")
                breakout_info = check_neckline_breakout(symbol, obo['neckline'], 'Short')
                
                for timeframe, info in breakout_info.items():
                    status = "✅ TEYİT EDİLDİ" if info['confirmed'] else "❌ TEYİT EDİLMEDİ"
                    volume_status = "✅ YÜKSEK HACİM" if info['volume_confirmed'] else "⚠️  DÜŞÜK HACİM"
                    print(f"   📊 {timeframe}: {status} | {volume_status}")
                    print(f"      💰 Fiyat: {format_price(info['current_price'])} | Boyun: {format_price(info['neckline_price'])}")
                    print(f"      📈 Kırılım Gücü: %{info['strength']:.2f} | Hacim Oranı: {info['volume_ratio']:.2f}x")
                
                # Hacim teyidi analizi
                print(f"\n📊 Hacim Teyidi Analizi:")
                volume_analysis = analyze_volume_confirmation(symbol)
                
                for timeframe, vol_info in volume_analysis.items():
                    vol_status = "✅ TEYİT EDİLDİ" if vol_info['confirmed'] else "⚠️  DÜŞÜK HACİM"
                    print(f"   📊 {timeframe}: {vol_status} | Trend: {vol_info['volume_trend']}")
                    print(f"      📈 Hacim Oranı: {vol_info['volume_ratio']:.2f}x | Ortalama: {vol_info['avg_volume']:.0f}")
                
                # OBO için risk analizi - Daha güvenli SL
                tp = fibo_levels['0.618']
                # SL'yi daha güvenli seviyede seç - Short için SL > Giriş olmalı
                # Minimum %3 mesafe olmalı
                min_sl_distance = current_price * 1.03  # %3 üstü
                
                # Önce en yüksek Fibonacci seviyesini dene
                if '0.236' in fibo_levels and fibo_levels['0.236'] > min_sl_distance:
                    sl = fibo_levels['0.236']
                elif '0.382' in fibo_levels and fibo_levels['0.382'] > min_sl_distance:
                    sl = fibo_levels['0.382']
                elif '0.5' in fibo_levels and fibo_levels['0.5'] > min_sl_distance:
                    sl = fibo_levels['0.5']
                else:
                    # Hiçbir Fibonacci seviyesi yeterince yukarıda değilse, %5 üstünü kullan
                    sl = current_price * 1.05
                
                # Fiyat henüz boyun çizgisini kırmamışsa, mevcut fiyattan analiz yap
                if current_price > obo['neckline']:
                    entry = current_price
                    print(f"\n💡 OBO Short Fırsatı (Bekleme Modu) - Erken giriş fırsatı!")
                    print(f"   📊 Boyun çizgisi: {format_price(obo['neckline'])}")
                    print(f"   📊 Mevcut fiyat: {format_price(current_price)}")
                    print(f"   📊 Kırılması gereken seviye: {format_price(obo['neckline'])}")
                else:
                    entry = current_price  # Formasyon tamamlandıysa anlık fiyattan giriş
                    print(f"\n💡 OBO Short Fırsatı (Aktif) - Formasyon tamamlandı!")
                    print(f"   📊 Boyun çizgisi: {format_price(obo['neckline'])}")
                    print(f"   📊 Mevcut fiyat: {format_price(current_price)}")
                    print(f"   📊 Formasyon tamamlandı, anlık fiyattan giriş!")
                
                # Formasyon yüksekliği bazlı TP hesaplama (daha tutarlı)
                formation_height = obo['neckline'] - obo['bas']
                tp_formation = entry - formation_height
                
                # Ana TP'yi formasyon yüksekliği ile güncelle
                tp = tp_formation
                
                # SL'yi düzelt - Short için SL > Giriş olmalı
                if sl <= entry:
                    # SL giriş fiyatından düşükse, %3 üstünü kullan
                    sl = entry * 1.03
                
                if tp < entry < sl and (entry - tp) / entry >= 0.01:
                    # 3 TP seviyesi hesaplama
                    print(f"\n🎯 3 TP SEVİYESİ HESAPLAMA:")
                    tp_levels = calculate_three_tp_levels(entry, tp, sl, 'Short', fibo_levels, bb_data, 'OBO')
                    
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                    
                    # TP ve SL optimizasyonu (optimize edilmiş değerleri kullanma)
                    print(f"\n🔧 TP/SL Optimizasyonu:")
                    # Optimize edilmiş değerleri kullanma, orijinal değerleri kullan
                    optimized_tp, optimized_sl, optimized_rr = tp, sl, (entry - tp) / (sl - entry) if sl > entry else 0
                    
                    # R/R oranı kontrolü - Sadece 1.2:1'den yüksek olanları kabul et
                    if optimized_rr >= 1.2:
                        # Optimize edilmiş değerlerle risk analizi
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Short')
                        print(f"   🎯 Giriş: {format_price(entry)}")
                        print(f"   🎯 TP: {format_price(optimized_tp)}")
                        print(f"   🛑 SL: {format_price(optimized_sl)}")
                        print(f"   ⚠️  {risk_analysis['risk_level']} | Kaldıraç: {risk_analysis['leverage']}")
                        print(f"   💵 Pozisyon: {risk_analysis['position_size']} | R/R: {risk_analysis['risk_reward']} ✅")
                        print(f"   🎯 Hedef: {risk_analysis['potential_gain']} potansiyel kazanç")
                        print(f"   🔒 Margin: {risk_analysis['margin_type']} | Risk: {risk_analysis['risk_amount']} | Max Kayıp: {risk_analysis['max_loss']}")
                        
                        # Sinyal verilerini kaydet
                        obo_signal = {
                            'valid': True,
                            'entry': entry,
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'risk_analysis': risk_analysis,
                            'tp_levels': tp_levels
                        }
                    else:
                        print(f"   ❌ R/R oranı yetersiz: {optimized_rr:.2f}:1 (Minimum 1.2:1 gerekli)")
                        obo_signal = {'valid': False}
                else:
                    print(f"   ❌ Risk/Ödül oranı yetersiz (TP: {format_price(tp)}, SL: {format_price(sl)})")
                    obo_signal = {'valid': False}
            
            # Cup and Handle formasyonu analizi
            cup_handle_signal = None
            if dominant_formation == 'CUP_HANDLE' and cup_handle:
                print(f"\n🔄 Cup & Handle formasyonu tespit edildi! (Skor: {cup_handle['score']:.1f})")
                print(f"📊 Fincan Dip: {format_price(cup_handle['cup_bottom_price'])}")
                print(f"📊 Sol Tepe: {format_price(cup_handle['cup_start_price'])}")
                print(f"📊 Sağ Tepe: {format_price(cup_handle['cup_end_price'])}")
                print(f"📊 Kulp Dip: {format_price(cup_handle['handle_bottom_price'])}")
                print(f"📊 Kırılım Noktası: {format_price(cup_handle['breakout_price'])}")
                
                # Durum kontrolleri
                if cup_handle['breakout_confirmed']:
                    print(f"✅ Kırılım Teyit Edildi!")
                else:
                    print(f"⏳ Kırılım Bekleniyor...")
                
                if cup_handle['volume_confirmed']:
                    print(f"✅ Hacim Teyit Edildi! (1.5x+ artış)")
                else:
                    print(f"⚠️  Hacim Teyidi Eksik (1.5x+ gerekli)")
                
                # Cup and Handle için risk analizi
                entry = current_price
                tp = entry * 1.30  # %30 hedef (kullanıcı isteği)
                sl = cup_handle['handle_bottom_price']  # Kulpun dibi stop loss
                
                if tp > entry > sl:
                    # 3 TP seviyesi hesaplama
                    print(f"\n🎯 3 TP SEVİYESİ HESAPLAMA:")
                    tp_levels = calculate_three_tp_levels(entry, tp, sl, 'Long', fibo_levels, bb_data, 'CUP_HANDLE')
                    
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                    
                    # TP ve SL optimizasyonu
                    print(f"\n🔧 TP/SL Optimizasyonu:")
                    optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, bb_data)
                    
                    # R/R oranı kontrolü - Sadece 1.2:1'den yüksek olanları kabul et
                    if optimized_rr >= 1.2:
                        # Optimize edilmiş değerlerle risk analizi
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                        print(f"   🎯 Giriş: {format_price(entry)}")
                        print(f"   🎯 TP: {format_price(optimized_tp)}")
                        print(f"   🛑 SL: {format_price(optimized_sl)}")
                        print(f"   ⚠️  {risk_analysis['risk_level']} | Kaldıraç: {risk_analysis['leverage']}")
                        print(f"   💵 Pozisyon: {risk_analysis['position_size']} | R/R: {risk_analysis['risk_reward']} ✅")
                        print(f"   🎯 Hedef: {risk_analysis['potential_gain']} potansiyel kazanç")
                        print(f"   🔒 Margin: {risk_analysis['margin_type']} | Risk: {risk_analysis['risk_amount']} | Max Kayıp: {risk_analysis['max_loss']}")
                        
                        # Cup and Handle sinyal verilerini kaydet
                        cup_handle_signal = {
                            'valid': True,
                            'entry': entry,
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'risk_analysis': risk_analysis,
                            'tp_levels': tp_levels
                        }
                        
                        print(f"✅ CUP AND HANDLE SİNYALİ GEÇERLİ!")
                    else:
                        print(f"❌ R/R oranı yetersiz: {optimized_rr:.2f}:1 (Minimum 1.2:1 gerekli)")
                        cup_handle_signal = {'valid': False}
                else:
                    print(f"❌ Risk/Ödül oranı yetersiz (TP: {format_price(tp)}, SL: {format_price(sl)})")
                    cup_handle_signal = {'valid': False}
            elif cup_handle is None:
                print(f"\n❌ Cup and Handle formasyonu bulunamadı")
                print(f"   💡 Sebepler:")
                print(f"      - U şeklinde fincan yapısı tespit edilemedi")
                print(f"      - Kulp derinliği %15'ten fazla")
                print(f"      - Hacim artışı 1.5x'den az")
                print(f"      - Kırılım henüz gerçekleşmedi")
            
            # Falling Wedge formasyonu analizi
            falling_wedge_signal = None
            if dominant_formation == 'FALLING_WEDGE' and falling_wedge:
                print(f"\n🔺 Falling Wedge formasyonu tespit edildi! (Skor: {falling_wedge['score']:.1f})")
                print(f"📊 Tepe 1: {format_price(falling_wedge['peaks'][0][1])}")
                print(f"📊 Tepe 2: {format_price(falling_wedge['peaks'][1][1])}")
                print(f"📊 Dip 1: {format_price(falling_wedge['troughs'][0][1])}")
                print(f"📊 Dip 2: {format_price(falling_wedge['troughs'][1][1])}")
                print(f"📈 Kırılım Noktası: {format_price(falling_wedge['breakout_price'])}")
                print(f"🎯 TP: {format_price(falling_wedge['tp'])} | SL: {format_price(falling_wedge['sl'])}")
                
                # Durum kontrolleri
                if falling_wedge['breakout_confirmed']:
                    print(f"✅ Kırılım Teyit Edildi!")
                else:
                    print(f"⏳ Kırılım Bekleniyor...")
                
                if falling_wedge['volume_confirmed']:
                    print(f"✅ Hacim Teyit Edildi! (1.5x+ artış)")
                else:
                    print(f"⚠️  Hacim Teyidi Eksik (1.5x+ gerekli)")
                
                # Falling Wedge için risk analizi
                entry = falling_wedge['entry_price']
                tp = falling_wedge['tp']
                sl = falling_wedge['sl']
                
                if tp > entry > sl:
                    # TP ve SL optimizasyonu
                    print(f"\n🔧 TP/SL Optimizasyonu:")
                    optimized_tp, optimized_sl, optimized_rr = optimize_tp_sl(entry, tp, sl, 'Long', fibo_levels, bb_data)
                    
                    # R/R oranı kontrolü - Sadece 1.2:1'den yüksek olanları kabul et
                    if optimized_rr >= 1.2:
                        # Optimize edilmiş değerlerle risk analizi
                        risk_analysis = calculate_optimal_risk(symbol, entry, optimized_tp, optimized_sl, 'Long')
                        print(f"   🎯 Giriş: {format_price(entry)}")
                        print(f"   🎯 TP: {format_price(optimized_tp)}")
                        print(f"   🛑 SL: {format_price(optimized_sl)}")
                        print(f"   ⚠️  {risk_analysis['risk_level']} | Kaldıraç: {risk_analysis['leverage']}")
                        print(f"   💵 Pozisyon: {risk_analysis['position_size']} | R/R: {risk_analysis['risk_reward']} ✅")
                        print(f"   🎯 Hedef: {risk_analysis['potential_gain']} potansiyel kazanç")
                        print(f"   🔒 Margin: {risk_analysis['margin_type']} | Risk: {risk_analysis['risk_amount']} | Max Kayıp: {risk_analysis['max_loss']}")
                        
                        # Falling Wedge sinyal verilerini kaydet
                        falling_wedge_signal = {
                            'valid': True,
                            'entry': entry,
                            'tp': optimized_tp,
                            'sl': optimized_sl,
                            'risk_analysis': risk_analysis
                        }
                        
                        print(f"✅ FALLING WEDGE SİNYALİ GEÇERLİ!")
                    else:
                        print(f"❌ R/R oranı yetersiz: {optimized_rr:.2f}:1 (Minimum 1.2:1 gerekli)")
                        falling_wedge_signal = {'valid': False}
                else:
                    print(f"❌ Risk/Ödül oranı yetersiz (TP: {format_price(tp)}, SL: {format_price(sl)})")
                    falling_wedge_signal = {'valid': False}
            elif falling_wedge is None:
                print(f"\n❌ Falling Wedge formasyonu bulunamadı")
                print(f"   💡 Sebepler:")
                print(f"      - Alçalan tepe ve dip yapısı tespit edilemedi")
                print(f"      - En az 3 tepe ve 3 dip gerekli")
                print(f"      - Kama sıkışması yeterli değil")
                print(f"      - Üst trend çizgisi kırılımı henüz gerçekleşmedi")
                print(f"      - Hacim artışı 1.5x'den az")
            
            # RSI analizi
            rsi_div = detect_rsi_divergence(df)
            if rsi_div == 'bullish':
                print(f"\n📈 RSI uyumsuzluğu: Bullish (ek long sinyali)")
            elif rsi_div == 'bearish':
                print(f"\n📉 RSI uyumsuzluğu: Bearish (ek short sinyali)")
            else:
                print(f"\n📊 RSI uyumsuzluğu tespit edilmedi.")
            
            # Teknik İndikatörler Analizi
            print(f"\n🔍 Teknik İndikatörler Analizi:")
            
            # MACD Analizi
            if macd_data:
                macd_emoji = "📈" if macd_data['trend'] == 'Bullish' else "📉"
                momentum_emoji = "🚀" if macd_data['momentum'] == 'Increasing' else "📉"
                print(f"   📊 MACD: {macd_emoji} {macd_data['trend']} | {momentum_emoji} {macd_data['momentum']}")
                print(f"      💰 MACD: {macd_data['macd_line']:.6f} | Sinyal: {macd_data['signal_line']:.6f}")
            
            # Bollinger Bands Analizi
            if bb_data:
                bb_emoji = "🔴" if bb_data['signal'] == 'Overbought' else "🟢" if bb_data['signal'] == 'Oversold' else "🟡"
                squeeze_emoji = "⚠️" if bb_data['squeeze'] else "✅"
                print(f"   📊 Bollinger: {bb_emoji} {bb_data['signal']} | {squeeze_emoji} {'Squeeze' if bb_data['squeeze'] else 'Normal'}")
                print(f"      💰 Üst: {format_price(bb_data['upper_band'])} | Alt: {format_price(bb_data['lower_band'])} | Pozisyon: %{bb_data['bb_position']*100:.1f}")
            
            # Stochastic Analizi
            if stoch_data:
                stoch_emoji = "🔴" if stoch_data['signal'] == 'Overbought' else "🟢" if stoch_data['signal'] == 'Oversold' else "🟡"
                crossover_emoji = "📈" if stoch_data['crossover'] == 'Bullish' else "📉" if stoch_data['crossover'] == 'Bearish' else "➡️"
                print(f"   📊 Stochastic: {stoch_emoji} {stoch_data['signal']} | {crossover_emoji} {stoch_data['crossover']}")
                print(f"      📊 %K: {stoch_data['k_percent']:.1f} | %D: {stoch_data['d_percent']:.1f}")
            
            # ADX Analizi
            if adx_data:
                strength_emoji = "🔥" if adx_data['trend_strength'] == 'Strong' else "⚡" if adx_data['trend_strength'] == 'Moderate' else "💤"
                direction_emoji = "📈" if adx_data['trend_direction'] == 'Bullish' else "📉"
                print(f"   📊 ADX: {strength_emoji} {adx_data['trend_strength']} | {direction_emoji} {adx_data['trend_direction']}")
                print(f"      📊 ADX: {adx_data['adx']:.1f} | +DI: {adx_data['plus_di']:.1f} | -DI: {adx_data['minus_di']:.1f}")
            
            # Sinyal Ağırlıklandırma Sistemi
            print(f"\n🎯 Sinyal Ağırlıklandırma Analizi:")
            # dominant_formation None ise varsayılan değer kullan
            formation_type_for_score = dominant_formation if dominant_formation else 'None'
            signal_score = calculate_signal_score(df, formation_type_for_score, None, macd_data, bb_data, stoch_data, adx_data, ma_trend)
            
            # Çelişki durumu
            conflict_emoji = "🔴" if "Yüksek" in signal_score['conflict'] else "🟡" if "Orta" in signal_score['conflict'] else "🟢"
            confidence_emoji = "🔥" if signal_score['confidence'] == 'Yüksek' else "⚡" if signal_score['confidence'] == 'Orta' else "💤"
            
            print(f"   📊 Çelişki Durumu: {conflict_emoji} {signal_score['conflict']}")
            print(f"   📊 Güven Seviyesi: {confidence_emoji} {signal_score['confidence']}")
            print(f"   📊 Final Sinyal: {'📈 LONG' if signal_score['final_signal'] == 'Long' else '📉 SHORT' if signal_score['final_signal'] == 'Short' else '⏸️ BEKLEME'}")
            print(f"   📊 Long Sinyalleri: %{signal_score['long_percentage']:.1f} | Short Sinyalleri: %{signal_score['short_percentage']:.1f}")
            
            # Detaylı sinyal listesi
            print(f"\n📋 Sinyal Detayları:")
            for signal in signal_score['signals']:
                print(f"   ✅ {signal}")
            
            # İndikatör uyumluluğu
            print(f"\n🔍 İndikatör Uyumluluğu:")
            indicators = signal_score['indicator_signals']
            for name, signal in indicators.items():
                emoji = "📈" if signal == 'Long' else "📉" if signal == 'Short' else "➡️"
                print(f"   {emoji} {name.upper()}: {signal}")
            
            rsi_signal_data = None
            rsi_signal = check_rsi(df)
            if rsi_signal:
                print(f"\n⚠️  {symbol} RSI 30'un altına düştü! (Aşırı satım bölgesi)")
                print("   - Fiyat tepki verebilir, izlenmeli.")
                print("   - Long için uygun bir dönüş sinyali beklenebilir.")
                
                # RSI için risk analizi
                son_fiyat = df['close'].iloc[-1]
                tp = None
                for level in ['0.382', '0.236']:
                    if fibo_levels[level] > son_fiyat:
                        tp = fibo_levels[level]
                        break
                if tp is None:
                    tp = fibo_high
                
                sl = None
                for level in ['0.786', '0.618']:
                    if fibo_levels[level] < son_fiyat:
                        sl = fibo_levels[level]
                        break
                if sl is None:
                    sl = fibo_low
                
                if tp > son_fiyat > sl:
                    # R/R oranı hesapla
                    reward_percent = (tp - son_fiyat) / son_fiyat
                    risk_percent = (son_fiyat - sl) / son_fiyat
                    rr_ratio = reward_percent / risk_percent if risk_percent > 0 else 0
                    
                    # R/R oranı kontrolü - Sadece 1.2:1'den yüksek olanları kabul et
                    if rr_ratio >= 1.2:
                        risk_analysis = calculate_optimal_risk(symbol, son_fiyat, tp, sl, 'Long')
                        print(f"\n💡 RSI Long Fırsatı:")
                        print(f"   🎯 Giriş: {format_price(son_fiyat)}")
                        print(f"   🎯 TP: {format_price(tp)}")
                        print(f"   🛑 SL: {format_price(sl)}")
                        print(f"   ⚠️  {risk_analysis['risk_level']} | Kaldıraç: {risk_analysis['leverage']}")
                        print(f"   💵 Pozisyon: {risk_analysis['position_size']} | R/R: {risk_analysis['risk_reward']} ✅")
                        print(f"   🎯 Hedef: {risk_analysis['potential_gain']} potansiyel kazanç")
                        print(f"   🔒 Margin: {risk_analysis['margin_type']} | Risk: {risk_analysis['risk_amount']} | Max Kayıp: {risk_analysis['max_loss']}")
                        
                        # RSI sinyal verilerini kaydet
                        rsi_signal_data = {
                            'valid': True,
                            'entry': son_fiyat,
                            'tp': tp,
                            'sl': sl,
                            'risk_analysis': risk_analysis
                        }
                    else:
                        print(f"   ❌ RSI R/R oranı yetersiz: {rr_ratio:.2f}:1 (Minimum 1.2:1 gerekli)")
                        rsi_signal_data = {'valid': False}
                else:
                    rsi_signal_data = {'valid': False}
            else:
                rsi_signal_data = {'valid': False}
            
            # Action plan'ı başlangıçta tanımla
            action_plan = {
                'immediate_action': 'BEKLE',
                'entry_price': current_price,
                'tp_price': current_price,
                'sl_price': current_price,
                'reason': 'Formasyon yetersiz'
            }
            
            # Final sinyal önerisi - DÜZELTİLMİŞ
            print(f"\n🎯 FİNAL SİNYAL ÖNERİSİ:")
            
            # Güven seviyesi kontrolü - DÜZELTİLMİŞ
            if signal_score['confidence'] == 'Düşük':
                print(f"   ⏸️  BEKLEME MODU - Düşük güven seviyesi")
                print(f"   💡 Öneri: Daha net sinyal bekleyin")
                print(f"   📊 Sebep: Güven seviyesi çok düşük (%{signal_score['long_percentage']:.1f} Long, %{signal_score['short_percentage']:.1f} Short)")
                action_plan['immediate_action'] = 'BEKLEME MODU'
                action_plan['reason'] = 'Düşük güven seviyesi'
                
            elif signal_score['conflict'] == 'Yüksek Çelişki':
                print(f"   ⏸️  BEKLEME MODU - Yüksek çelişki")
                print(f"   💡 Öneri: Daha net sinyal bekleyin")
                print(f"   📊 Sebep: Çelişkili sinyaller (%{signal_score['long_percentage']:.1f} Long, %{signal_score['short_percentage']:.1f} Short)")
                action_plan['immediate_action'] = 'BEKLEME MODU'
                action_plan['reason'] = 'Yüksek çelişki'
                
            # Botanlik.py ile aynı basit mantık - Sadece yüksek güven için
            elif dominant_formation == 'TOBO' and tobo_signal and tobo_signal.get('valid') and signal_score['confidence'] in ['Orta', 'Yüksek']:
                print(f"   📈 LONG GİRİŞ - TOBO Formasyonu")
                print(f"   🎯 Giriş: {format_price(tobo_signal['entry'])}")
                print(f"   🎯 TP: {format_price(tobo_signal['tp'])}")
                print(f"   🛑 SL: {format_price(tobo_signal['sl'])}")
                print(f"   ⚡ Kaldıraç: 5x")
                print(f"   💵 Pozisyon: Kasanın %5'i")
                print(f"   📊 R/R: {tobo_signal['risk_analysis']['risk_reward']}")
                print(f"   🎯 Hedef: {tobo_signal['risk_analysis']['potential_gain']}")
                print(f"   🔒 Margin: {tobo_signal['risk_analysis']['margin_type']} | Risk: {tobo_signal['risk_analysis']['risk_amount']}")
                print(f"   ⚡ Sinyal Gücü: {signal_score['confidence'].upper()} (%{signal_score['long_percentage']:.1f})")
                print(f"   ✅ FUTURES İŞLEM AÇILABİLİR!")
                
                # Action plan'ı güncelle
                action_plan['immediate_action'] = 'LONG GİR'
                action_plan['entry_price'] = tobo_signal['entry']
                action_plan['tp_price'] = tobo_signal['tp']
                action_plan['sl_price'] = tobo_signal['sl']
                action_plan['reason'] = f'TOBO Formasyonu - {signal_score["confidence"]} Long Sinyali'
                
            elif dominant_formation == 'OBO' and obo_signal and obo_signal.get('valid') and signal_score['confidence'] in ['Orta', 'Yüksek']:
                print(f"   📉 SHORT GİRİŞ - OBO Formasyonu")
                print(f"   🎯 Giriş: {format_price(obo_signal['entry'])}")
                print(f"   🎯 TP: {format_price(obo_signal['tp'])}")
                print(f"   🛑 SL: {format_price(obo_signal['sl'])}")
                print(f"   ⚡ Kaldıraç: 5x")
                print(f"   💵 Pozisyon: Kasanın %5'i")
                print(f"   📊 R/R: {obo_signal['risk_analysis']['risk_reward']}")
                print(f"   🎯 Hedef: {obo_signal['risk_analysis']['potential_gain']}")
                print(f"   🔒 Margin: {obo_signal['risk_analysis']['margin_type']} | Risk: {obo_signal['risk_analysis']['risk_amount']}")
                print(f"   ⚡ Sinyal Gücü: {signal_score['confidence'].upper()} (%{signal_score['short_percentage']:.1f})")
                print(f"   ✅ FUTURES İŞLEM AÇILABİLİR!")
                
                # Action plan'ı güncelle
                action_plan['immediate_action'] = 'SHORT GİR'
                action_plan['entry_price'] = obo_signal['entry']
                action_plan['tp_price'] = obo_signal['tp']
                action_plan['sl_price'] = obo_signal['sl']
                action_plan['reason'] = f'OBO Formasyonu - {signal_score["confidence"]} Short Sinyali'
                
            else:
                print(f"   ⏸️  BEKLEME MODU - Uygun formasyon bulunamadı")
                print(f"   💡 Öneri: Daha net sinyal bekleyin")
                print(f"   📊 Sebep: Formasyon yetersiz veya güven seviyesi düşük")
                action_plan['immediate_action'] = 'BEKLEME MODU'
                action_plan['reason'] = 'Formasyon yetersiz veya geçersiz'
            
            print(f"\n🔍 AĞIRLIKLANDIRMA SONUCU:")
            print(f"   📊 Formasyon: {signal_score['formation_signal']}")
            print(f"   📊 İndikatörler: %{signal_score['long_percentage']:.1f} Long | %{signal_score['short_percentage']:.1f} Short")
            print(f"   📊 Final Karar: {signal_score['final_signal']} ({signal_score['confidence']} güven)")
            
            # Formasyon bilgileri
            if formations:
                print(f"\n📊 Formasyon Bilgileri:")
                print(f"   🛡️  Destek: {format_price(formations['support'])}")
                print(f"   🚧 Direnç: {format_price(formations['resistance'])}")
                if formations['kanal_var']:
                    print(f"   📈 Kanal formasyonu: {formations['kanal_yonu']}")
                else:
                    print(f"   ❌ Kanal formasyonu tespit edilmedi.")
            
            # Anlık fiyatı en altta tekrar yazdır
            print(f"\n💰 Anlık fiyat (güncel): {format_price(current_price)}")
            
            # Kapsamlı trading senaryoları analizi
            formation_data = tobo if dominant_formation == 'TOBO' else obo if dominant_formation == 'OBO' else None
            scenarios, action_plan = analyze_trading_scenarios(df, dominant_formation, formation_data, current_price, fibo_levels, bb_data, signal_score)
            
            # Optimize edilmiş değerleri action_plan'a aktar
            if signal_score['final_signal'] == 'Long' and tobo_signal and tobo_signal['valid']:
                action_plan['entry_price'] = tobo_signal['entry']
                action_plan['tp_price'] = tobo_signal['tp']
                action_plan['sl_price'] = tobo_signal['sl']
                print(f"\n🔧 Optimize edilmiş değerler action_plan'a aktarıldı:")
                print(f"   Giriş: {format_price(tobo_signal['entry'])}")
                print(f"   TP: {format_price(tobo_signal['tp'])}")
                print(f"   SL: {format_price(tobo_signal['sl'])}")
            elif signal_score['final_signal'] == 'Short' and obo_signal and obo_signal['valid']:
                action_plan['entry_price'] = obo_signal['entry']
                action_plan['tp_price'] = obo_signal['tp']
                action_plan['sl_price'] = obo_signal['sl']
                print(f"\n🔧 Optimize edilmiş değerler action_plan'a aktarıldı:")
                print(f"   Giriş: {format_price(obo_signal['entry'])}")
                print(f"   TP: {format_price(obo_signal['tp'])}")
                print(f"   SL: {format_price(obo_signal['sl'])}")
            
            print_trading_summary(action_plan, scenarios, signal_score)
            
            # FUTURES TRADING ANALİZİ - OPTİMİZE EDİLMİŞ ÇIKTI
            print(f"\n" + "="*80)
            print(f"🎯 FUTURES TRADING ANALİZİ - {symbol}")
            print(f"="*80)
            
            # 1. ANLIK FİYAT VE TEMEL BİLGİLER
            print(f"\n💰 ANLIK FİYAT: {format_price(current_price)}")
            print(f"📊 Fibonacci Seviyeleri:")
            print(f"   🔺 En Yüksek: {format_price(fibo_high)} | 🔻 En Düşük: {format_price(fibo_low)}")
            print(f"   📈 0.236: {format_price(fibo_levels['0.236'])} | 0.382: {format_price(fibo_levels['0.382'])}")
            print(f"   📉 0.618: {format_price(fibo_levels['0.618'])} | 0.786: {format_price(fibo_levels['0.786'])}")
            
            # 2. TEKNİK TREND VE FORMASYONLAR
            print(f"\n📈 TEKNİK TREND VE FORMASYONLAR:")
            print(f"   📊 MA Trend: {ma_trend}")
            
            # MA değerlerini hesapla
            ma7 = df['close'].rolling(window=7).mean().iloc[-1]
            ma25 = df['close'].rolling(window=25).mean().iloc[-1]
            ma50 = df['close'].rolling(window=50).mean().iloc[-1]
            ma99 = df['close'].rolling(window=99).mean().iloc[-1]
            
            print(f"   📊 MA7: {format_price(ma7)} | MA25: {format_price(ma25)} | MA50: {format_price(ma50)} | MA99: {format_price(ma99)}")
            
            # Formasyon bilgilerini al
            all_tobo = find_all_tobo(df)
            all_obo = find_all_obo(df)
            
            tobo = all_tobo[-1] if all_tobo else None
            obo = all_obo[-1] if all_obo else None
            
            if dominant_formation == 'TOBO' and tobo:
                print(f"   🔄 TOBO Formasyonu: Sol Omuz {format_price(tobo['sol_omuz'])} | Baş {format_price(tobo['bas'])} | Sağ Omuz {format_price(tobo['sag_omuz'])}")
                print(f"   📊 Boyun Çizgisi: {format_price(tobo['neckline'])} | Durum: {'Aktif' if current_price > tobo['neckline'] else 'Bekleme'}")
            elif dominant_formation == 'OBO' and obo:
                print(f"   🔄 OBO Formasyonu: Sol Omuz {format_price(obo['sol_omuz'])} | Baş {format_price(obo['bas'])} | Sağ Omuz {format_price(obo['sag_omuz'])}")
                print(f"   📊 Boyun Çizgisi: {format_price(obo['neckline'])} | Durum: {'Aktif' if current_price < obo['neckline'] else 'Bekleme'}")
            
            # 3. HACİM TEYİDİ VE KIRILIM GÜCÜ (Opsiyonel - botanlik.py gibi)
            print(f"\n📊 HACİM TEYİDİ VE KIRILIM GÜCÜ:")
            neckline_price = None
            if dominant_formation == 'TOBO' and tobo:
                neckline_price = tobo['neckline']
            elif dominant_formation == 'OBO' and obo:
                neckline_price = obo['neckline']
                
            if neckline_price:
                breakout_info = check_neckline_breakout(symbol, neckline_price, 'Long' if dominant_formation == 'TOBO' else 'Short')
                for tf, info in breakout_info.items():
                    status = "✅ TEYİT EDİLDİ" if info['confirmed'] else "❌ TEYİT EDİLMEDİ"
                    volume_status = "✅ YÜKSEK HACİM" if info['volume_confirmed'] else "⚠️ DÜŞÜK HACİM"
                    print(f"   📊 {tf.upper()}: {status} | {volume_status}")
                    print(f"      💰 Kırılım Gücü: %{info['strength']:.2f} | Hacim Oranı: {info['volume_ratio']:.2f}x")
                    
                # Hacim teyidi olmasa bile işlem önerisi ver (botanlik.py mantığı)
                print(f"   💡 Not: Hacim teyidi olmasa bile teknik analiz yeterli olabilir")
            
            # 4. TEKNİK İNDİKATÖRLER
            print(f"\n🔍 TEKNİK İNDİKATÖRLER:")
            if macd_data:
                trend_emoji = "📈" if macd_data['trend'] == 'Bullish' else "📉"
                momentum_emoji = "🔥" if macd_data['momentum'] == 'Increasing' else "💤"
                print(f"   📊 MACD: {trend_emoji} {macd_data['trend']} | {momentum_emoji} {macd_data['momentum']}")
            
            if bb_data:
                signal_emoji = "🟢" if bb_data['signal'] == 'Oversold' else "🔴" if bb_data['signal'] == 'Overbought' else "🟡"
                print(f"   📊 Bollinger: {signal_emoji} {bb_data['signal']} | Pozisyon: %{bb_data['bb_position']*100:.1f}")
            
            if stoch_data:
                k_emoji = "🟢" if stoch_data['signal'] == 'Oversold' else "🔴" if stoch_data['signal'] == 'Overbought' else "🟡"
                print(f"   📊 Stochastic: {k_emoji} %K: {stoch_data['k_percent']:.1f} | %D: {stoch_data['d_percent']:.1f}")
            
            if adx_data:
                strength_emoji = "🔥" if adx_data['trend_strength'] == 'Strong' else "⚡"
                print(f"   📊 ADX: {strength_emoji} {adx_data['trend_strength']} | {adx_data['trend_direction']}")
            
            # 5. KALDIRAÇ VE POZİSYON BÜYÜKLÜĞÜ ÖNERİSİ
            print(f"\n⚡ KALDIRAÇ VE POZİSYON BÜYÜKLÜĞÜ:")
            if action_plan['immediate_action'] in ['LONG GİR', 'SHORT GİR']:
                # Risk/Ödül hesaplama
                if action_plan['immediate_action'] == 'LONG GİR':
                    risk = (action_plan['entry_price'] - action_plan['sl_price']) / action_plan['entry_price']
                    reward = (action_plan['tp_price'] - action_plan['entry_price']) / action_plan['entry_price']
                else:
                    risk = (action_plan['sl_price'] - action_plan['entry_price']) / action_plan['entry_price']
                    reward = (action_plan['entry_price'] - action_plan['tp_price']) / action_plan['entry_price']
                
                rr_ratio = reward / risk if risk > 0 else 0
                
                # Kaldıraç önerisi (Güvenli seviyeler)
                if rr_ratio >= 5 and signal_score['confidence'] == 'Yüksek':
                    leverage = "8x-12x"
                    position_size = "Kasanın %6-8'i"
                    risk_level = "Orta Risk"
                elif rr_ratio >= 3:
                    leverage = "5x-8x"
                    position_size = "Kasanın %4-6'i"
                    risk_level = "Düşük Risk"
                elif rr_ratio >= 2:
                    leverage = "3x-5x"
                    position_size = "Kasanın %3-4'i"
                    risk_level = "Çok Düşük Risk"
                else:
                    leverage = "2x-3x"
                    position_size = "Kasanın %2-3'i"
                    risk_level = "Minimal Risk"
                
                print(f"   ⚡ Önerilen Kaldıraç: {leverage}")
                print(f"   💵 Pozisyon Büyüklüğü: {position_size}")
                print(f"   ⚠️  Risk Seviyesi: {risk_level}")
                print(f"   🔒 Margin Türü: ISOLATED (Önerilen)")
                print(f"   📊 Maksimum Risk: %{risk*100:.1f} | Potansiyel Kazanç: %{reward*100:.1f}")
            else:
                print(f"   ⏸️  İşlem önerisi yok - Bekleme modu")
            
            # 6. STOP LOSS VE TAKE PROFIT SEVİYELERİ
            print(f"\n🎯 STOP LOSS VE TAKE PROFIT:")
            if action_plan['immediate_action'] in ['LONG GİR', 'SHORT GİR']:
                print(f"   💰 Giriş Fiyatı: {format_price(action_plan['entry_price'])}")
                print(f"   🎯 Take Profit: {format_price(action_plan['tp_price'])}")
                print(f"   🛑 Stop Loss: {format_price(action_plan['sl_price'])}")
                print(f"   📊 Risk/Ödül Oranı: {rr_ratio:.2f}:1")
                
                # 3 TP seviyesi gösterimi
                if 'best_signal' in locals() and best_signal and 'tp_levels' in best_signal:
                    tp_levels = best_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'tobo_signal' in locals() and tobo_signal and tobo_signal.get('valid') and 'tp_levels' in tobo_signal:
                    tp_levels = tobo_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'obo_signal' in locals() and obo_signal and obo_signal.get('valid') and 'tp_levels' in obo_signal:
                    tp_levels = obo_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'cup_handle_signal' in locals() and cup_handle_signal and cup_handle_signal.get('valid') and 'tp_levels' in cup_handle_signal:
                    tp_levels = cup_handle_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                
                # Giriş zamanlaması
                if dominant_formation in ['TOBO', 'OBO']:
                    neckline = None
                    if dominant_formation == 'TOBO' and tobo:
                        neckline = tobo['neckline']
                    elif dominant_formation == 'OBO' and obo:
                        neckline = obo['neckline']
                        
                    if neckline:
                        if dominant_formation == 'TOBO' and current_price > neckline:
                            timing = "✅ BOYUN KIRILDI - HEMEN GİR"
                        elif dominant_formation == 'OBO' and current_price < neckline:
                            timing = "✅ BOYUN KIRILDI - HEMEN GİR"
                        else:
                            timing = "⏳ BOYUN KIRILIMI BEKLENİYOR"
                    else:
                        timing = "📊 FORMASYON BEKLENİYOR"
                else:
                    timing = "📊 FORMASYON BEKLENİYOR"
                
                print(f"   ⏰ Giriş Zamanlaması: {timing}")
            else:
                print(f"   ⏸️  İşlem önerisi yok")
            
            # 7. POTANSİYEL SENARYOLAR VE UYARILAR (Daha esnek - botanlik.py gibi)
            print(f"\n⚠️  POTANSİYEL SENARYOLAR VE UYARILAR:")
            if action_plan['immediate_action'] in ['LONG GİR', 'SHORT GİR']:
                print(f"   📈 En İyi Senaryo: {action_plan['reason']}")
                print(f"   📊 Güven Seviyesi: {signal_score['confidence']}")
                print(f"   ⚠️  Çelişki Durumu: {signal_score['conflict']}")
                
                # Risk uyarıları (Daha esnek)
                if signal_score['conflict'] == 'Yüksek Çelişki':
                    print(f"   ⚠️  UYARI: Çelişkili sinyaller - Küçük pozisyon önerilir")
                if rr_ratio < 1.0:
                    print(f"   ⚠️  UYARI: Düşük R/R oranı - Risk yüksek!")
                elif rr_ratio < 1.5:
                    print(f"   💡 UYARI: Orta R/R oranı - Normal risk")
                else:
                    print(f"   ✅ Mükemmel R/R oranı - Düşük risk")
                
                if signal_score['confidence'] == 'Düşük':
                    print(f"   💡 UYARI: Düşük güven seviyesi - Küçük pozisyon!")
                elif signal_score['confidence'] == 'Orta':
                    print(f"   💡 Orta güven seviyesi - Normal pozisyon")
                else:
                    print(f"   ✅ Yüksek güven seviyesi - Büyük pozisyon")
                
                # Piyasa koşulları
                print(f"   📊 Piyasa Koşulu: {'Volatil' if bb_data and bb_data.get('squeeze', False) else 'Normal'}")
                print(f"   📈 Trend Gücü: {'Güçlü' if adx_data and adx_data['trend_strength'] == 'Strong' else 'Zayıf'}")
            else:
                print(f"   💡 Öneri: Daha net sinyal bekleyin")
                print(f"   📊 Sebep: {action_plan.get('reason', 'Çelişkili sinyaller')}")
                print(f"   💡 Not: botanlik.py daha esnek sinyaller verebilir")
            
            # 8. SON KARAR
            print(f"\n" + "="*80)
            print(f"🎯 SON KARAR:")
            if action_plan['immediate_action'] == 'LONG GİR':
                print(f"   📈 LONG GİRİŞ - {signal_score['confidence']} GÜVEN")
                print(f"   💰 Giriş: {format_price(action_plan['entry_price'])}")
                print(f"   🎯 TP: {format_price(action_plan['tp_price'])}")
                print(f"   🛑 SL: {format_price(action_plan['sl_price'])}")
                print(f"   ⚡ Kaldıraç: 5x")
                print(f"   💵 Pozisyon: Kasanın %5'i")
                print(f"   📊 R/R: {rr_ratio:.2f}:1")
                
                # 3 TP seviyesi gösterimi
                if 'best_signal' in locals() and best_signal and 'tp_levels' in best_signal:
                    tp_levels = best_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'tobo_signal' in locals() and tobo_signal and tobo_signal.get('valid') and 'tp_levels' in tobo_signal:
                    tp_levels = tobo_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'obo_signal' in locals() and obo_signal and obo_signal.get('valid') and 'tp_levels' in obo_signal:
                    tp_levels = obo_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'cup_handle_signal' in locals() and cup_handle_signal and cup_handle_signal.get('valid') and 'tp_levels' in cup_handle_signal:
                    tp_levels = cup_handle_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                
            elif action_plan['immediate_action'] == 'SHORT GİR':
                print(f"   📉 SHORT GİRİŞ - {signal_score['confidence']} GÜVEN")
                print(f"   💰 Giriş: {format_price(action_plan['entry_price'])}")
                print(f"   🎯 TP: {format_price(action_plan['tp_price'])}")
                print(f"   🛑 SL: {format_price(action_plan['sl_price'])}")
                print(f"   ⚡ Kaldıraç: 5x")
                print(f"   💵 Pozisyon: Kasanın %5'i")
                print(f"   📊 R/R: {rr_ratio:.2f}:1")
                
                # 3 TP seviyesi gösterimi (Short için)
                if 'best_signal' in locals() and best_signal and 'tp_levels' in best_signal:
                    tp_levels = best_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'tobo_signal' in locals() and tobo_signal and tobo_signal.get('valid') and 'tp_levels' in tobo_signal:
                    tp_levels = tobo_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'obo_signal' in locals() and obo_signal and obo_signal.get('valid') and 'tp_levels' in obo_signal:
                    tp_levels = obo_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                elif 'cup_handle_signal' in locals() and cup_handle_signal and cup_handle_signal.get('valid') and 'tp_levels' in cup_handle_signal:
                    tp_levels = cup_handle_signal['tp_levels']
                    print(f"\n🎯 3 TP SEVİYESİ:")
                    print(f"   🎯 TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                    print(f"   🎯 TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                    print(f"   🎯 TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                
            else:
                print(f"   ⏸️  BEKLE - UYGUN İŞLEM BULUNMUYOR")
                print(f"   💡 Öneri: Daha net sinyal bekleyin")
            print(f"="*80)
            
            # --- YENİ İNDİKATÖR ANALİZLERİ (4H ve 1D) ---
            ind_results = {}
            for tf in ['4h', '1d']:
                df_tf = fetch_ohlcv(symbol, tf)
                if df_tf is not None and not df_tf.empty:
                    ind_results[tf] = {
                        'ichimoku': calculate_ichimoku(df_tf),
                        'supertrend': calculate_supertrend(df_tf),
                        'vwap': calculate_vwap(df_tf),
                        'obv': calculate_obv(df_tf),
                        'heikin_ashi': calculate_heikin_ashi(df_tf)
                    }
            # Konsol çıktısı örneği
            for tf in ind_results:
                print(f"\n[{symbol} - {tf.upper()}] İndikatörler:")
                ichi = ind_results[tf]['ichimoku']
                if ichi:
                    print(f"  Ichimoku: {ichi['signal']} | Tenkan-Kijun: {ichi['tenkan_kijun_cross']} | Bulut: {ichi['cloud_bottom']:.2f}-{ichi['cloud_top']:.2f}")
                st = ind_results[tf]['supertrend']
                if st:
                    print(f"  Supertrend: {st['signal']} | Band: {st['lowerband']:.2f}-{st['upperband']:.2f}")
                vwap = ind_results[tf]['vwap']
                if vwap:
                    print(f"  VWAP: {vwap['signal']} | VWAP: {vwap['vwap']:.2f} | Fiyat: {vwap['price']:.2f}")
                obv = ind_results[tf]['obv']
                if obv:
                    print(f"  OBV: {obv['obv_trend']} | Fiyat trendi: {obv['price_trend']} | Diverjans: {obv['divergence']}")
                ha = ind_results[tf]['heikin_ashi']
                if ha:
                    print(f"  Heikin Ashi trend: {ha['trend']} | HA Close: {ha['ha_close']:.2f}")
            
            # --- SİNYAL AĞIRLIKLANDIRMA ve KARAR SİSTEMİ ---
            signal_score = 0
            signal_details = []
            # Formasyonlar
            if formation_signal and 'type' in formation_signal:
                ftype = formation_signal['type']
                if 'DOUBLE_BOTTOM' in ftype:
                    signal_score += 20
                    signal_details.append('Double Bottom: +20')
                if 'DOUBLE_TOP' in ftype:
                    signal_score += 20
                    signal_details.append('Double Top: +20')
                if 'BULLISH_FLAG' in ftype:
                    signal_score += 15
                    signal_details.append('Bullish Flag: +15')
                if 'BEARISH_FLAG' in ftype:
                    signal_score += 15
                    signal_details.append('Bearish Flag: +15')
                if 'ASCENDING_TRIANGLE' in ftype:
                    signal_score += 10
                    signal_details.append('Ascending Triangle: +10')
                if 'DESCENDING_TRIANGLE' in ftype:
                    signal_score += 10
                    signal_details.append('Descending Triangle: +10')
                if 'SYMMETRICAL_TRIANGLE' in ftype:
                    signal_score += 10
                    signal_details.append('Symmetrical Triangle: +10')
                if 'RISING_WEDGE' in ftype:
                    signal_score += 10
                    signal_details.append('Rising Wedge: +10')
                if 'FALLING_WEDGE' in ftype:
                    signal_score += 10
                    signal_details.append('Falling Wedge: +10')
                if 'RISING' in ftype and 'CHANNEL' in ftype:
                    signal_score += 8
                    signal_details.append('Rising Channel: +8')
                if 'FALLING' in ftype and 'CHANNEL' in ftype:
                    signal_score += 8
                    signal_details.append('Falling Channel: +8')
                if 'HORIZONTAL' in ftype and 'CHANNEL' in ftype:
                    signal_score += 8
                    signal_details.append('Horizontal Channel: +8')
            # İndikatörler (4H ve 1D)
            for tf in ind_results:
                ichi = ind_results[tf]['ichimoku']
                if ichi and ichi['signal'] == 'bullish':
                    signal_score += 15
                    signal_details.append(f'Ichimoku ({tf}) bullish: +15')
                if ichi and ichi['signal'] == 'bearish':
                    signal_score -= 15
                    signal_details.append(f'Ichimoku ({tf}) bearish: -15')
                st = ind_results[tf]['supertrend']
                if st and st['signal'] == 'buy':
                    signal_score += 10
                    signal_details.append(f'Supertrend ({tf}) BUY: +10')
                if st and st['signal'] == 'sell':
                    signal_score -= 10
                    signal_details.append(f'Supertrend ({tf}) SELL: -10')
                vwap = ind_results[tf]['vwap']
                if vwap and vwap['signal'] == 'above':
                    signal_score += 10
                    signal_details.append(f'VWAP ({tf}) üstü: +10')
                if vwap and vwap['signal'] == 'below':
                    signal_score -= 10
                    signal_details.append(f'VWAP ({tf}) altı: -10')
                obv = ind_results[tf]['obv']
                if obv and not obv['divergence']:
                    signal_score += 5
                    signal_details.append(f'OBV ({tf}) uyumlu: +5')
                if obv and obv['divergence']:
                    signal_score -= 5
                    signal_details.append(f'OBV ({tf}) uyumsuz: -5')
                ha = ind_results[tf]['heikin_ashi']
                if ha and ha['trend'] == 'bullish':
                    signal_score += 5
                    signal_details.append(f'Heikin Ashi ({tf}) bullish: +5')
                if ha and ha['trend'] == 'bearish':
                    signal_score -= 5
                    signal_details.append(f'Heikin Ashi ({tf}) bearish: -5')
            # Hacim teyidi
            if formation_signal and formation_signal.get('volume_confirmed'):
                signal_score += 10
                signal_details.append('Hacim teyidi: +10')
            # Karar
            if signal_score >= 30:
                karar = 'LONG'
            elif signal_score <= -30:
                karar = 'SHORT'
            else:
                karar = 'BEKLE'
            # Dinamik risk ve kaldıraç önerisi
            if signal_score >= 60:
                risk_pct = 3
                leverage = 5
                risk_text = 'Yüksek güven: %3 risk, 5x kaldıraç'
            elif signal_score >= 30:
                risk_pct = 2
                leverage = 3
                risk_text = 'Orta güven: %2 risk, 3x kaldıraç'
            elif signal_score <= -60:
                risk_pct = 3
                leverage = 5
                risk_text = 'Yüksek güven (short): %3 risk, 5x kaldıraç'
            elif signal_score <= -30:
                risk_pct = 2
                leverage = 3
                risk_text = 'Orta güven (short): %2 risk, 3x kaldıraç'
            else:
                risk_pct = 1
                leverage = 1
                risk_text = 'Düşük güven: %1 risk, 1x kaldıraç (bekle)'
            print(f"\n🎯 Sinyal Skoru: {signal_score} | Karar: {karar}")
            print('Detaylar:')
            for det in signal_details:
                print(f"  - {det}")
            if karar != 'BEKLE':
                print(f"Pozisyon önerisi: {karar} | {risk_text}")
                # --- İşlem Detayları ---
                entry = None
                tp = None
                sl = None
                rr = None
                risk_analysis = None
                tp_levels = None
                if formation_signal and 'entry_price' in formation_signal:
                    entry = formation_signal['entry_price']
                elif 'entry' in locals():
                    entry = entry
                if formation_signal and 'tp' in formation_signal:
                    tp = formation_signal['tp']
                if formation_signal and 'sl' in formation_signal:
                    sl = formation_signal['sl']
                mantikli = True
                if entry and tp and sl:
                    if karar == 'LONG':
                        mantikli = tp > entry > sl
                        rr = (tp - entry) / (entry - sl) if (entry - sl) > 0 else None
                    else:
                        mantikli = tp < entry < sl
                        rr = (entry - tp) / (sl - entry) if (sl - entry) > 0 else None
                else:
                    mantikli = False
                if not mantikli:
                    karar = 'BEKLE'
                    print("   ⚠️  UYARI: Pozisyon parametreleri mantıksız! TP, giriş ve SL sıralaması yanlış. İşlem önerilmiyor, bekleme modu.")
                    print("Kırılım teyitsiz veya sinyal zayıf, bekleme modu önerilir.")
                else:
                    print(f"Pozisyon önerisi: {karar} | {risk_text}")
                    print(f"   🎯 Giriş: {format_price(entry) if entry else 'Bilgi yok'}")
                    print(f"   🎯 TP: {format_price(tp) if tp else 'Bilgi yok'}")
                    print(f"   🛑 SL: {format_price(sl) if sl else 'Bilgi yok'}")
                    print(f"   📊 R/R Oranı: {rr:.2f}:1" if rr else "   📊 R/R Oranı: Hesaplanamadı")
                    print(f"   ⚡ Kaldıraç: {leverage}x | Pozisyon: %{risk_pct} risk")
                    if entry and tp and sl:
                        if karar == 'LONG':
                            hedef = (tp - entry) / entry * 100
                            risk = (entry - sl) / entry * 100
                        else:
                            hedef = (entry - tp) / entry * 100
                            risk = (sl - entry) / entry * 100
                        print(f"   🎯 Hedef: %{hedef:.2f} | Risk: %{risk:.2f}")
                    if 'tp_levels' in locals() and tp_levels:
                        print(f"   🎯 3 TP SEVİYESİ:")
                        print(f"      TP1 (İlk Kâr): {format_price(tp_levels['tp1']['price'])} ({tp_levels['tp1']['level']}) | +%{tp_levels['tp1']['gain']:.1f}")
                        print(f"      TP2 (Orta Kâr): {format_price(tp_levels['tp2']['price'])} ({tp_levels['tp2']['level']}) | +%{tp_levels['tp2']['gain']:.1f}")
                        print(f"      TP3 (Maksimum): {format_price(tp_levels['tp3']['price'])} ({tp_levels['tp3']['level']}) | +%{tp_levels['tp3']['gain']:.1f}")
                    else:
                        print("   🎯 3 TP SEVİYESİ: Hesaplanamadı.")
            else:
                print("Kırılım teyitsiz veya sinyal zayıf, bekleme modu önerilir.")
            
        except Exception as e:
            import traceback
            print(f'❌ Hata oluştu: {e}')
            print(f'🔍 Hata detayı: {traceback.format_exc()}')
        
        print("\n⏰ Yeni bir coin için Enter'a basın, çıkmak için ESC'ye basın...")
        key = msvcrt.getch()
        if key == b'\x1b':  # ESC
            print('👋 Çıkılıyor...')
            break

if __name__ == "__main__":
    main() 