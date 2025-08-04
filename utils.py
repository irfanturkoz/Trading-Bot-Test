"""
Utility fonksiyonları
"""

def format_price(price):
    """
    Fiyatı formatlar
    
    Args:
        price (float): Formatlanacak fiyat
        
    Returns:
        str: Formatlanmış fiyat
    """
    if price >= 1000:
        return f"{price:,.0f}"
    elif price >= 1:
        return f"{price:.2f}"
    else:
        return f"{price:.6f}" 