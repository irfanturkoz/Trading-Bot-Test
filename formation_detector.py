# formation_detector.py
import numpy as np
import pandas as pd


def detect_formations(df, window=20, tolerance=0.5):
    """
    Son window kadar mumda destek (alt trend) ve direnç (üst trend) çizgilerini tespit eder.
    Kanal olup olmadığını ve kanalın yönünü (yükselen/düşen) belirler.
    """
    if len(df) < window:
        return None
    lows = df['low'][-window:]
    highs = df['high'][-window:]
    support = lows.min()
    resistance = highs.max()
    
    # Kanal kontrolü: fiyatlar destek ve direnç arasında mı hareket ediyor?
    kanal = np.all((df['low'][-window:] > support - tolerance) & (df['high'][-window:] < resistance + tolerance))

    # Kanal yönü: destek ve direnç çizgilerinin eğimi
    kanal_yonu = None
    if kanal:
        # Basit doğrusal regresyon ile eğim bul
        x = np.arange(window)
        support_fit = np.polyfit(x, lows.values, 1)
        resistance_fit = np.polyfit(x, highs.values, 1)
        support_slope = support_fit[0]
        resistance_slope = resistance_fit[0]
        # Ortalama eğim
        avg_slope = (support_slope + resistance_slope) / 2
        if avg_slope > 0.01:
            kanal_yonu = 'Yükselen Kanal'
        elif avg_slope < -0.01:
            kanal_yonu = 'Düşen Kanal'
        else:
            kanal_yonu = 'Yatay Kanal'
    
    formations = {
        'support': support,
        'resistance': resistance,
        'kanal_var': kanal,
        'kanal_yonu': kanal_yonu
    }
    return formations 


def calculate_fibonacci_levels(df, window=20):
    """
    Son window içindeki en yüksek ve en düşük fiyatlara göre fibonacci düzeltme seviyelerini hesaplar.
    """
    high = df['high'][-window:].max()
    low = df['low'][-window:].min()
    diff = high - low
    levels = {
        '0.236': high - diff * 0.236,
        '0.382': high - diff * 0.382,
        '0.5': high - diff * 0.5,
        '0.618': high - diff * 0.618,
        '0.786': high - diff * 0.786,
    }
    return levels, high, low


def detect_rsi_divergence(df, rsi_period=14, window=20):
    """
    RSI uyumsuzluğunu tespit eder. Bullish divergence (long) veya bearish divergence (short) döndürür.
    """
    if len(df) < window + rsi_period:
        return None
    close = df['close'][-window:]
    rsi = get_rsi(df['close'], period=rsi_period)[-window:]
    # Fiyat ve RSI'da dip/tepe noktalarını bul
    price_min_idx = np.argmin(close)
    price_max_idx = np.argmax(close)
    rsi_min_idx = np.argmin(rsi)
    rsi_max_idx = np.argmax(rsi)
    # Bullish divergence: fiyat yeni dip yaparken RSI daha yüksek dip yapıyor
    if price_min_idx > 0 and rsi_min_idx > 0:
        if close.iloc[price_min_idx] < close.iloc[0] and rsi.iloc[price_min_idx] > rsi.iloc[0]:
            return 'bullish'
    # Bearish divergence: fiyat yeni tepe yaparken RSI daha düşük tepe yapıyor
    if price_max_idx > 0 and rsi_max_idx > 0:
        if close.iloc[price_max_idx] > close.iloc[0] and rsi.iloc[price_max_idx] < rsi.iloc[0]:
            return 'bearish'
    return None


def get_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi 


def detect_tobo(df, window=30):
    """
    Son window içinde TOBO (Ters Omuz Baş Omuz) formasyonu tespit eder.
    Basit algoritma: 3 dip noktası, ortadaki en düşük, omuzlar baştan yukarıda ve birbirine yakın.
    """
    if len(df) < window:
        return None
    lows = df['low'][-window:].values
    idx = np.argpartition(lows, 3)[:3]  # En düşük 3 dip
    idx = np.sort(idx)
    dips = lows[idx]
    # Ortadaki dip en düşük olmalı (baş)
    if dips[1] < dips[0] and dips[1] < dips[2]:
        sol_omuz = dips[0]
        bas = dips[1]
        sag_omuz = dips[2]
        # Omuzlar baştan yukarıda ve birbirine yakın olmalı - Daha sıkı kriterler
        if sol_omuz > bas and sag_omuz > bas and abs(sol_omuz - sag_omuz) / bas < 0.10:
            # Boyun çizgisi: sol ve sağ omuzun tepe noktalarının ortalaması
            highs = df['high'][-window:].values
            sol_tepe = highs[idx[0]]
            sag_tepe = highs[idx[2]]
            neckline = (sol_tepe + sag_tepe) / 2
            return {
                'sol_omuz': sol_omuz,
                'bas': bas,
                'sag_omuz': sag_omuz,
                'neckline': neckline,
                'tobo_start': df['open_time'].iloc[-window+idx[0]],
                'tobo_end': df['open_time'].iloc[-window+idx[2]]
            }
    return None 


def detect_obo(df, window=30):
    """
    Son window içinde OBO (Omuz Baş Omuz) formasyonu tespit eder.
    Basit algoritma: 3 tepe noktası, ortadaki en yüksek, omuzlar baştan aşağıda ve birbirine yakın.
    """
    if len(df) < window:
        return None
    highs = df['high'][-window:].values
    idx = np.argpartition(-highs, 3)[:3]  # En yüksek 3 tepe
    idx = np.sort(idx)
    peaks = highs[idx]
    # Ortadaki tepe en yüksek olmalı (baş)
    if peaks[1] > peaks[0] and peaks[1] > peaks[2]:
        sol_omuz = peaks[0]
        bas = peaks[1]
        sag_omuz = peaks[2]
        # Omuzlar baştan aşağıda ve birbirine yakın olmalı - Daha sıkı kriterler
        if sol_omuz < bas and sag_omuz < bas and abs(sol_omuz - sag_omuz) / bas < 0.10:
            # Boyun çizgisi: sol ve sağ omuzun dip noktalarının ortalaması
            lows = df['low'][-window:].values
            sol_dip = lows[idx[0]]
            sag_dip = lows[idx[2]]
            neckline = (sol_dip + sag_dip) / 2
            return {
                'sol_omuz': sol_omuz,
                'bas': bas,
                'sag_omuz': sag_omuz,
                'neckline': neckline,
                'obo_start': df['open_time'].iloc[-window+idx[0]],
                'obo_end': df['open_time'].iloc[-window+idx[2]]
            }
    return None 


def find_all_tobo(df, window=30, min_distance=3):
    """
    Son window içinde birden fazla TOBO (Ters Omuz Baş Omuz) formasyonu tespit eder.
    Her formasyonun başlangıç ve bitiş indeksleri ile detaylarını döndürür.
    """
    results = []
    lows = df['low'][-window:].values
    for i in range(window - 6):  # En az 7 mumluk bir formasyon aralığı
        idx = np.array([i, i+3, i+6])
        dips = lows[idx]
        if dips[1] < dips[0] and dips[1] < dips[2]:
            sol_omuz = dips[0]
            bas = dips[1]
            sag_omuz = dips[2]
            if sol_omuz > bas and sag_omuz > bas and abs(sol_omuz - sag_omuz) / bas < 0.15:
                highs = df['high'][-window:].values
                sol_tepe = highs[idx[0]]
                sag_tepe = highs[idx[2]]
                neckline = (sol_tepe + sag_tepe) / 2
                results.append({
                    'sol_omuz': sol_omuz,
                    'bas': bas,
                    'sag_omuz': sag_omuz,
                    'neckline': neckline,
                    'tobo_start': df['open_time'].iloc[-window+idx[0]],
                    'tobo_end': df['open_time'].iloc[-window+idx[2]]
                })
    return results


def find_all_obo(df, window=30, min_distance=3):
    """
    Son window içinde birden fazla OBO (Omuz Baş Omuz) formasyonu tespit eder.
    Her formasyonun başlangıç ve bitiş indeksleri ile detaylarını döndürür.
    """
    results = []
    highs = df['high'][-window:].values
    for i in range(window - 6):
        idx = np.array([i, i+3, i+6])
        peaks = highs[idx]
        if peaks[1] > peaks[0] and peaks[1] > peaks[2]:
            sol_omuz = peaks[0]
            bas = peaks[1]
            sag_omuz = peaks[2]
            if sol_omuz < bas and sag_omuz < bas and abs(sol_omuz - sag_omuz) / bas < 0.15:
                lows = df['low'][-window:].values
                sol_dip = lows[idx[0]]
                sag_dip = lows[idx[2]]
                neckline = (sol_dip + sag_dip) / 2
                results.append({
                    'sol_omuz': sol_omuz,
                    'bas': bas,
                    'sag_omuz': sag_omuz,
                    'neckline': neckline,
                    'obo_start': df['open_time'].iloc[-window+idx[0]],
                    'obo_end': df['open_time'].iloc[-window+idx[2]]
                })
    return results 


def detect_cup_and_handle(df, window=50):
    """
    Cup and Handle (Fincan ve Kulp) formasyonu tespit eder.
    
    Kurallar:
    - Fiyat, U şeklinde bir yapı oluşturmalı (fincan)
    - Bu yapının ardından kısa ve sığ bir düşüş gelmeli (kulp). Düşüş maksimum %15 olmalı
    - Kulp sonrasında gelen yukarı yönlü kırılımda hacim artışı olmalı
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Fincan tespiti için U şeklini ara
        # Fincan genellikle window'un ilk %60-80'inde oluşur
        cup_start = int(window * 0.1)  # %10'dan sonra başla
        cup_end = int(window * 0.7)    # %70'te bitir
        
        best_cup = None
        best_score = 0
        
        for start in range(cup_start, cup_end - 10):
            for end in range(start + 10, cup_end + 10):
                cup_length = end - start
                if cup_length < 10:  # En az 10 mum olsun
                    continue
                
                # Fincan başlangıç ve bitiş seviyeleri
                cup_start_price = closes[start]
                cup_end_price = closes[end]
                
                # Fincan başlangıç ve bitiş seviyeleri yakın olmalı (%5 tolerans)
                price_diff = abs(cup_start_price - cup_end_price) / cup_start_price
                if price_diff > 0.05:
                    continue
                
                # Fincanın en dibi
                cup_bottom_idx = np.argmin(lows[start:end]) + start
                cup_bottom_price = lows[cup_bottom_idx]
                
                # Fincan derinliği kontrolü (%10-30 arası olmalı)
                cup_depth = (cup_start_price - cup_bottom_price) / cup_start_price
                if cup_depth < 0.10 or cup_depth > 0.30:
                    continue
                
                # U şekli kontrolü - fincanın sağ tarafı sol tarafına benzer olmalı
                left_half = closes[start:cup_bottom_idx]
                right_half = closes[cup_bottom_idx:end]
                
                if len(left_half) < 3 or len(right_half) < 3:
                    continue
                
                # Fincan simetrisi kontrolü
                left_slope = np.polyfit(range(len(left_half)), left_half, 1)[0]
                right_slope = np.polyfit(range(len(right_half)), right_half, 1)[0]
                
                # Sağ taraf yukarı yönlü olmalı, sol taraf aşağı yönlü olmalı
                if right_slope < 0 or left_slope > 0:
                    continue
                
                # Kulp tespiti - fincan sonrası kısa düşüş
                handle_start = end
                handle_end = min(end + 15, window - 1)  # Maksimum 15 mum
                
                if handle_end <= handle_start:
                    continue
                
                # Kulpun en dibi
                handle_bottom_idx = np.argmin(lows[handle_start:handle_end]) + handle_start
                handle_bottom_price = lows[handle_bottom_idx]
                
                # Kulp derinliği kontrolü (%15'ten az olmalı)
                handle_depth = (cup_end_price - handle_bottom_price) / cup_end_price
                if handle_depth > 0.15:
                    continue
                
                # Kulp sonrası kırılım kontrolü
                breakout_start = handle_end
                if breakout_start >= window - 1:
                    continue
                
                # Son 3 mumda kırılım var mı?
                recent_closes = closes[breakout_start:]
                recent_volumes = volumes[breakout_start:]
                
                if len(recent_closes) < 3:
                    continue
                
                # Kırılım kontrolü - fiyat fincan seviyesini geçmeli
                breakout_confirmed = False
                volume_confirmed = False
                
                for i in range(len(recent_closes)):
                    if recent_closes[i] > cup_end_price:
                        # Hacim artışı kontrolü - son 20 mum ortalamasının 1.5 katı
                        if i < len(recent_volumes) - 1:
                            avg_volume = np.mean(volumes[max(0, breakout_start-20):breakout_start])
                            if recent_volumes[i] > avg_volume * 1.5:  # %50 hacim artışı (1.5x)
                                volume_confirmed = True
                        breakout_confirmed = True
                        break
                
                if not breakout_confirmed:
                    continue
                
                # Formasyon skoru hesapla
                score = 0
                score += (0.3 - cup_depth) * 100  # Derinlik ideal
                score += (0.15 - handle_depth) * 100  # Kulp sığ olmalı
                score += 50 if volume_confirmed else 0  # Hacim teyidi
                score += 30 if breakout_confirmed else 0  # Kırılım teyidi
                
                if score > best_score:
                    best_score = score
                    best_cup = {
                        'cup_start': start,
                        'cup_end': end,
                        'cup_bottom': cup_bottom_idx,
                        'cup_start_price': cup_start_price,
                        'cup_end_price': cup_end_price,
                        'cup_bottom_price': cup_bottom_price,
                        'cup_depth': cup_depth,
                        'handle_start': handle_start,
                        'handle_end': handle_end,
                        'handle_bottom': handle_bottom_idx,
                        'handle_bottom_price': handle_bottom_price,
                        'handle_depth': handle_depth,
                        'breakout_price': cup_end_price,
                        'breakout_confirmed': breakout_confirmed,
                        'volume_confirmed': volume_confirmed,
                        'score': score
                    }
        
        return best_cup
        
    except Exception as e:
        return None


def detect_falling_wedge(df, window=40):
    """
    Falling Wedge (Düşen Kama) formasyonu tespit eder.
    
    Kurallar:
    - Alçalan tepe ve diplerden oluşmalı (yüksekten düşük kapanışlara doğru sıkışan yapı)
    - En az 3 tepe ve 3 dip tespit edilmeli
    - Kırılım üst çizgiyi yukarı kırarsa geçerli sayılmalı
    - Hacim kırılımda artmalı (1.5x veya üzeri)
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        # En az 5 mumluk aralıklarla tepe ve dip arama
        for i in range(2, len(closes) - 2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        # En az 3 tepe ve 3 dip gerekli
        if len(peaks) < 3 or len(troughs) < 3:
            return None
        
        # Son 3 tepe ve 3 dipi al
        recent_peaks = peaks[-3:]
        recent_troughs = troughs[-3:]
        
        # Falling Wedge kontrolü - tepe ve dipler alçalmalı
        peak_prices = [p[1] for p in recent_peaks]
        trough_prices = [t[1] for t in recent_troughs]
        
        # Tepe trendi kontrolü - alçalan
        peak_trend = all(peak_prices[i] > peak_prices[i+1] for i in range(len(peak_prices)-1))
        # Dip trendi kontrolü - alçalan ama daha yavaş
        trough_trend = all(trough_prices[i] > trough_prices[i+1] for i in range(len(trough_prices)-1))
        
        if not peak_trend or not trough_trend:
            return None
        
        # Üst ve alt trend çizgilerinin eğimlerini hesapla
        peak_indices = [p[0] for p in recent_peaks]
        trough_indices = [t[0] for t in recent_troughs]
        
        # Doğrusal regresyon ile eğim hesapla
        peak_slope = np.polyfit(peak_indices, peak_prices, 1)[0]
        trough_slope = np.polyfit(trough_indices, trough_prices, 1)[0]
        
        # Üst trend daha dik olmalı (daha negatif eğim)
        if peak_slope >= trough_slope:
            return None
        
        # Kama sıkışması kontrolü - son tepe ve dip arasındaki mesafe azalmalı
        first_gap = peak_prices[0] - trough_prices[0]
        last_gap = peak_prices[-1] - trough_prices[-1]
        
        if last_gap >= first_gap:
            return None
        
        # Kırılım kontrolü - son 5 mumda üst trend çizgisini yukarı kırma
        upper_trend_line = peak_prices[-1] + peak_slope * (len(closes) - 1 - peak_indices[-1])
        breakout_confirmed = False
        volume_confirmed = False
        
        # Son 5 mumda kırılım kontrolü
        for i in range(max(0, len(closes)-5), len(closes)):
            if closes[i] > upper_trend_line:
                # Hacim artışı kontrolü - son 20 mum ortalamasının 1.5 katı
                avg_volume = np.mean(volumes[max(0, i-20):i])
                if volumes[i] > avg_volume * 1.5:
                    volume_confirmed = True
                breakout_confirmed = True
                breakout_price = closes[i]
                break
        
        if not breakout_confirmed:
            return None
        
        # Formasyon skoru hesapla
        score = 0
        score += 30 if breakout_confirmed else 0  # Kırılım teyidi
        score += 25 if volume_confirmed else 0   # Hacim teyidi
        score += 20 if abs(peak_slope) > abs(trough_slope) * 1.5 else 0  # Kama açısı
        score += 15 if last_gap < first_gap * 0.7 else 0  # Sıkışma derecesi
        score += 10 if len(peaks) >= 4 and len(troughs) >= 4 else 0  # Ek tepe/dip
        
        # İşlem parametreleri
        entry_price = breakout_price
        wedge_height = peak_prices[0] - trough_prices[0]  # İlk tepe-dip arası
        tp = entry_price + wedge_height  # Hedef = kama yüksekliği kadar yukarı
        sl = trough_prices[-1]  # Son dip seviyesi
        
        return {
            'peaks': recent_peaks,
            'troughs': recent_troughs,
            'peak_slope': peak_slope,
            'trough_slope': trough_slope,
            'upper_trend_line': upper_trend_line,
            'breakout_price': breakout_price,
            'breakout_confirmed': breakout_confirmed,
            'volume_confirmed': volume_confirmed,
            'entry_price': entry_price,
            'tp': tp,
            'sl': sl,
            'wedge_height': wedge_height,
            'score': score
        }
        
    except Exception as e:
        return None


def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    MACD hesaplama
    """
    try:
        exp1 = df['close'].ewm(span=fast).mean()
        exp2 = df['close'].ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd_line': macd_line.iloc[-1],
            'signal_line': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1],
            'trend': 'Bullish' if macd_line.iloc[-1] > signal_line.iloc[-1] else 'Bearish',
            'momentum': 'Increasing' if histogram.iloc[-1] > histogram.iloc[-2] else 'Decreasing'
        }
    except Exception as e:
        return None


def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    Bollinger Bands hesaplama
    """
    try:
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        current_price = df['close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Pozisyon analizi
        bb_position = (current_price - current_lower) / (current_upper - current_lower)
        
        # Sinyal analizi
        if current_price > current_upper:
            signal = 'Overbought'
        elif current_price < current_lower:
            signal = 'Oversold'
        else:
            signal = 'Neutral'
        
        return {
            'upper_band': current_upper,
            'lower_band': current_lower,
            'middle_band': sma.iloc[-1],
            'bb_position': bb_position,
            'signal': signal,
            'squeeze': (current_upper - current_lower) / sma.iloc[-1] < 0.1  # %10'dan az genişlik
        }
    except Exception as e:
        return None


def calculate_stochastic(df, k_period=14, d_period=3):
    """
    Stochastic Oscillator hesaplama
    """
    try:
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        current_k = k_percent.iloc[-1]
        current_d = d_percent.iloc[-1]
        
        # Sinyal analizi
        if current_k > 80 and current_d > 80:
            signal = 'Overbought'
        elif current_k < 20 and current_d < 20:
            signal = 'Oversold'
        else:
            signal = 'Neutral'
        
        # Kesişim analizi
        if k_percent.iloc[-1] > d_percent.iloc[-1] and k_percent.iloc[-2] <= d_percent.iloc[-2]:
            crossover = 'Bullish'
        elif k_percent.iloc[-1] < d_percent.iloc[-1] and k_percent.iloc[-2] >= d_percent.iloc[-2]:
            crossover = 'Bearish'
        else:
            crossover = 'None'
        
        return {
            'k_percent': current_k,
            'd_percent': current_d,
            'signal': signal,
            'crossover': crossover
        }
    except Exception as e:
        return None


def calculate_adx(df, period=14):
    """
    ADX (Average Directional Index) hesaplama
    """
    try:
        # True Range hesaplama
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        
        # Directional Movement hesaplama
        up_move = df['high'] - df['high'].shift()
        down_move = df['low'].shift() - df['low']
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed values
        tr_smooth = true_range.rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / tr_smooth)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / tr_smooth)
        
        # ADX hesaplama
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        current_adx = adx.iloc[-1]
        current_plus_di = plus_di.iloc[-1]
        current_minus_di = minus_di.iloc[-1]
        
        # Trend gücü analizi
        if current_adx > 25:
            trend_strength = 'Strong'
        elif current_adx > 20:
            trend_strength = 'Moderate'
        else:
            trend_strength = 'Weak'
        
        # Trend yönü
        if current_plus_di > current_minus_di:
            trend_direction = 'Bullish'
        else:
            trend_direction = 'Bearish'
        
        return {
            'adx': current_adx,
            'plus_di': current_plus_di,
            'minus_di': current_minus_di,
            'trend_strength': trend_strength,
            'trend_direction': trend_direction
        }
    except Exception as e:
        return None 


def detect_double_bottom_top(df, window=40):
    """
    Double Bottom (V şekli) ve Double Top (M şekli) formasyonu tespit eder.
    
    Kurallar:
    - İki benzer dip (Double Bottom) veya iki benzer tepe (Double Top)
    - Dip/tepe seviyeleri %5 tolerans içinde olmalı
    - Boyun çizgisi kırılımı hacimle teyit edilmeli
    - En az 10 mum arayla oluşmalı
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, len(recent_data) - 2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        # En az 2 tepe ve 2 dip olmalı
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Double Top tespiti (M şekli)
        if len(peaks) >= 2:
            # Son iki tepeyi al
            peak1, peak2 = peaks[-2], peaks[-1]
            
            # Tepe seviyeleri %5 tolerans içinde olmalı
            tolerance = 0.05
            if abs(peak1[1] - peak2[1]) / peak1[1] <= tolerance:
                # Tepe arasındaki dip seviyesi
                dip_between_peaks = min(lows[peak1[0]:peak2[0]])
                
                # Boyun çizgisi (dip seviyesi)
                neckline = dip_between_peaks
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_confirmed = current_price < neckline
                
                # Hacim teyidi
                avg_volume = np.mean(volumes[-20:])
                current_volume = volumes[-1]
                volume_confirmed = current_volume > avg_volume * 1.5
                
                # Formasyon skoru
                score = 0
                if breakout_confirmed:
                    score += 30
                if volume_confirmed:
                    score += 25
                if abs(peak1[1] - peak2[1]) / peak1[1] <= 0.02:  # %2 tolerans
                    score += 25
                if peak2[0] - peak1[0] >= 10:  # En az 10 mum arayla
                    score += 20
                
                if score >= 50:
                    return {
                        'type': 'DOUBLE_TOP',
                        'score': score,
                        'peak1_price': peak1[1],
                        'peak2_price': peak2[1],
                        'neckline_price': neckline,
                        'breakout_price': current_price,
                        'breakout_confirmed': breakout_confirmed,
                        'volume_confirmed': volume_confirmed,
                        'entry_price': current_price,
                        'tp': neckline * 0.85,  # %15 aşağı hedef
                        'sl': peak2[1] * 1.02,  # %2 üstü stop loss
                        'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
                    }
        
        # Double Bottom tespiti (V şekli)
        if len(troughs) >= 2:
            # Son iki dip
            trough1, trough2 = troughs[-2], troughs[-1]
            
            # Dip seviyeleri %5 tolerans içinde olmalı
            tolerance = 0.05
            if abs(trough1[1] - trough2[1]) / trough1[1] <= tolerance:
                # Dip arasındaki tepe seviyesi
                peak_between_troughs = max(highs[trough1[0]:trough2[0]])
                
                # Boyun çizgisi (tepe seviyesi)
                neckline = peak_between_troughs
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_confirmed = current_price > neckline
                
                # Hacim teyidi
                avg_volume = np.mean(volumes[-20:])
                current_volume = volumes[-1]
                volume_confirmed = current_volume > avg_volume * 1.5
                
                # Formasyon skoru
                score = 0
                if breakout_confirmed:
                    score += 30
                if volume_confirmed:
                    score += 25
                if abs(trough1[1] - trough2[1]) / trough1[1] <= 0.02:  # %2 tolerans
                    score += 25
                if trough2[0] - trough1[0] >= 10:  # En az 10 mum arayla
                    score += 20
                
                if score >= 50:
                    return {
                        'type': 'DOUBLE_BOTTOM',
                        'score': score,
                        'trough1_price': trough1[1],
                        'trough2_price': trough2[1],
                        'neckline_price': neckline,
                        'breakout_price': current_price,
                        'breakout_confirmed': breakout_confirmed,
                        'volume_confirmed': volume_confirmed,
                        'entry_price': current_price,
                        'tp': neckline * 1.15,  # %15 yukarı hedef
                        'sl': trough2[1] * 0.98,  # %2 altı stop loss
                        'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
                    }
        
        return None
        
    except Exception as e:
        return None 


def detect_bullish_bearish_flag(df, window=30):
    """
    Bullish/Bearish Flag formasyonu tespit eder.
    
    Kurallar:
    - Yönlü trend sonrası kısa konsolidasyon
    - Konsolidasyon sırasında hacim düşer
    - Kırılımda hacim artar
    - Flag direği ve bayrak kısmı tespit edilmeli
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Trend yönünü belirle (ilk 10 mum)
        first_10_closes = closes[:10]
        trend_direction = 'bullish' if first_10_closes[-1] > first_10_closes[0] else 'bearish'
        
        # Flag direği tespiti (trend kısmı)
        pole_start = 0
        pole_end = 0
        
        if trend_direction == 'bullish':
            # Yükseliş trendi için direk
            for i in range(1, len(recent_data) - 5):
                if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
                    pole_end = i
                    break
        else:
            # Düşüş trendi için direk
            for i in range(1, len(recent_data) - 5):
                if closes[i] < closes[i-1] and closes[i] < closes[i+1]:
                    pole_end = i
                    break
        
        if pole_end < 5:  # En az 5 mum direk olmalı
            return None
        
        # Flag kısmı (konsolidasyon)
        flag_start = pole_end + 1
        flag_end = len(recent_data) - 1
        
        if flag_end - flag_start < 3:  # En az 3 mum flag olmalı
            return None
        
        # Flag kısmında paralel kanal kontrolü
        flag_highs = highs[flag_start:flag_end]
        flag_lows = lows[flag_start:flag_end]
        
        # Üst ve alt trend çizgileri
        upper_trend = np.polyfit(range(len(flag_highs)), flag_highs, 1)
        lower_trend = np.polyfit(range(len(flag_lows)), flag_lows, 1)
        
        # Trend çizgileri paralel mi? (eğim farkı %10'dan az)
        slope_diff = abs(upper_trend[0] - lower_trend[0]) / abs(upper_trend[0])
        if slope_diff > 0.1:
            return None
        
        # Hacim analizi
        pole_volume = np.mean(volumes[pole_start:pole_end])
        flag_volume = np.mean(volumes[flag_start:flag_end])
        current_volume = volumes[-1]
        
        # Flag sırasında hacim düşmeli
        volume_decrease = flag_volume < pole_volume * 0.8
        
        # Kırılım kontrolü
        current_price = closes[-1]
        upper_line = upper_trend[0] * (len(flag_highs) - 1) + upper_trend[1]
        lower_line = lower_trend[0] * (len(flag_lows) - 1) + lower_trend[1]
        
        if trend_direction == 'bullish':
            # Bullish flag - yukarı kırılım
            breakout_confirmed = current_price > upper_line
            volume_confirmed = current_volume > flag_volume * 1.5
        else:
            # Bearish flag - aşağı kırılım
            breakout_confirmed = current_price < lower_line
            volume_confirmed = current_volume > flag_volume * 1.5
        
        # Formasyon skoru
        score = 0
        if breakout_confirmed:
            score += 30
        if volume_confirmed:
            score += 25
        if volume_decrease:
            score += 20
        if slope_diff <= 0.05:  # Çok paralel
            score += 15
        if flag_end - flag_start >= 5:  # Uzun flag
            score += 10
        
        if score >= 50:
            # Hedef hesaplama (flag yüksekliği kadar)
            flag_height = upper_line - lower_line
            if trend_direction == 'bullish':
                tp = current_price + flag_height
                sl = lower_line * 0.98
            else:
                tp = current_price - flag_height
                sl = upper_line * 1.02
            
            return {
                'type': 'BULLISH_FLAG' if trend_direction == 'bullish' else 'BEARISH_FLAG',
                'score': score,
                'trend_direction': trend_direction,
                'pole_start': pole_start,
                'pole_end': pole_end,
                'flag_start': flag_start,
                'flag_end': flag_end,
                'upper_line': upper_line,
                'lower_line': lower_line,
                'breakout_price': current_price,
                'breakout_confirmed': breakout_confirmed,
                'volume_confirmed': volume_confirmed,
                'volume_decrease': volume_decrease,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
            }
        
        return None
        
    except Exception as e:
        return None 


def detect_ascending_descending_triangle(df, window=40):
    """
    Ascending ve Descending Triangle formasyonu tespit eder.
    
    Kurallar:
    - Yatay ve eğik çizgiden oluşan üçgen
    - En az 2 tepe ve 2 dip olmalı
    - Kırılımda hacim teyidi istenmeli
    - Ascending: Yatay üst, yükselen alt çizgi
    - Descending: Yatay alt, düşen üst çizgi
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, len(recent_data) - 2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        # En az 2 tepe ve 2 dip olmalı
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Ascending Triangle tespiti (yatay üst, yükselen alt)
        if len(peaks) >= 2 and len(troughs) >= 2:
            # Üst çizgi (yatay) - tepe seviyeleri benzer olmalı
            peak1, peak2 = peaks[-2], peaks[-1]
            peak_tolerance = 0.03  # %3 tolerans
            
            if abs(peak1[1] - peak2[1]) / peak1[1] <= peak_tolerance:
                # Alt çizgi (yükselen) - dip seviyeleri yükselmeli
                trough1, trough2 = troughs[-2], troughs[-1]
                
                if trough2[1] > trough1[1] * 1.02:  # En az %2 yükseliş
                    # Trend çizgileri hesapla
                    upper_line = (peak1[1] + peak2[1]) / 2  # Yatay üst çizgi
                    
                    # Alt çizgi eğimi
                    lower_slope = (trough2[1] - trough1[1]) / (trough2[0] - trough1[0])
                    lower_intercept = trough1[1] - lower_slope * trough1[0]
                    
                    # Kırılım kontrolü
                    current_price = closes[-1]
                    breakout_confirmed = current_price > upper_line
                    
                    # Hacim teyidi (detaylı)
                    avg_volume = np.mean(volumes[-20:])
                    current_volume = volumes[-1]
                    volume_confirmed = current_volume > avg_volume * 1.5
                    
                    # Hacim trendi
                    recent_volumes = volumes[-5:]
                    volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
                    
                    # Formasyon skoru (gelişmiş)
                    score = 0
                    
                    # Kırılım kontrolü (30 puan)
                    if breakout_confirmed:
                        score += 30
                        breakout_strength = (current_price - upper_line) / upper_line * 100
                    else:
                        breakout_strength = 0
                    
                    # Hacim teyidi (25 puan)
                    if volume_confirmed:
                        score += 25
                    
                    # Tepe benzerliği (20 puan)
                    peak_diff = abs(peak1[1] - peak2[1]) / peak1[1]
                    if peak_diff <= 0.01:  # %1 tolerans
                        score += 20
                    elif peak_diff <= 0.02:  # %2 tolerans
                        score += 15
                    elif peak_diff <= 0.03:  # %3 tolerans
                        score += 10
                    
                    # Dip yükselişi (15 puan)
                    trough_rise = (trough2[1] - trough1[1]) / trough1[1]
                    if trough_rise >= 0.05:  # %5 yükseliş
                        score += 15
                    elif trough_rise >= 0.03:  # %3 yükseliş
                        score += 10
                    elif trough_rise >= 0.02:  # %2 yükseliş
                        score += 5
                    
                    # Daha fazla tepe/dip (10 puan)
                    if len(peaks) >= 3 and len(troughs) >= 3:
                        score += 10
                    
                    if score >= 50:
                        # Güven seviyesi belirleme
                        if score >= 85:
                            confidence = 'High'
                        elif score >= 70:
                            confidence = 'Medium'
                        else:
                            confidence = 'Low'
                        
                        # Hedef hesaplama (üçgen yüksekliği kadar)
                        triangle_height = upper_line - lower_intercept
                        tp = current_price + triangle_height
                        sl = lower_intercept * 0.98
                        
                        return {
                            'type': 'ASCENDING_TRIANGLE',
                            'score': score,
                            'confidence': confidence,
                            'upper_line': upper_line,
                            'lower_slope': lower_slope,
                            'lower_intercept': lower_intercept,
                            'peak1_price': peak1[1],
                            'peak2_price': peak2[1],
                            'trough1_price': trough1[1],
                            'trough2_price': trough2[1],
                            'peak1_index': peak1[0],
                            'peak2_index': peak2[0],
                            'trough1_index': trough1[0],
                            'trough2_index': trough2[0],
                            'breakout_price': current_price,
                            'breakout_confirmed': breakout_confirmed,
                            'breakout_strength': breakout_strength,
                            'volume_confirmed': volume_confirmed,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                            'volume_trend': volume_trend,
                            'peak_similarity': peak_diff,
                            'trough_rise': trough_rise,
                            'entry_price': current_price,
                            'tp': tp,
                            'sl': sl,
                            'direction': 'LONG',
                            'triangle_height': triangle_height
                        }
        
        # Descending Triangle tespiti (yatay alt, düşen üst)
        if len(peaks) >= 2 and len(troughs) >= 2:
            # Alt çizgi (yatay) - dip seviyeleri benzer olmalı
            trough1, trough2 = troughs[-2], troughs[-1]
            trough_tolerance = 0.03  # %3 tolerans
            
            if abs(trough1[1] - trough2[1]) / trough1[1] <= trough_tolerance:
                # Üst çizgi (düşen) - tepe seviyeleri düşmeli
                peak1, peak2 = peaks[-2], peaks[-1]
                
                if peak2[1] < peak1[1] * 0.98:  # En az %2 düşüş
                    # Trend çizgileri hesapla
                    lower_line = (trough1[1] + trough2[1]) / 2  # Yatay alt çizgi
                    
                    # Üst çizgi eğimi
                    upper_slope = (peak2[1] - peak1[1]) / (peak2[0] - peak1[0])
                    upper_intercept = peak1[1] - upper_slope * peak1[0]
                    
                    # Kırılım kontrolü
                    current_price = closes[-1]
                    breakout_confirmed = current_price < lower_line
                    
                    # Hacim teyidi (detaylı)
                    avg_volume = np.mean(volumes[-20:])
                    current_volume = volumes[-1]
                    volume_confirmed = current_volume > avg_volume * 1.5
                    
                    # Hacim trendi
                    recent_volumes = volumes[-5:]
                    volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
                    
                    # Formasyon skoru (gelişmiş)
                    score = 0
                    
                    # Kırılım kontrolü (30 puan)
                    if breakout_confirmed:
                        score += 30
                        breakout_strength = (lower_line - current_price) / lower_line * 100
                    else:
                        breakout_strength = 0
                    
                    # Hacim teyidi (25 puan)
                    if volume_confirmed:
                        score += 25
                    
                    # Dip benzerliği (20 puan)
                    trough_diff = abs(trough1[1] - trough2[1]) / trough1[1]
                    if trough_diff <= 0.01:  # %1 tolerans
                        score += 20
                    elif trough_diff <= 0.02:  # %2 tolerans
                        score += 15
                    elif trough_diff <= 0.03:  # %3 tolerans
                        score += 10
                    
                    # Tepe düşüşü (15 puan)
                    peak_fall = (peak1[1] - peak2[1]) / peak1[1]
                    if peak_fall >= 0.05:  # %5 düşüş
                        score += 15
                    elif peak_fall >= 0.03:  # %3 düşüş
                        score += 10
                    elif peak_fall >= 0.02:  # %2 düşüş
                        score += 5
                    
                    # Daha fazla tepe/dip (10 puan)
                    if len(peaks) >= 3 and len(troughs) >= 3:
                        score += 10
                    
                    if score >= 50:
                        # Güven seviyesi belirleme
                        if score >= 85:
                            confidence = 'High'
                        elif score >= 70:
                            confidence = 'Medium'
                        else:
                            confidence = 'Low'
                        
                        # Hedef hesaplama (üçgen yüksekliği kadar)
                        triangle_height = upper_intercept - lower_line
                        tp = current_price - triangle_height
                        sl = lower_line * 1.02
                        
                        return {
                            'type': 'DESCENDING_TRIANGLE',
                            'score': score,
                            'confidence': confidence,
                            'lower_line': lower_line,
                            'upper_slope': upper_slope,
                            'upper_intercept': upper_intercept,
                            'peak1_price': peak1[1],
                            'peak2_price': peak2[1],
                            'trough1_price': trough1[1],
                            'trough2_price': trough2[1],
                            'peak1_index': peak1[0],
                            'peak2_index': peak2[0],
                            'trough1_index': trough1[0],
                            'trough2_index': trough2[0],
                            'breakout_price': current_price,
                            'breakout_confirmed': breakout_confirmed,
                            'breakout_strength': breakout_strength,
                            'volume_confirmed': volume_confirmed,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                            'volume_trend': volume_trend,
                            'trough_similarity': trough_diff,
                            'peak_fall': peak_fall,
                            'entry_price': current_price,
                            'tp': tp,
                            'sl': sl,
                            'direction': 'SHORT',
                            'triangle_height': triangle_height
                        }
        
        return None
        
    except Exception as e:
        return None 


def detect_symmetrical_triangle(df, window=40):
    """
    Symmetrical Triangle formasyonu tespit eder.
    
    Kurallar:
    - Konsolide olan ve sıkışan fiyat yapısı
    - Üçgenin daralan yapısı analiz edilmeli
    - Kırılım yönü belirlenerek işlem kararı verilmeli
    - Üst ve alt trend çizgileri eğimleri zıt yönlü olmalı
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, len(recent_data) - 2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        # En az 3 tepe ve 3 dip olmalı
        if len(peaks) < 3 or len(troughs) < 3:
            return None
        
        # Üst ve alt trend çizgileri hesapla
        peak_indices = [p[0] for p in peaks]
        peak_prices = [p[1] for p in peaks]
        trough_indices = [t[0] for t in troughs]
        trough_prices = [t[1] for t in troughs]
        
        # En az 3 nokta olmalı
        if len(peak_indices) < 3 or len(trough_indices) < 3:
            return None
        
        # Üst trend çizgisi (düşen)
        upper_trend = np.polyfit(peak_indices, peak_prices, 1)
        upper_slope = upper_trend[0]
        
        # Alt trend çizgisi (yükselen)
        lower_trend = np.polyfit(trough_indices, trough_prices, 1)
        lower_slope = lower_trend[0]
        
        # Eğimler zıt yönlü olmalı (üst düşen, alt yükselen)
        if upper_slope >= 0 or lower_slope <= 0:
            return None
        
        # Üçgen daralması kontrolü
        # Son tepe ve dip noktaları arasındaki mesafe azalmalı
        if len(peaks) >= 3 and len(troughs) >= 3:
            first_peak = peaks[0]
            last_peak = peaks[-1]
            first_trough = troughs[0]
            last_trough = troughs[-1]
            
            # İlk ve son noktalar arasındaki mesafe
            first_distance = abs(first_peak[1] - first_trough[1])
            last_distance = abs(last_peak[1] - last_trough[1])
            
            # Mesafe azalmalı (daralma)
            if last_distance >= first_distance * 0.8:
                return None
        
        # Kırılım yönü belirleme
        current_price = closes[-1]
        
        # Üst ve alt çizgi değerleri (son nokta için)
        upper_line = upper_trend[0] * (len(recent_data) - 1) + upper_trend[1]
        lower_line = lower_trend[0] * (len(recent_data) - 1) + lower_trend[1]
        
        # Kırılım kontrolü
        breakout_up = current_price > upper_line
        breakout_down = current_price < lower_line
        
        # Hacim teyidi
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_confirmed = current_volume > avg_volume * 1.5
        
        # Formasyon skoru
        score = 0
        
        if breakout_up or breakout_down:
            score += 30
        if volume_confirmed:
            score += 25
        
        # Eğim kontrolü (çok dik olmamalı)
        if abs(upper_slope) < 0.1 and abs(lower_slope) < 0.1:
            score += 20
        
        # Daralma kontrolü
        if last_distance < first_distance * 0.6:
            score += 15
        
        # Daha fazla tepe/dip noktası
        if len(peaks) >= 4 and len(troughs) >= 4:
            score += 10
        
        if score >= 50:
            # Hedef hesaplama (üçgen yüksekliği kadar)
            triangle_height = upper_line - lower_line
            
            if breakout_up:
                tp = current_price + triangle_height
                sl = lower_line * 0.98
                direction = 'LONG'
            else:
                tp = current_price - triangle_height
                sl = upper_line * 1.02
                direction = 'SHORT'
            
            return {
                'type': 'SYMMETRICAL_TRIANGLE',
                'score': score,
                'upper_slope': upper_slope,
                'lower_slope': lower_slope,
                'upper_line': upper_line,
                'lower_line': lower_line,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'volume_confirmed': volume_confirmed,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction,
                'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
            }
        
        return None
        
    except Exception as e:
        return None 


def detect_rising_falling_channel(df, window=50):
    """
    Rising ve Falling Channel formasyonu tespit eder.
    
    Kurallar:
    - Paralel trend çizgileri içinde fiyat hareketi
    - Trend yönü belirlenmeli
    - Destek/direnç seviyeleri çıkarılmalı
    - En az 3 tepe ve 3 dip olmalı
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, len(recent_data) - 2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        # En az 3 tepe ve 3 dip olmalı
        if len(peaks) < 3 or len(troughs) < 3:
            return None
        
        # Üst ve alt trend çizgileri hesapla
        peak_indices = [p[0] for p in peaks]
        peak_prices = [p[1] for p in peaks]
        trough_indices = [t[0] for t in troughs]
        trough_prices = [t[1] for t in troughs]
        
        # En az 3 nokta olmalı
        if len(peak_indices) < 3 or len(trough_indices) < 3:
            return None
        
        # Üst trend çizgisi
        upper_trend = np.polyfit(peak_indices, peak_prices, 1)
        upper_slope = upper_trend[0]
        
        # Alt trend çizgisi
        lower_trend = np.polyfit(trough_indices, trough_prices, 1)
        lower_slope = lower_trend[0]
        
        # Eğimler benzer olmalı (paralel kanal)
        slope_diff = abs(upper_slope - lower_slope) / abs(upper_slope)
        if slope_diff > 0.2:  # %20 tolerans
            return None
        
        # Kanal yönünü belirle
        if upper_slope > 0.001:  # Yükselen kanal
            channel_type = 'RISING'
        elif upper_slope < -0.001:  # Düşen kanal
            channel_type = 'FALLING'
        else:  # Yatay kanal
            channel_type = 'HORIZONTAL'
        
        # Kanal genişliği hesapla
        upper_line = upper_trend[0] * (len(recent_data) - 1) + upper_trend[1]
        lower_line = lower_trend[0] * (len(recent_data) - 1) + lower_trend[1]
        channel_width = upper_line - lower_line
        
        # Kanal genişliği çok dar olmamalı
        avg_price = np.mean(closes)
        if channel_width < avg_price * 0.02:  # %2'den az
            return None
        
        # Kırılım kontrolü
        current_price = closes[-1]
        
        # Üst ve alt çizgilere olan mesafe
        distance_to_upper = abs(current_price - upper_line)
        distance_to_lower = abs(current_price - lower_line)
        
        # Kırılım kontrolü
        breakout_up = current_price > upper_line
        breakout_down = current_price < lower_line
        
        # Hacim teyidi
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_confirmed = current_volume > avg_volume * 1.5
        
        # Formasyon skoru
        score = 0
        
        if breakout_up or breakout_down:
            score += 30
        if volume_confirmed:
            score += 25
        
        # Paralellik kontrolü
        if slope_diff <= 0.1:  # Çok paralel
            score += 20
        
        # Kanal genişliği kontrolü
        if channel_width > avg_price * 0.05:  # %5'ten fazla
            score += 15
        
        # Daha fazla tepe/dip noktası
        if len(peaks) >= 4 and len(troughs) >= 4:
            score += 10
        
        if score >= 50:
            # Hedef hesaplama (kanal genişliği kadar)
            if breakout_up:
                tp = current_price + channel_width
                sl = lower_line * 0.98
                direction = 'LONG'
            elif breakout_down:
                tp = current_price - channel_width
                sl = upper_line * 1.02
                direction = 'SHORT'
            else:
                # Kanal içinde - trend yönüne göre
                if channel_type == 'RISING':
                    tp = upper_line
                    sl = lower_line * 0.98
                    direction = 'LONG'
                elif channel_type == 'FALLING':
                    tp = lower_line
                    sl = upper_line * 1.02
                    direction = 'SHORT'
                else:
                    tp = upper_line
                    sl = lower_line * 0.98
                    direction = 'NEUTRAL'
            
            return {
                'type': f'{channel_type}_CHANNEL',
                'score': score,
                'upper_slope': upper_slope,
                'lower_slope': lower_slope,
                'upper_line': upper_line,
                'lower_line': lower_line,
                'channel_width': channel_width,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'volume_confirmed': volume_confirmed,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction,
                'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
            }
        
        return None
        
    except Exception as e:
        return None 


def detect_macd_rsi_divergence(df, window=30):
    """
    MACD ve RSI divergence (uyumsuzluk) tespit eder.
    
    Kurallar:
    - Fiyat yeni dip yaparken RSI/MACD dip yapmıyorsa pozitif uyumsuzluk
    - Fiyat yeni tepe yaparken RSI/MACD daha düşük tepe yapıyorsa negatif uyumsuzluk
    - Uyumsuzluk varsa sinyal olarak ekle
    
    Returns:
        dict: Divergence detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # RSI hesapla
        rsi_period = 14
        if len(recent_data) < rsi_period:
            return None
        
        # RSI hesaplama
        delta = np.diff(closes)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.mean(gain[:rsi_period])
        avg_loss = np.mean(loss[:rsi_period])
        
        rsi_values = []
        for i in range(rsi_period, len(closes)):
            if i > rsi_period:
                avg_gain = (avg_gain * (rsi_period - 1) + gain[i-1]) / rsi_period
                avg_loss = (avg_loss * (rsi_period - 1) + loss[i-1]) / rsi_period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # MACD hesapla
        ema12 = calculate_ema(closes, 12)
        ema26 = calculate_ema(closes, 26)
        macd_line = ema12 - ema26
        signal_line = calculate_ema(macd_line, 9)
        
        # Yerel tepe ve dip noktalarını bul (fiyat)
        price_peaks = []
        price_troughs = []
        
        for i in range(2, len(closes) - 2):
            # Fiyat tepe noktası
            if closes[i] > closes[i-1] and closes[i] > closes[i-2] and \
               closes[i] > closes[i+1] and closes[i] > closes[i+2]:
                price_peaks.append((i, closes[i]))
            
            # Fiyat dip noktası
            if closes[i] < closes[i-1] and closes[i] < closes[i-2] and \
               closes[i] < closes[i+1] and closes[i] < closes[i+2]:
                price_troughs.append((i, closes[i]))
        
        # RSI tepe ve dip noktalarını bul
        rsi_peaks = []
        rsi_troughs = []
        
        for i in range(2, len(rsi_values) - 2):
            # RSI tepe noktası
            if rsi_values[i] > rsi_values[i-1] and rsi_values[i] > rsi_values[i-2] and \
               rsi_values[i] > rsi_values[i+1] and rsi_values[i] > rsi_values[i+2]:
                rsi_peaks.append((i + rsi_period, rsi_values[i]))
            
            # RSI dip noktası
            if rsi_values[i] < rsi_values[i-1] and rsi_values[i] < rsi_values[i-2] and \
               rsi_values[i] < rsi_values[i+1] and rsi_values[i] < rsi_values[i+2]:
                rsi_troughs.append((i + rsi_period, rsi_values[i]))
        
        # MACD tepe ve dip noktalarını bul
        macd_peaks = []
        macd_troughs = []
        
        for i in range(2, len(macd_line) - 2):
            # MACD tepe noktası
            if macd_line[i] > macd_line[i-1] and macd_line[i] > macd_line[i-2] and \
               macd_line[i] > macd_line[i+1] and macd_line[i] > macd_line[i+2]:
                macd_peaks.append((i, macd_line[i]))
            
            # MACD dip noktası
            if macd_line[i] < macd_line[i-1] and macd_line[i] < macd_line[i-2] and \
               macd_line[i] < macd_line[i+1] and macd_line[i] < macd_line[i+2]:
                macd_troughs.append((i, macd_line[i]))
        
        # Divergence tespiti
        divergences = []
        
        # Pozitif Divergence (Bullish) - Fiyat dip, RSI/MACD yükseliş
        if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
            # Son iki fiyat dip
            price_trough1, price_trough2 = price_troughs[-2], price_troughs[-1]
            
            # Son iki RSI dip
            rsi_trough1, rsi_trough2 = rsi_troughs[-2], rsi_troughs[-1]
            
            # Fiyat düşerken RSI yükseliyor mu?
            if price_trough2[1] < price_trough1[1] and rsi_trough2[1] > rsi_trough1[1]:
                divergences.append({
                    'type': 'BULLISH_RSI_DIVERGENCE',
                    'indicator': 'RSI',
                    'price_trough1': price_trough1[1],
                    'price_trough2': price_trough2[1],
                    'rsi_trough1': rsi_trough1[1],
                    'rsi_trough2': rsi_trough2[1],
                    'strength': 'Strong' if abs(price_trough2[1] - price_trough1[1]) / price_trough1[1] > 0.05 else 'Weak'
                })
        
        # MACD pozitif divergence
        if len(price_troughs) >= 2 and len(macd_troughs) >= 2:
            price_trough1, price_trough2 = price_troughs[-2], price_troughs[-1]
            macd_trough1, macd_trough2 = macd_troughs[-2], macd_troughs[-1]
            
            if price_trough2[1] < price_trough1[1] and macd_trough2[1] > macd_trough1[1]:
                divergences.append({
                    'type': 'BULLISH_MACD_DIVERGENCE',
                    'indicator': 'MACD',
                    'price_trough1': price_trough1[1],
                    'price_trough2': price_trough2[1],
                    'macd_trough1': macd_trough1[1],
                    'macd_trough2': macd_trough2[1],
                    'strength': 'Strong' if abs(price_trough2[1] - price_trough1[1]) / price_trough1[1] > 0.05 else 'Weak'
                })
        
        # Negatif Divergence (Bearish) - Fiyat tepe, RSI/MACD düşüş
        if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
            price_peak1, price_peak2 = price_peaks[-2], price_peaks[-1]
            rsi_peak1, rsi_peak2 = rsi_peaks[-2], rsi_peaks[-1]
            
            if price_peak2[1] > price_peak1[1] and rsi_peak2[1] < rsi_peak1[1]:
                divergences.append({
                    'type': 'BEARISH_RSI_DIVERGENCE',
                    'indicator': 'RSI',
                    'price_peak1': price_peak1[1],
                    'price_peak2': price_peak2[1],
                    'rsi_peak1': rsi_peak1[1],
                    'rsi_peak2': rsi_peak2[1],
                    'strength': 'Strong' if abs(price_peak2[1] - price_peak1[1]) / price_peak1[1] > 0.05 else 'Weak'
                })
        
        # MACD negatif divergence
        if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
            price_peak1, price_peak2 = price_peaks[-2], price_peaks[-1]
            macd_peak1, macd_peak2 = macd_peaks[-2], macd_peaks[-1]
            
            if price_peak2[1] > price_peak1[1] and macd_peak2[1] < macd_peak1[1]:
                divergences.append({
                    'type': 'BEARISH_MACD_DIVERGENCE',
                    'indicator': 'MACD',
                    'price_peak1': price_peak1[1],
                    'price_peak2': price_peak2[1],
                    'macd_peak1': macd_peak1[1],
                    'macd_peak2': macd_peak2[1],
                    'strength': 'Strong' if abs(price_peak2[1] - price_peak1[1]) / price_peak1[1] > 0.05 else 'Weak'
                })
        
        if divergences:
            # En güçlü divergence'ı seç
            strongest_divergence = max(divergences, key=lambda x: 1 if x['strength'] == 'Strong' else 0)
            
            current_price = closes[-1]
            
            # Hedef hesaplama
            if 'BULLISH' in strongest_divergence['type']:
                # Pozitif divergence - yukarı hedef
                price_change = abs(strongest_divergence.get('price_trough2', 0) - strongest_divergence.get('price_trough1', 0))
                tp = current_price + price_change
                sl = current_price * 0.98
                direction = 'LONG'
            else:
                # Negatif divergence - aşağı hedef
                price_change = abs(strongest_divergence.get('price_peak2', 0) - strongest_divergence.get('price_peak1', 0))
                tp = current_price - price_change
                sl = current_price * 1.02
                direction = 'SHORT'
            
            # Skor hesaplama
            score = 60  # Base score
            if strongest_divergence['strength'] == 'Strong':
                score += 20
            if len(divergences) > 1:  # Birden fazla divergence
                score += 20
            
            return {
                'type': strongest_divergence['type'],
                'score': score,
                'indicator': strongest_divergence['indicator'],
                'strength': strongest_divergence['strength'],
                'all_divergences': divergences,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction,
                'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
            }
        
        return None
        
    except Exception as e:
        return None


def calculate_ema(data, period):
    """Exponential Moving Average hesaplar"""
    alpha = 2 / (period + 1)
    ema = [data[0]]
    
    for i in range(1, len(data)):
        ema.append(alpha * data[i] + (1 - alpha) * ema[i-1])
    
    return np.array(ema) 


def analyze_all_formations(df):
    """
    Tüm formasyonları analiz eder ve en iyi sinyali döner.
    
    Returns:
        dict: En iyi formasyon sinyali veya None
    """
    formations = []
    
    # Mevcut formasyonlar
    tobo = detect_tobo(df)
    if tobo:
        formations.append(tobo)
    
    obo = detect_obo(df)
    if obo:
        formations.append(obo)
    
    cup_handle = detect_cup_and_handle(df)
    if cup_handle:
        formations.append(cup_handle)
    
    falling_wedge = detect_falling_wedge(df)
    if falling_wedge:
        formations.append(falling_wedge)
    
    # Yeni formasyonlar
    double_bottom_top = detect_double_bottom_top(df)
    if double_bottom_top:
        formations.append(double_bottom_top)
    
    bullish_bearish_flag = detect_bullish_bearish_flag(df)
    if bullish_bearish_flag:
        formations.append(bullish_bearish_flag)
    
    ascending_descending_triangle = detect_ascending_descending_triangle(df)
    if ascending_descending_triangle:
        formations.append(ascending_descending_triangle)
    
    symmetrical_triangle = detect_symmetrical_triangle(df)
    if symmetrical_triangle:
        formations.append(symmetrical_triangle)
    
    rising_falling_channel = detect_rising_falling_channel(df)
    if rising_falling_channel:
        formations.append(rising_falling_channel)
    
    macd_rsi_divergence = detect_macd_rsi_divergence(df)
    if macd_rsi_divergence:
        formations.append(macd_rsi_divergence)
    
    # En yüksek skorlu formasyonu seç
    if formations:
        best_formation = max(formations, key=lambda x: x['score'])
        return best_formation
    
    return None


def detect_double_bottom_top_advanced(df, window=50):
    """
    Gelişmiş Double Bottom (V şekli) ve Double Top (M şekli) formasyonu tespit eder.
    
    Kurallar:
    - İki benzer dip (Double Bottom) veya iki benzer tepe (Double Top)
    - Dip/tepe seviyeleri %1-2 tolerans içinde olmalı
    - Boyun çizgisi kırılımı hacimle teyit edilmeli
    - En az 10 mum arayla oluşmalı
    - Hacim analizi detaylı yapılmalı
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul (daha hassas)
        peaks = []
        troughs = []
        
        for i in range(3, len(recent_data) - 3):
            # Tepe noktası (5 mum kontrolü)
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]):
                peaks.append((i, highs[i]))
            
            # Dip noktası (5 mum kontrolü)
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]):
                troughs.append((i, lows[i]))
        
        # En az 2 tepe ve 2 dip olmalı
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Double Top tespiti (M şekli)
        if len(peaks) >= 2:
            # Son iki tepeyi al
            peak1, peak2 = peaks[-2], peaks[-1]
            
            # Tepe seviyeleri %2 tolerans içinde olmalı (daha hassas)
            tolerance = 0.02
            price_diff = abs(peak1[1] - peak2[1]) / peak1[1]
            
            if price_diff <= tolerance:
                # Tepe arasındaki dip seviyesi (boyun çizgisi)
                dip_between_peaks = min(lows[peak1[0]:peak2[0]])
                
                # Boyun çizgisi
                neckline = dip_between_peaks
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_confirmed = current_price < neckline
                
                # Hacim analizi (detaylı)
                avg_volume = np.mean(volumes[-20:])
                current_volume = volumes[-1]
                volume_confirmed = current_volume > avg_volume * 1.5
                
                # Hacim trendi analizi
                recent_volumes = volumes[-5:]
                volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
                
                # Formasyon skoru (gelişmiş)
                score = 0
                
                # Kırılım kontrolü (30 puan)
                if breakout_confirmed:
                    score += 30
                    breakout_strength = (neckline - current_price) / neckline * 100
                else:
                    breakout_strength = 0
                
                # Hacim teyidi (25 puan)
                if volume_confirmed:
                    score += 25
                
                # Tepe benzerliği (20 puan)
                if price_diff <= 0.01:  # %1 tolerans
                    score += 20
                elif price_diff <= 0.015:  # %1.5 tolerans
                    score += 15
                elif price_diff <= 0.02:  # %2 tolerans
                    score += 10
                
                # Zaman aralığı (15 puan)
                time_gap = peak2[0] - peak1[0]
                if time_gap >= 15:  # En az 15 mum
                    score += 15
                elif time_gap >= 10:  # En az 10 mum
                    score += 10
                
                # Hacim trendi (10 puan)
                if volume_trend == 'Yükselen':
                    score += 10
                
                if score >= 50:
                    # Güven seviyesi belirleme
                    if score >= 85:
                        confidence = 'High'
                    elif score >= 70:
                        confidence = 'Medium'
                    else:
                        confidence = 'Low'
                    
                    # Hedef hesaplama
                    formation_height = peak1[1] - neckline
                    tp = current_price - formation_height
                    sl = peak2[1] * 1.02  # %2 üstü stop loss
                    
                    return {
                        'type': 'DOUBLE_TOP',
                        'score': score,
                        'confidence': confidence,
                        'peak1_price': peak1[1],
                        'peak2_price': peak2[1],
                        'peak1_index': peak1[0],
                        'peak2_index': peak2[0],
                        'neckline_price': neckline,
                        'breakout_price': current_price,
                        'breakout_confirmed': breakout_confirmed,
                        'breakout_strength': breakout_strength,
                        'volume_confirmed': volume_confirmed,
                        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                        'volume_trend': volume_trend,
                        'price_similarity': price_diff,
                        'time_gap': time_gap,
                        'entry_price': current_price,
                        'tp': tp,
                        'sl': sl,
                        'direction': 'SHORT',
                        'formation_height': formation_height
                    }
        
        # Double Bottom tespiti (V şekli)
        if len(troughs) >= 2:
            # Son iki dip
            trough1, trough2 = troughs[-2], troughs[-1]
            
            # Dip seviyeleri %2 tolerans içinde olmalı
            tolerance = 0.02
            price_diff = abs(trough1[1] - trough2[1]) / trough1[1]
            
            if price_diff <= tolerance:
                # Dip arasındaki tepe seviyesi (boyun çizgisi)
                peak_between_troughs = max(highs[trough1[0]:trough2[0]])
                
                # Boyun çizgisi
                neckline = peak_between_troughs
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_confirmed = current_price > neckline
                
                # Hacim analizi (detaylı)
                avg_volume = np.mean(volumes[-20:])
                current_volume = volumes[-1]
                volume_confirmed = current_volume > avg_volume * 1.5
                
                # Hacim trendi analizi
                recent_volumes = volumes[-5:]
                volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
                
                # Formasyon skoru (gelişmiş)
                score = 0
                
                # Kırılım kontrolü (30 puan)
                if breakout_confirmed:
                    score += 30
                    breakout_strength = (current_price - neckline) / neckline * 100
                else:
                    breakout_strength = 0
                
                # Hacim teyidi (25 puan)
                if volume_confirmed:
                    score += 25
                
                # Dip benzerliği (20 puan)
                if price_diff <= 0.01:  # %1 tolerans
                    score += 20
                elif price_diff <= 0.015:  # %1.5 tolerans
                    score += 15
                elif price_diff <= 0.02:  # %2 tolerans
                    score += 10
                
                # Zaman aralığı (15 puan)
                time_gap = trough2[0] - trough1[0]
                if time_gap >= 15:  # En az 15 mum
                    score += 15
                elif time_gap >= 10:  # En az 10 mum
                    score += 10
                
                # Hacim trendi (10 puan)
                if volume_trend == 'Yükselen':
                    score += 10
                
                if score >= 50:
                    # Güven seviyesi belirleme
                    if score >= 85:
                        confidence = 'High'
                    elif score >= 70:
                        confidence = 'Medium'
                    else:
                        confidence = 'Low'
                    
                    # Hedef hesaplama
                    formation_height = neckline - trough1[1]
                    tp = current_price + formation_height
                    sl = trough2[1] * 0.98  # %2 altı stop loss
                    
                    return {
                        'type': 'DOUBLE_BOTTOM',
                        'score': score,
                        'confidence': confidence,
                        'trough1_price': trough1[1],
                        'trough2_price': trough2[1],
                        'trough1_index': trough1[0],
                        'trough2_index': trough2[0],
                        'neckline_price': neckline,
                        'breakout_price': current_price,
                        'breakout_confirmed': breakout_confirmed,
                        'breakout_strength': breakout_strength,
                        'volume_confirmed': volume_confirmed,
                        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                        'volume_trend': volume_trend,
                        'price_similarity': price_diff,
                        'time_gap': time_gap,
                        'entry_price': current_price,
                        'tp': tp,
                        'sl': sl,
                        'direction': 'LONG',
                        'formation_height': formation_height
                    }
        
        return None
        
    except Exception as e:
        return None


def detect_bullish_bearish_flag_advanced(df, window=40):
    """
    Gelişmiş Bullish/Bearish Flag formasyonu tespit eder.
    
    Kurallar:
    - Güçlü yönlü hareket sonrası kısa süren düzeltme (konsolidasyon)
    - Konsolidasyon sırasında hacim düşer
    - Sonrasında hacimli kırılım beklentisi vardır
    - Bayrak direği + konsolidasyon bölgesi tespit edilmeli
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Trend yönünü belirle (ilk 15 mum)
        first_15_closes = closes[:15]
        trend_direction = 'bullish' if first_15_closes[-1] > first_15_closes[0] * 1.05 else 'bearish'
        
        # Flag direği tespiti (trend kısmı) - daha hassas
        pole_start = 0
        pole_end = 0
        
        if trend_direction == 'bullish':
            # Yükseliş trendi için direk - en az %5 yükseliş
            for i in range(5, len(recent_data) - 8):
                price_change = (closes[i] - closes[0]) / closes[0]
                if price_change >= 0.05:  # En az %5 yükseliş
                    pole_end = i
                    break
        else:
            # Düşüş trendi için direk - en az %5 düşüş
            for i in range(5, len(recent_data) - 8):
                price_change = (closes[0] - closes[i]) / closes[0]
                if price_change >= 0.05:  # En az %5 düşüş
                    pole_end = i
                    break
        
        if pole_end < 8:  # En az 8 mum direk olmalı
            return None
        
        # Flag kısmı (konsolidasyon) - daha detaylı analiz
        flag_start = pole_end + 1
        flag_end = len(recent_data) - 1
        
        if flag_end - flag_start < 5:  # En az 5 mum flag olmalı
            return None
        
        # Flag kısmında paralel kanal kontrolü
        flag_highs = highs[flag_start:flag_end]
        flag_lows = lows[flag_start:flag_end]
        
        # Üst ve alt trend çizgileri
        upper_trend = np.polyfit(range(len(flag_highs)), flag_highs, 1)
        lower_trend = np.polyfit(range(len(flag_lows)), flag_lows, 1)
        
        # Trend çizgileri paralel mi? (eğim farkı %15'den az)
        slope_diff = abs(upper_trend[0] - lower_trend[0]) / abs(upper_trend[0])
        if slope_diff > 0.15:
            return None
        
        # Hacim analizi (detaylı)
        pole_volume = np.mean(volumes[pole_start:pole_end])
        flag_volume = np.mean(volumes[flag_start:flag_end])
        current_volume = volumes[-1]
        
        # Flag sırasında hacim düşmeli (%20'den fazla)
        volume_decrease = flag_volume < pole_volume * 0.8
        
        # Kırılım kontrolü
        current_price = closes[-1]
        upper_line = upper_trend[0] * (len(flag_highs) - 1) + upper_trend[1]
        lower_line = lower_trend[0] * (len(flag_lows) - 1) + lower_trend[1]
        
        if trend_direction == 'bullish':
            # Bullish flag - yukarı kırılım
            breakout_confirmed = current_price > upper_line
            volume_confirmed = current_volume > flag_volume * 1.5
        else:
            # Bearish flag - aşağı kırılım
            breakout_confirmed = current_price < lower_line
            volume_confirmed = current_volume > flag_volume * 1.5
        
        # Formasyon skoru (gelişmiş)
        score = 0
        
        # Kırılım kontrolü (30 puan)
        if breakout_confirmed:
            score += 30
            if trend_direction == 'bullish':
                breakout_strength = (current_price - upper_line) / upper_line * 100
            else:
                breakout_strength = (lower_line - current_price) / lower_line * 100
        else:
            breakout_strength = 0
        
        # Hacim teyidi (25 puan)
        if volume_confirmed:
            score += 25
        
        # Hacim düşüşü (20 puan)
        if volume_decrease:
            score += 20
        
        # Paralellik kontrolü (15 puan)
        if slope_diff <= 0.05:  # Çok paralel
            score += 15
        elif slope_diff <= 0.10:  # Paralel
            score += 10
        
        # Flag uzunluğu (10 puan)
        flag_length = flag_end - flag_start
        if flag_length >= 8:  # Uzun flag
            score += 10
        elif flag_length >= 5:  # Orta flag
            score += 5
        
        if score >= 50:
            # Güven seviyesi belirleme
            if score >= 85:
                confidence = 'High'
            elif score >= 70:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            # Hedef hesaplama (flag yüksekliği kadar)
            flag_height = upper_line - lower_line
            if trend_direction == 'bullish':
                tp = current_price + flag_height
                sl = lower_line * 0.98
                direction = 'LONG'
            else:
                tp = current_price - flag_height
                sl = upper_line * 1.02
                direction = 'SHORT'
            
            return {
                'type': 'BULLISH_FLAG' if trend_direction == 'bullish' else 'BEARISH_FLAG',
                'score': score,
                'confidence': confidence,
                'trend_direction': trend_direction,
                'pole_start': pole_start,
                'pole_end': pole_end,
                'flag_start': flag_start,
                'flag_end': flag_end,
                'upper_line': upper_line,
                'lower_line': lower_line,
                'breakout_price': current_price,
                'breakout_confirmed': breakout_confirmed,
                'breakout_strength': breakout_strength,
                'volume_confirmed': volume_confirmed,
                'volume_decrease': volume_decrease,
                'volume_ratio': current_volume / flag_volume if flag_volume > 0 else 1,
                'pole_volume_ratio': pole_volume / flag_volume if flag_volume > 0 else 1,
                'slope_diff': slope_diff,
                'flag_length': flag_length,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction,
                'flag_height': flag_height
            }
        
        return None
        
    except Exception as e:
        return None


def detect_ascending_descending_triangle_advanced(df, window=50):
    """
    Gelişmiş Ascending ve Descending Triangle formasyonu tespit eder.
    
    Kurallar:
    - En az 2 tepe ve 2 dip ile oluşan üçgen formasyonlar
    - Ascending: Yatay direnç + yükselen dipler
    - Descending: Yatay destek + alçalan tepeler
    - Kırılım yönüne göre işlem fırsatı sunar
    - Hacim teyidi ekle
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul (daha hassas)
        peaks = []
        troughs = []
        
        for i in range(3, len(recent_data) - 3):
            # Tepe noktası (5 mum kontrolü)
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]):
                peaks.append((i, highs[i]))
            
            # Dip noktası (5 mum kontrolü)
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]):
                troughs.append((i, lows[i]))
        
        # En az 2 tepe ve 2 dip olmalı
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Ascending Triangle tespiti (yatay üst, yükselen alt)
        if len(peaks) >= 2 and len(troughs) >= 2:
            # Üst çizgi (yatay) - tepe seviyeleri benzer olmalı
            peak1, peak2 = peaks[-2], peaks[-1]
            peak_tolerance = 0.03  # %3 tolerans
            
            if abs(peak1[1] - peak2[1]) / peak1[1] <= peak_tolerance:
                # Alt çizgi (yükselen) - dip seviyeleri yükselmeli
                trough1, trough2 = troughs[-2], troughs[-1]
                
                if trough2[1] > trough1[1] * 1.02:  # En az %2 yükseliş
                    # Trend çizgileri hesapla
                    upper_line = (peak1[1] + peak2[1]) / 2  # Yatay üst çizgi
                    
                    # Alt çizgi eğimi
                    lower_slope = (trough2[1] - trough1[1]) / (trough2[0] - trough1[0])
                    lower_intercept = trough1[1] - lower_slope * trough1[0]
                    
                    # Kırılım kontrolü
                    current_price = closes[-1]
                    breakout_confirmed = current_price > upper_line
                    
                    # Hacim teyidi (detaylı)
                    avg_volume = np.mean(volumes[-20:])
                    current_volume = volumes[-1]
                    volume_confirmed = current_volume > avg_volume * 1.5
                    
                    # Hacim trendi
                    recent_volumes = volumes[-5:]
                    volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
                    
                    # Formasyon skoru (gelişmiş)
                    score = 0
                    
                    # Kırılım kontrolü (30 puan)
                    if breakout_confirmed:
                        score += 30
                        breakout_strength = (current_price - upper_line) / upper_line * 100
                    else:
                        breakout_strength = 0
                    
                    # Hacim teyidi (25 puan)
                    if volume_confirmed:
                        score += 25
                    
                    # Tepe benzerliği (20 puan)
                    peak_diff = abs(peak1[1] - peak2[1]) / peak1[1]
                    if peak_diff <= 0.01:  # %1 tolerans
                        score += 20
                    elif peak_diff <= 0.02:  # %2 tolerans
                        score += 15
                    elif peak_diff <= 0.03:  # %3 tolerans
                        score += 10
                    
                    # Dip yükselişi (15 puan)
                    trough_rise = (trough2[1] - trough1[1]) / trough1[1]
                    if trough_rise >= 0.05:  # %5 yükseliş
                        score += 15
                    elif trough_rise >= 0.03:  # %3 yükseliş
                        score += 10
                    elif trough_rise >= 0.02:  # %2 yükseliş
                        score += 5
                    
                    # Daha fazla tepe/dip (10 puan)
                    if len(peaks) >= 3 and len(troughs) >= 3:
                        score += 10
                    
                    if score >= 50:
                        # Güven seviyesi belirleme
                        if score >= 85:
                            confidence = 'High'
                        elif score >= 70:
                            confidence = 'Medium'
                        else:
                            confidence = 'Low'
                        
                        # Hedef hesaplama (üçgen yüksekliği kadar)
                        triangle_height = upper_line - lower_intercept
                        tp = current_price + triangle_height
                        sl = lower_intercept * 0.98
                        
                        return {
                            'type': 'ASCENDING_TRIANGLE',
                            'score': score,
                            'confidence': confidence,
                            'upper_line': upper_line,
                            'lower_slope': lower_slope,
                            'lower_intercept': lower_intercept,
                            'peak1_price': peak1[1],
                            'peak2_price': peak2[1],
                            'trough1_price': trough1[1],
                            'trough2_price': trough2[1],
                            'peak1_index': peak1[0],
                            'peak2_index': peak2[0],
                            'trough1_index': trough1[0],
                            'trough2_index': trough2[0],
                            'breakout_price': current_price,
                            'breakout_confirmed': breakout_confirmed,
                            'breakout_strength': breakout_strength,
                            'volume_confirmed': volume_confirmed,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                            'volume_trend': volume_trend,
                            'peak_similarity': peak_diff,
                            'trough_rise': trough_rise,
                            'entry_price': current_price,
                            'tp': tp,
                            'sl': sl,
                            'direction': 'LONG',
                            'triangle_height': triangle_height
                        }
        
        # Descending Triangle tespiti (yatay alt, düşen üst)
        if len(peaks) >= 2 and len(troughs) >= 2:
            # Alt çizgi (yatay) - dip seviyeleri benzer olmalı
            trough1, trough2 = troughs[-2], troughs[-1]
            trough_tolerance = 0.03  # %3 tolerans
            
            if abs(trough1[1] - trough2[1]) / trough1[1] <= trough_tolerance:
                # Üst çizgi (düşen) - tepe seviyeleri düşmeli
                peak1, peak2 = peaks[-2], peaks[-1]
                
                if peak2[1] < peak1[1] * 0.98:  # En az %2 düşüş
                    # Trend çizgileri hesapla
                    lower_line = (trough1[1] + trough2[1]) / 2  # Yatay alt çizgi
                    
                    # Üst çizgi eğimi
                    upper_slope = (peak2[1] - peak1[1]) / (peak2[0] - peak1[0])
                    upper_intercept = peak1[1] - upper_slope * peak1[0]
                    
                    # Kırılım kontrolü
                    current_price = closes[-1]
                    breakout_confirmed = current_price < lower_line
                    
                    # Hacim teyidi (detaylı)
                    avg_volume = np.mean(volumes[-20:])
                    current_volume = volumes[-1]
                    volume_confirmed = current_volume > avg_volume * 1.5
                    
                    # Hacim trendi
                    recent_volumes = volumes[-5:]
                    volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
                    
                    # Formasyon skoru (gelişmiş)
                    score = 0
                    
                    # Kırılım kontrolü (30 puan)
                    if breakout_confirmed:
                        score += 30
                        breakout_strength = (lower_line - current_price) / lower_line * 100
                    else:
                        breakout_strength = 0
                    
                    # Hacim teyidi (25 puan)
                    if volume_confirmed:
                        score += 25
                    
                    # Dip benzerliği (20 puan)
                    trough_diff = abs(trough1[1] - trough2[1]) / trough1[1]
                    if trough_diff <= 0.01:  # %1 tolerans
                        score += 20
                    elif trough_diff <= 0.02:  # %2 tolerans
                        score += 15
                    elif trough_diff <= 0.03:  # %3 tolerans
                        score += 10
                    
                    # Tepe düşüşü (15 puan)
                    peak_fall = (peak1[1] - peak2[1]) / peak1[1]
                    if peak_fall >= 0.05:  # %5 düşüş
                        score += 15
                    elif peak_fall >= 0.03:  # %3 düşüş
                        score += 10
                    elif peak_fall >= 0.02:  # %2 düşüş
                        score += 5
                    
                    # Daha fazla tepe/dip (10 puan)
                    if len(peaks) >= 3 and len(troughs) >= 3:
                        score += 10
                    
                    if score >= 50:
                        # Güven seviyesi belirleme
                        if score >= 85:
                            confidence = 'High'
                        elif score >= 70:
                            confidence = 'Medium'
                        else:
                            confidence = 'Low'
                        
                        # Hedef hesaplama (üçgen yüksekliği kadar)
                        triangle_height = upper_intercept - lower_line
                        tp = current_price - triangle_height
                        sl = lower_line * 1.02
                        
                        return {
                            'type': 'DESCENDING_TRIANGLE',
                            'score': score,
                            'confidence': confidence,
                            'lower_line': lower_line,
                            'upper_slope': upper_slope,
                            'upper_intercept': upper_intercept,
                            'peak1_price': peak1[1],
                            'peak2_price': peak2[1],
                            'trough1_price': trough1[1],
                            'trough2_price': trough2[1],
                            'peak1_index': peak1[0],
                            'peak2_index': peak2[0],
                            'trough1_index': trough1[0],
                            'trough2_index': trough2[0],
                            'breakout_price': current_price,
                            'breakout_confirmed': breakout_confirmed,
                            'breakout_strength': breakout_strength,
                            'volume_confirmed': volume_confirmed,
                            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                            'volume_trend': volume_trend,
                            'trough_similarity': trough_diff,
                            'peak_fall': peak_fall,
                            'entry_price': current_price,
                            'tp': tp,
                            'sl': sl,
                            'direction': 'SHORT',
                            'triangle_height': triangle_height
                        }
        
        return None
        
    except Exception as e:
        return None


def detect_symmetrical_triangle_advanced(df, window=50):
    """
    Gelişmiş Symmetrical Triangle formasyonu tespit eder.
    
    Kurallar:
    - Yükselen dipler + alçalan tepeler = sıkışan yapı
    - Nötr formasyondur
    - Kırılım yönü, hacim ve mum gücüyle analiz edilmeli
    - En az 3 tepe ve 3 dip olmalı
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul (daha hassas)
        peaks = []
        troughs = []
        
        for i in range(3, len(recent_data) - 3):
            # Tepe noktası (5 mum kontrolü)
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]):
                peaks.append((i, highs[i]))
            
            # Dip noktası (5 mum kontrolü)
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]):
                troughs.append((i, lows[i]))
        
        # En az 3 tepe ve 3 dip olmalı
        if len(peaks) < 3 or len(troughs) < 3:
            return None
        
        # Üst ve alt trend çizgileri hesapla
        peak_indices = [p[0] for p in peaks]
        peak_prices = [p[1] for p in peaks]
        trough_indices = [t[0] for t in troughs]
        trough_prices = [t[1] for t in troughs]
        
        # En az 3 nokta olmalı
        if len(peak_indices) < 3 or len(trough_indices) < 3:
            return None
        
        # Üst trend çizgisi (düşen)
        upper_trend = np.polyfit(peak_indices, peak_prices, 1)
        upper_slope = upper_trend[0]
        
        # Alt trend çizgisi (yükselen)
        lower_trend = np.polyfit(trough_indices, trough_prices, 1)
        lower_slope = lower_trend[0]
        
        # Eğimler zıt yönlü olmalı (üst düşen, alt yükselen)
        if upper_slope >= 0 or lower_slope <= 0:
            return None
        
        # Üçgen daralması kontrolü (daha hassas)
        if len(peaks) >= 3 and len(troughs) >= 3:
            first_peak = peaks[0]
            last_peak = peaks[-1]
            first_trough = troughs[0]
            last_trough = troughs[-1]
            
            # İlk ve son noktalar arasındaki mesafe
            first_distance = abs(first_peak[1] - first_trough[1])
            last_distance = abs(last_peak[1] - last_trough[1])
            
            # Mesafe azalmalı (daralma) - en az %20 azalma
            if last_distance >= first_distance * 0.8:
                return None
        
        # Kırılım yönü belirleme
        current_price = closes[-1]
        
        # Üst ve alt çizgi değerleri (son nokta için)
        upper_line = upper_trend[0] * (len(recent_data) - 1) + upper_trend[1]
        lower_line = lower_trend[0] * (len(recent_data) - 1) + lower_trend[1]
        
        # Kırılım kontrolü
        breakout_up = current_price > upper_line
        breakout_down = current_price < lower_line
        
        # Hacim teyidi (detaylı)
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_confirmed = current_volume > avg_volume * 1.5
        
        # Hacim trendi
        recent_volumes = volumes[-5:]
        volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
        
        # Mum gücü analizi (son 3 mum)
        recent_closes = closes[-3:]
        recent_highs = highs[-3:]
        recent_lows = lows[-3:]
        
        bullish_candles = 0
        bearish_candles = 0
        
        for i in range(len(recent_closes)):
            body_size = abs(recent_closes[i] - recent_closes[i-1]) if i > 0 else 0
            total_range = recent_highs[i] - recent_lows[i]
            
            if body_size > 0 and total_range > 0:
                body_ratio = body_size / total_range
                if body_ratio > 0.6:  # Güçlü mum
                    if recent_closes[i] > recent_closes[i-1]:
                        bullish_candles += 1
                    else:
                        bearish_candles += 1
        
        # Formasyon skoru (gelişmiş)
        score = 0
        
        # Kırılım kontrolü (30 puan)
        if breakout_up or breakout_down:
            score += 30
            if breakout_up:
                breakout_strength = (current_price - upper_line) / upper_line * 100
                breakout_direction = 'UP'
            else:
                breakout_strength = (lower_line - current_price) / lower_line * 100
                breakout_direction = 'DOWN'
        else:
            breakout_strength = 0
            breakout_direction = 'NONE'
        
        # Hacim teyidi (25 puan)
        if volume_confirmed:
            score += 25
        
        # Eğim kontrolü (20 puan) - çok dik olmamalı
        if abs(upper_slope) < 0.1 and abs(lower_slope) < 0.1:
            score += 20
        elif abs(upper_slope) < 0.15 and abs(lower_slope) < 0.15:
            score += 15
        elif abs(upper_slope) < 0.2 and abs(lower_slope) < 0.2:
            score += 10
        
        # Daralma kontrolü (15 puan)
        if last_distance < first_distance * 0.6:
            score += 15
        elif last_distance < first_distance * 0.7:
            score += 10
        elif last_distance < first_distance * 0.8:
            score += 5
        
        # Daha fazla tepe/dip noktası (10 puan)
        if len(peaks) >= 4 and len(troughs) >= 4:
            score += 10
        
        if score >= 50:
            # Güven seviyesi belirleme
            if score >= 85:
                confidence = 'High'
            elif score >= 70:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            # Hedef hesaplama (üçgen yüksekliği kadar)
            triangle_height = upper_line - lower_line
            
            if breakout_up:
                tp = current_price + triangle_height
                sl = lower_line * 0.98
                direction = 'LONG'
            elif breakout_down:
                tp = current_price - triangle_height
                sl = upper_line * 1.02
                direction = 'SHORT'
            else:
                # Kırılım yoksa - mum gücüne göre yön belirle
                if bullish_candles > bearish_candles:
                    tp = upper_line
                    sl = lower_line * 0.98
                    direction = 'LONG'
                elif bearish_candles > bullish_candles:
                    tp = lower_line
                    sl = upper_line * 1.02
                    direction = 'SHORT'
                else:
                    tp = upper_line
                    sl = lower_line * 0.98
                    direction = 'NEUTRAL'
            
            return {
                'type': 'SYMMETRICAL_TRIANGLE',
                'score': score,
                'confidence': confidence,
                'upper_slope': upper_slope,
                'lower_slope': lower_slope,
                'upper_line': upper_line,
                'lower_line': lower_line,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'breakout_direction': breakout_direction,
                'breakout_strength': breakout_strength,
                'volume_confirmed': volume_confirmed,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                'volume_trend': volume_trend,
                'bullish_candles': bullish_candles,
                'bearish_candles': bearish_candles,
                'first_distance': first_distance,
                'last_distance': last_distance,
                'contraction_ratio': last_distance / first_distance if first_distance > 0 else 1,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction,
                'triangle_height': triangle_height
            }
        
        return None
        
    except Exception as e:
        return None


def detect_rising_channel_advanced(df, window=60):
    """
    Gelişmiş Rising Channel formasyonu tespit eder.
    
    Kurallar:
    - Paralel yükselen destek ve direnç çizgileri
    - En az 2 dip ve 2 tepe analizi gerekir
    - Kanal dışı kırılım riskli olur
    - Yükselen trend içinde paralel kanal
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Yerel tepe ve dip noktalarını bul (daha hassas)
        peaks = []
        troughs = []
        
        for i in range(3, len(recent_data) - 3):
            # Tepe noktası (5 mum kontrolü)
            if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] and
                highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]):
                peaks.append((i, highs[i]))
            
            # Dip noktası (5 mum kontrolü)
            if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] and
                lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]):
                troughs.append((i, lows[i]))
        
        # En az 3 tepe ve 3 dip olmalı
        if len(peaks) < 3 or len(troughs) < 3:
            return None
        
        # Üst ve alt trend çizgileri hesapla
        peak_indices = [p[0] for p in peaks]
        peak_prices = [p[1] for p in peaks]
        trough_indices = [t[0] for t in troughs]
        trough_prices = [t[1] for t in troughs]
        
        # En az 3 nokta olmalı
        if len(peak_indices) < 3 or len(trough_indices) < 3:
            return None
        
        # Üst trend çizgisi (yükselen)
        upper_trend = np.polyfit(peak_indices, peak_prices, 1)
        upper_slope = upper_trend[0]
        
        # Alt trend çizgisi (yükselen)
        lower_trend = np.polyfit(trough_indices, trough_prices, 1)
        lower_slope = lower_trend[0]
        
        # Her iki çizgi de yükselen olmalı
        if upper_slope <= 0.001 or lower_slope <= 0.001:
            return None
        
        # Eğimler benzer olmalı (paralel kanal) - %25 tolerans
        slope_diff = abs(upper_slope - lower_slope) / abs(upper_slope)
        if slope_diff > 0.25:
            return None
        
        # Kanal genişliği hesapla
        upper_line = upper_trend[0] * (len(recent_data) - 1) + upper_trend[1]
        lower_line = lower_trend[0] * (len(recent_data) - 1) + lower_trend[1]
        channel_width = upper_line - lower_line
        
        # Kanal genişliği çok dar olmamalı
        avg_price = np.mean(closes)
        if channel_width < avg_price * 0.02:  # %2'den az
            return None
        
        # Kırılım kontrolü
        current_price = closes[-1]
        
        # Üst ve alt çizgilere olan mesafe
        distance_to_upper = abs(current_price - upper_line)
        distance_to_lower = abs(current_price - lower_line)
        
        # Kırılım kontrolü
        breakout_up = current_price > upper_line
        breakout_down = current_price < lower_line
        
        # Hacim teyidi (detaylı)
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_confirmed = current_volume > avg_volume * 1.5
        
        # Hacim trendi
        recent_volumes = volumes[-5:]
        volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
        
        # Kanal içi pozisyon analizi
        channel_position = (current_price - lower_line) / channel_width if channel_width > 0 else 0.5
        
        # Formasyon skoru (gelişmiş)
        score = 0
        
        # Kırılım kontrolü (30 puan)
        if breakout_up or breakout_down:
            score += 30
            if breakout_up:
                breakout_strength = (current_price - upper_line) / upper_line * 100
                breakout_direction = 'UP'
            else:
                breakout_strength = (lower_line - current_price) / lower_line * 100
                breakout_direction = 'DOWN'
        else:
            breakout_strength = 0
            breakout_direction = 'NONE'
        
        # Hacim teyidi (25 puan)
        if volume_confirmed:
            score += 25
        
        # Paralellik kontrolü (20 puan)
        if slope_diff <= 0.1:  # Çok paralel
            score += 20
        elif slope_diff <= 0.15:  # Paralel
            score += 15
        elif slope_diff <= 0.25:  # Kabul edilebilir
            score += 10
        
        # Kanal genişliği kontrolü (15 puan)
        if channel_width > avg_price * 0.05:  # %5'ten fazla
            score += 15
        elif channel_width > avg_price * 0.03:  # %3'ten fazla
            score += 10
        elif channel_width > avg_price * 0.02:  # %2'den fazla
            score += 5
        
        # Daha fazla tepe/dip noktası (10 puan)
        if len(peaks) >= 4 and len(troughs) >= 4:
            score += 10
        
        if score >= 50:
            # Güven seviyesi belirleme
            if score >= 85:
                confidence = 'High'
            elif score >= 70:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            # Hedef hesaplama (kanal genişliği kadar)
            if breakout_up:
                tp = current_price + channel_width
                sl = lower_line * 0.98
                direction = 'LONG'
            elif breakout_down:
                tp = current_price - channel_width
                sl = upper_line * 1.02
                direction = 'SHORT'
            else:
                # Kanal içinde - yükselen trend olduğu için long ağırlıklı
                tp = upper_line
                sl = lower_line * 0.98
                direction = 'LONG'
            
            return {
                'type': 'RISING_CHANNEL',
                'score': score,
                'confidence': confidence,
                'upper_slope': upper_slope,
                'lower_slope': lower_slope,
                'upper_line': upper_line,
                'lower_line': lower_line,
                'channel_width': channel_width,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'breakout_direction': breakout_direction,
                'breakout_strength': breakout_strength,
                'volume_confirmed': volume_confirmed,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                'volume_trend': volume_trend,
                'channel_position': channel_position,
                'slope_diff': slope_diff,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction
            }
        
        return None
        
    except Exception as e:
        return None


def detect_macd_divergence_advanced(df, window=40):
    """
    Gelişmiş MACD Divergence (uyumsuzluk) tespit eder.
    
    Kurallar:
    - Pozitif uyumsuzluk: Fiyat daha düşük dip yaparken MACD daha yüksek dip yapar
    - Negatif uyumsuzluk: Fiyat daha yüksek tepe yaparken MACD daha düşük tepe yapar
    - Daha hassas hesaplama ve güven skoru
    
    Returns:
        dict: Divergence detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        # Son window kadar veriyi al
        recent_data = df.tail(window)
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # MACD hesapla (daha hassas)
        ema12 = calculate_ema(closes, 12)
        ema26 = calculate_ema(closes, 26)
        macd_line = ema12 - ema26
        signal_line = calculate_ema(macd_line, 9)
        histogram = macd_line - signal_line
        
        # Yerel tepe ve dip noktalarını bul (fiyat) - daha hassas
        price_peaks = []
        price_troughs = []
        
        for i in range(3, len(closes) - 3):
            # Fiyat tepe noktası (5 mum kontrolü)
            if (closes[i] > closes[i-1] and closes[i] > closes[i-2] and closes[i] > closes[i-3] and
                closes[i] > closes[i+1] and closes[i] > closes[i+2] and closes[i] > closes[i+3]):
                price_peaks.append((i, closes[i]))
            
            # Fiyat dip noktası (5 mum kontrolü)
            if (closes[i] < closes[i-1] and closes[i] < closes[i-2] and closes[i] < closes[i-3] and
                closes[i] < closes[i+1] and closes[i] < closes[i+2] and closes[i] < closes[i+3]):
                price_troughs.append((i, closes[i]))
        
        # MACD tepe ve dip noktalarını bul - daha hassas
        macd_peaks = []
        macd_troughs = []
        
        for i in range(3, len(macd_line) - 3):
            # MACD tepe noktası (5 mum kontrolü)
            if (macd_line[i] > macd_line[i-1] and macd_line[i] > macd_line[i-2] and macd_line[i] > macd_line[i-3] and
                macd_line[i] > macd_line[i+1] and macd_line[i] > macd_line[i+2] and macd_line[i] > macd_line[i+3]):
                macd_peaks.append((i, macd_line[i]))
            
            # MACD dip noktası (5 mum kontrolü)
            if (macd_line[i] < macd_line[i-1] and macd_line[i] < macd_line[i-2] and macd_line[i] < macd_line[i-3] and
                macd_line[i] < macd_line[i+1] and macd_line[i] < macd_line[i+2] and macd_line[i] < macd_line[i+3]):
                macd_troughs.append((i, macd_line[i]))
        
        # Divergence tespiti (gelişmiş)
        divergences = []
        
        # Pozitif Divergence (Bullish) - Fiyat dip, MACD yükseliş
        if len(price_troughs) >= 2 and len(macd_troughs) >= 2:
            # Son iki fiyat dip
            price_trough1, price_trough2 = price_troughs[-2], price_troughs[-1]
            
            # Son iki MACD dip
            macd_trough1, macd_trough2 = macd_troughs[-2], macd_troughs[-1]
            
            # Fiyat düşerken MACD yükseliyor mu?
            if price_trough2[1] < price_trough1[1] and macd_trough2[1] > macd_trough1[1]:
                # Divergence gücü hesapla
                price_change = (price_trough1[1] - price_trough2[1]) / price_trough1[1]
                macd_change = (macd_trough2[1] - macd_trough1[1]) / abs(macd_trough1[1]) if macd_trough1[1] != 0 else 0
                
                # Güçlü divergence için minimum değişim
                if price_change > 0.02 and macd_change > 0.1:  # En az %2 fiyat düşüşü, %10 MACD yükselişi
                    strength = 'Strong' if price_change > 0.05 and macd_change > 0.2 else 'Weak'
                    
                    divergences.append({
                        'type': 'BULLISH_MACD_DIVERGENCE',
                        'indicator': 'MACD',
                        'price_trough1': price_trough1[1],
                        'price_trough2': price_trough2[1],
                        'macd_trough1': macd_trough1[1],
                        'macd_trough2': macd_trough2[1],
                        'price_change': price_change,
                        'macd_change': macd_change,
                        'strength': strength,
                        'time_gap': price_trough2[0] - price_trough1[0]
                    })
        
        # Negatif Divergence (Bearish) - Fiyat tepe, MACD düşüş
        if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
            # Son iki fiyat tepe
            price_peak1, price_peak2 = price_peaks[-2], price_peaks[-1]
            
            # Son iki MACD tepe
            macd_peak1, macd_peak2 = macd_peaks[-2], macd_peaks[-1]
            
            # Fiyat yükselirken MACD düşüyor mu?
            if price_peak2[1] > price_peak1[1] and macd_peak2[1] < macd_peak1[1]:
                # Divergence gücü hesapla
                price_change = (price_peak2[1] - price_peak1[1]) / price_peak1[1]
                macd_change = (macd_peak1[1] - macd_peak2[1]) / abs(macd_peak1[1]) if macd_peak1[1] != 0 else 0
                
                # Güçlü divergence için minimum değişim
                if price_change > 0.02 and macd_change > 0.1:  # En az %2 fiyat yükselişi, %10 MACD düşüşü
                    strength = 'Strong' if price_change > 0.05 and macd_change > 0.2 else 'Weak'
                    
                    divergences.append({
                        'type': 'BEARISH_MACD_DIVERGENCE',
                        'indicator': 'MACD',
                        'price_peak1': price_peak1[1],
                        'price_peak2': price_peak2[1],
                        'macd_peak1': macd_peak1[1],
                        'macd_peak2': macd_peak2[1],
                        'price_change': price_change,
                        'macd_change': macd_change,
                        'strength': strength,
                        'time_gap': price_peak2[0] - price_peak1[0]
                    })
        
        if divergences:
            # En güçlü divergence'ı seç
            strongest_divergence = max(divergences, key=lambda x: 1 if x['strength'] == 'Strong' else 0)
            
            current_price = closes[-1]
            
            # Hacim analizi
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            volume_confirmed = current_volume > avg_volume * 1.5
            
            # Hacim trendi
            recent_volumes = volumes[-5:]
            volume_trend = 'Yükselen' if recent_volumes[-1] > recent_volumes[0] else 'Düşen'
            
            # Hedef hesaplama (daha hassas)
            if 'BULLISH' in strongest_divergence['type']:
                # Pozitif divergence - yukarı hedef
                price_change = abs(strongest_divergence['price_trough2'] - strongest_divergence['price_trough1'])
                tp = current_price + price_change
                sl = current_price * 0.98
                direction = 'LONG'
            else:
                # Negatif divergence - aşağı hedef
                price_change = abs(strongest_divergence['price_peak2'] - strongest_divergence['price_peak1'])
                tp = current_price - price_change
                sl = current_price * 1.02
                direction = 'SHORT'
            
            # Skor hesaplama (gelişmiş)
            score = 60  # Base score
            
            # Divergence gücü (20 puan)
            if strongest_divergence['strength'] == 'Strong':
                score += 20
            
            # Hacim teyidi (10 puan)
            if volume_confirmed:
                score += 10
            
            # Zaman aralığı (10 puan)
            if strongest_divergence['time_gap'] >= 10:  # En az 10 mum
                score += 10
            
            # Güven seviyesi belirleme
            if score >= 85:
                confidence = 'High'
            elif score >= 70:
                confidence = 'Medium'
            else:
                confidence = 'Low'
            
            return {
                'type': strongest_divergence['type'],
                'score': score,
                'confidence': confidence,
                'indicator': strongest_divergence['indicator'],
                'strength': strongest_divergence['strength'],
                'price_change': strongest_divergence['price_change'],
                'macd_change': strongest_divergence['macd_change'],
                'time_gap': strongest_divergence['time_gap'],
                'all_divergences': divergences,
                'volume_confirmed': volume_confirmed,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1,
                'volume_trend': volume_trend,
                'entry_price': current_price,
                'tp': tp,
                'sl': sl,
                'direction': direction
            }
        
        return None
        
    except Exception as e:
        return None


def analyze_all_formations_advanced(df):
    """
    Tüm gelişmiş formasyonları analiz eder ve en iyi sinyali döner.
    
    Returns:
        dict: En iyi formasyon sinyali veya None
    """
    formations = []
    
    # Mevcut formasyonlar
    tobo = detect_tobo(df)
    if tobo:
        formations.append(tobo)
    
    obo = detect_obo(df)
    if obo:
        formations.append(obo)
    
    cup_handle = detect_cup_and_handle(df)
    if cup_handle:
        formations.append(cup_handle)
    
    falling_wedge = detect_falling_wedge(df)
    if falling_wedge:
        formations.append(falling_wedge)
    
    # Gelişmiş formasyonlar
    double_bottom_top = detect_double_bottom_top_advanced(df)
    if double_bottom_top:
        formations.append(double_bottom_top)
    
    bullish_bearish_flag = detect_bullish_bearish_flag_advanced(df)
    if bullish_bearish_flag:
        formations.append(bullish_bearish_flag)
    
    ascending_descending_triangle = detect_ascending_descending_triangle_advanced(df)
    if ascending_descending_triangle:
        formations.append(ascending_descending_triangle)
    
    symmetrical_triangle = detect_symmetrical_triangle_advanced(df)
    if symmetrical_triangle:
        formations.append(symmetrical_triangle)
    
    rising_channel = detect_rising_channel_advanced(df)
    if rising_channel:
        formations.append(rising_channel)
    
    # Mevcut kanal formasyonları
    rising_falling_channel = detect_rising_falling_channel(df)
    if rising_falling_channel:
        formations.append(rising_falling_channel)
    
    # Divergence formasyonları
    macd_divergence = detect_macd_divergence_advanced(df)
    if macd_divergence:
        formations.append(macd_divergence)
    
    macd_rsi_divergence = detect_macd_rsi_divergence(df)
    if macd_rsi_divergence:
        formations.append(macd_rsi_divergence)
    
    # En yüksek skorlu formasyonu seç
    if formations:
        # Sadece 'score' anahtarına sahip formasyonları filtrele
        valid_formations = [f for f in formations if isinstance(f, dict) and 'score' in f]
        if valid_formations:
            best_formation = max(valid_formations, key=lambda x: x['score'])
            return best_formation
    
    return None
    
    return None


def find_rectangle(df, min_touches=4, min_height_ratio=0.02, max_height_ratio=0.15):
    """
    Rectangle (Kutu Kanal) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # En son 50 mumda formasyon ara
        lookback = min(50, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            # Tepe noktası
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            # Dip noktası
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son tepe ve dip noktalarını al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Direnç ve destek seviyelerini hesapla
        resistance_level = np.mean([p[1] for p in recent_peaks])
        support_level = np.mean([t[1] for t in recent_troughs])
        
        # Yükseklik kontrolü
        height = resistance_level - support_level
        height_ratio = height / support_level
        
        if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
            return None
        
        # Direnç ve destek toleransı
        resistance_tolerance = height * 0.05
        support_tolerance = height * 0.05
        
        # Tepe ve dip noktalarının direnç/destek seviyelerine yakınlığını kontrol et
        resistance_touches = sum(1 for p in recent_peaks if abs(p[1] - resistance_level) <= resistance_tolerance)
        support_touches = sum(1 for t in recent_troughs if abs(t[1] - support_level) <= support_tolerance)
        
        if resistance_touches < 2 or support_touches < 2:
            return None
        
        # Mevcut fiyat pozisyonu
        current_price = closes[-1]
        breakout_threshold = height * 0.02  # %2 kırılım eşiği
        
        # Kırılım durumu
        breakout_up = current_price > resistance_level + breakout_threshold
        breakout_down = current_price < support_level - breakout_threshold
        in_range = support_level - breakout_threshold <= current_price <= resistance_level + breakout_threshold
        
        # Formasyon skoru
        score = min(100, (resistance_touches + support_touches) * 15)
        
        return {
            'type': 'RECTANGLE',
            'resistance': resistance_level,
            'support': support_level,
            'height': height,
            'resistance_touches': resistance_touches,
            'support_touches': support_touches,
            'breakout_up': breakout_up,
            'breakout_down': breakout_down,
            'in_range': in_range,
            'score': score,
            'current_price': current_price
        }
    except Exception as e:
        return None

def find_ascending_triangle(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.20):
    """
    Ascending Triangle (Yükselen Üçgen) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Yatay direnç çizgisi
        resistance_level = np.mean([p[1] for p in recent_peaks])
        resistance_tolerance = resistance_level * 0.02
        
        # Yükselen destek çizgisi (linear regression)
        if len(recent_troughs) >= 2:
            x = np.array([t[0] for t in recent_troughs])
            y = np.array([t[1] for t in recent_troughs])
            
            # Linear regression
            slope, intercept = np.polyfit(x, y, 1)
            
            # Pozitif eğim kontrolü (yükselen destek)
            if slope <= 0:
                return None
            
            # Destek çizgisinin güncel değeri
            current_support = slope * (len(df) - 1) + intercept
            
            # Yükseklik kontrolü
            height = resistance_level - current_support
            height_ratio = height / current_support
            
            if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                return None
            
            # Direnç dokunuşları
            resistance_touches = sum(1 for p in recent_peaks if abs(p[1] - resistance_level) <= resistance_tolerance)
            
            # Destek dokunuşları (eğimli çizgiye yakınlık)
            support_touches = 0
            for t in recent_troughs:
                expected_support = slope * t[0] + intercept
                if abs(t[1] - expected_support) <= resistance_tolerance:
                    support_touches += 1
            
            if resistance_touches < 2 or support_touches < 2:
                return None
            
            # Kırılım kontrolü
            current_price = closes[-1]
            breakout_threshold = height * 0.02
            
            breakout_up = current_price > resistance_level + breakout_threshold
            breakout_down = current_price < current_support - breakout_threshold
            
            # Formasyon skoru
            score = min(100, (resistance_touches + support_touches) * 15)
            
            return {
                'type': 'ASCENDING_TRIANGLE',
                'resistance': resistance_level,
                'support_slope': slope,
                'support_intercept': intercept,
                'current_support': current_support,
                'height': height,
                'resistance_touches': resistance_touches,
                'support_touches': support_touches,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'score': score,
                'current_price': current_price
            }
    except Exception as e:
        return None

def find_descending_triangle(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.20):
    """
    Descending Triangle (Alçalan Üçgen) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Yatay destek çizgisi
        support_level = np.mean([t[1] for t in recent_troughs])
        support_tolerance = support_level * 0.02
        
        # Alçalan direnç çizgisi (linear regression)
        if len(recent_peaks) >= 2:
            x = np.array([p[0] for p in recent_peaks])
            y = np.array([p[1] for p in recent_peaks])
            
            # Linear regression
            slope, intercept = np.polyfit(x, y, 1)
            
            # Negatif eğim kontrolü (alçalan direnç)
            if slope >= 0:
                return None
            
            # Direnç çizgisinin güncel değeri
            current_resistance = slope * (len(df) - 1) + intercept
            
            # Yükseklik kontrolü
            height = current_resistance - support_level
            height_ratio = height / support_level
            
            if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                return None
            
            # Destek dokunuşları
            support_touches = sum(1 for t in recent_troughs if abs(t[1] - support_level) <= support_tolerance)
            
            # Direnç dokunuşları (eğimli çizgiye yakınlık)
            resistance_touches = 0
            for p in recent_peaks:
                expected_resistance = slope * p[0] + intercept
                if abs(p[1] - expected_resistance) <= support_tolerance:
                    resistance_touches += 1
            
            if resistance_touches < 2 or support_touches < 2:
                return None
            
            # Kırılım kontrolü
            current_price = closes[-1]
            breakout_threshold = height * 0.02
            
            breakout_up = current_price > current_resistance + breakout_threshold
            breakout_down = current_price < support_level - breakout_threshold
            
            # Formasyon skoru
            score = min(100, (resistance_touches + support_touches) * 15)
            
            return {
                'type': 'DESCENDING_TRIANGLE',
                'support': support_level,
                'resistance_slope': slope,
                'resistance_intercept': intercept,
                'current_resistance': current_resistance,
                'height': height,
                'resistance_touches': resistance_touches,
                'support_touches': support_touches,
                'breakout_up': breakout_up,
                'breakout_down': breakout_down,
                'score': score,
                'current_price': current_price
            }
    except Exception as e:
        return None

def find_symmetrical_triangle(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.20):
    """
    Symmetrical Triangle (Simetrik Üçgen) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Direnç çizgisi (linear regression)
        if len(recent_peaks) >= 2:
            x_resistance = np.array([p[0] for p in recent_peaks])
            y_resistance = np.array([p[1] for p in recent_peaks])
            slope_resistance, intercept_resistance = np.polyfit(x_resistance, y_resistance, 1)
            
            # Destek çizgisi (linear regression)
            if len(recent_troughs) >= 2:
                x_support = np.array([t[0] for t in recent_troughs])
                y_support = np.array([t[1] for t in recent_troughs])
                slope_support, intercept_support = np.polyfit(x_support, y_support, 1)
                
                # Eğimlerin zıt yönlü olması kontrolü
                if slope_resistance >= 0 or slope_support <= 0:
                    return None
                
                # Çizgilerin yakınsaması kontrolü
                convergence_ratio = abs(slope_resistance - slope_support) / abs(slope_resistance)
                if convergence_ratio < 0.3:  # Çok yavaş yakınsama
                    return None
                
                # Güncel değerler
                current_resistance = slope_resistance * (len(df) - 1) + intercept_resistance
                current_support = slope_support * (len(df) - 1) + intercept_support
                
                # Yükseklik kontrolü
                height = current_resistance - current_support
                height_ratio = height / current_support
                
                if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                    return None
                
                # Dokunuş sayıları
                tolerance = height * 0.05
                
                resistance_touches = 0
                for p in recent_peaks:
                    expected_resistance = slope_resistance * p[0] + intercept_resistance
                    if abs(p[1] - expected_resistance) <= tolerance:
                        resistance_touches += 1
                
                support_touches = 0
                for t in recent_troughs:
                    expected_support = slope_support * t[0] + intercept_support
                    if abs(t[1] - expected_support) <= tolerance:
                        support_touches += 1
                
                if resistance_touches < 2 or support_touches < 2:
                    return None
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_threshold = height * 0.02
                
                breakout_up = current_price > current_resistance + breakout_threshold
                breakout_down = current_price < current_support - breakout_threshold
                
                # Formasyon skoru
                score = min(100, (resistance_touches + support_touches) * 15)
                
                return {
                    'type': 'SYMMETRICAL_TRIANGLE',
                    'resistance_slope': slope_resistance,
                    'resistance_intercept': intercept_resistance,
                    'support_slope': slope_support,
                    'support_intercept': intercept_support,
                    'current_resistance': current_resistance,
                    'current_support': current_support,
                    'height': height,
                    'resistance_touches': resistance_touches,
                    'support_touches': support_touches,
                    'breakout_up': breakout_up,
                    'breakout_down': breakout_down,
                    'score': score,
                    'current_price': current_price
                }
    except Exception as e:
        return None

def find_broadening_formation(df, min_touches=3, min_height_ratio=0.02, max_height_ratio=0.25):
    """
    Broadening Formation (Genleşen Üçgen / Megafoon) formasyonu tespit eder
    """
    try:
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        lookback = min(60, len(df))
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        
        for i in range(2, lookback-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # En son noktaları al
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs
        
        # Direnç çizgisi (linear regression)
        if len(recent_peaks) >= 2:
            x_resistance = np.array([p[0] for p in recent_peaks])
            y_resistance = np.array([p[1] for p in recent_peaks])
            slope_resistance, intercept_resistance = np.polyfit(x_resistance, y_resistance, 1)
            
            # Destek çizgisi (linear regression)
            if len(recent_troughs) >= 2:
                x_support = np.array([t[0] for t in recent_troughs])
                y_support = np.array([t[1] for t in recent_troughs])
                slope_support, intercept_support = np.polyfit(x_support, y_support, 1)
                
                # Eğimlerin aynı yönlü olması kontrolü (genleşme)
                if slope_resistance <= 0 or slope_support >= 0:
                    return None
                
                # Çizgilerin ıraksaması kontrolü
                divergence_ratio = abs(slope_resistance + slope_support) / abs(slope_resistance)
                if divergence_ratio < 0.3:  # Çok yavaş ıraksama
                    return None
                
                # Güncel değerler
                current_resistance = slope_resistance * (len(df) - 1) + intercept_resistance
                current_support = slope_support * (len(df) - 1) + intercept_support
                
                # Yükseklik kontrolü
                height = current_resistance - current_support
                height_ratio = height / current_support
                
                if height_ratio < min_height_ratio or height_ratio > max_height_ratio:
                    return None
                
                # Dokunuş sayıları
                tolerance = height * 0.05
                
                resistance_touches = 0
                for p in recent_peaks:
                    expected_resistance = slope_resistance * p[0] + intercept_resistance
                    if abs(p[1] - expected_resistance) <= tolerance:
                        resistance_touches += 1
                
                support_touches = 0
                for t in recent_troughs:
                    expected_support = slope_support * t[0] + intercept_support
                    if abs(t[1] - expected_support) <= tolerance:
                        support_touches += 1
                
                if resistance_touches < 2 or support_touches < 2:
                    return None
                
                # Kırılım kontrolü
                current_price = closes[-1]
                breakout_threshold = height * 0.02
                
                breakout_up = current_price > current_resistance + breakout_threshold
                breakout_down = current_price < current_support - breakout_threshold
                
                # Formasyon skoru
                score = min(100, (resistance_touches + support_touches) * 15)
                
                return {
                    'type': 'BROADENING_FORMATION',
                    'resistance_slope': slope_resistance,
                    'resistance_intercept': intercept_resistance,
                    'support_slope': slope_support,
                    'support_intercept': intercept_support,
                    'current_resistance': current_resistance,
                    'current_support': current_support,
                    'height': height,
                    'resistance_touches': resistance_touches,
                    'support_touches': support_touches,
                    'breakout_up': breakout_up,
                    'breakout_down': breakout_down,
                    'score': score,
                    'current_price': current_price
                }
    except Exception as e:
        return None

def detect_rising_wedge(df, window=40):
    """
    Rising Wedge (Yükselen Kama) formasyonu tespit eder.
    
    Kurallar:
    - Yükselen tepe ve diplerden oluşmalı (yüksekten daha yüksek kapanışlara doğru sıkışan yapı)
    - En az 3 tepe ve 3 dip tespit edilmeli
    - Kırılım alt çizgiyi aşağı kırarsa geçerli sayılmalı
    - Hacim kırılımda artmalı (1.5x veya üzeri)
    
    Returns:
        dict: Formasyon detayları veya None
    """
    if len(df) < window:
        return None
    
    try:
        recent_data = df.tail(window)
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values
        volumes = recent_data['volume'].values
        
        # Tepe ve dip noktalarını bul
        peaks = []
        troughs = []
        for i in range(2, len(closes) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                peaks.append((i, highs[i]))
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                troughs.append((i, lows[i]))
        if len(peaks) < 3 or len(troughs) < 3:
            return None
        recent_peaks = peaks[-3:]
        recent_troughs = troughs[-3:]
        peak_prices = [p[1] for p in recent_peaks]
        trough_prices = [t[1] for t in recent_troughs]
        # Tepe trendi kontrolü - yükselen
        peak_trend = all(peak_prices[i] < peak_prices[i+1] for i in range(len(peak_prices)-1))
        # Dip trendi kontrolü - yükselen ama daha yavaş
        trough_trend = all(trough_prices[i] < trough_prices[i+1] for i in range(len(trough_prices)-1))
        if not peak_trend or not trough_trend:
            return None
        peak_indices = [p[0] for p in recent_peaks]
        trough_indices = [t[0] for t in recent_troughs]
        peak_slope = np.polyfit(peak_indices, peak_prices, 1)[0]
        trough_slope = np.polyfit(trough_indices, trough_prices, 1)[0]
        # Üst trend daha dik olmalı (daha pozitif eğim)
        if peak_slope <= trough_slope:
            return None
        # Kama sıkışması kontrolü - son tepe ve dip arasındaki mesafe azalmalı
        first_gap = peak_prices[0] - trough_prices[0]
        last_gap = peak_prices[-1] - trough_prices[-1]
        if last_gap >= first_gap:
            return None
        # Kırılım kontrolü - son 5 mumda alt trend çizgisini aşağı kırma
        lower_trend_line = trough_prices[-1] + trough_slope * (len(closes) - 1 - trough_indices[-1])
        breakout_confirmed = False
        volume_confirmed = False
        for i in range(max(0, len(closes)-5), len(closes)):
            if closes[i] < lower_trend_line:
                avg_volume = np.mean(volumes[max(0, i-20):i])
                if volumes[i] > avg_volume * 1.5:
                    volume_confirmed = True
                breakout_confirmed = True
                breakout_price = closes[i]
                break
        if not breakout_confirmed:
            return None
        score = 0
        score += 30 if breakout_confirmed else 0
        score += 25 if volume_confirmed else 0
        score += 20 if abs(peak_slope) > abs(trough_slope) * 1.5 else 0
        score += 15 if last_gap < first_gap * 0.7 else 0
        if score >= 50:
            return {
                'type': 'RISING_WEDGE',
                'score': score,
                'peak_prices': peak_prices,
                'trough_prices': trough_prices,
                'breakout_price': breakout_price,
                'breakout_confirmed': breakout_confirmed,
                'volume_confirmed': volume_confirmed,
                'entry_price': breakout_price,
                'tp': breakout_price - (peak_prices[-1] - trough_prices[-1]),
                'sl': peak_prices[-1] * 1.02,
                'confidence': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low'
            }
        return None
    except Exception as e:
        return None

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