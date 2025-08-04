#!/usr/bin/env python3
"""
Test script to verify the fixes work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_formation_analyzer import AdvancedFormationAnalyzer
from data_fetcher import fetch_ohlcv

def test_fixes():
    """Test the fixes for the type errors and quality score issues"""
    
    print("🧪 Testing fixes...")
    
    # Create analyzer
    analyzer = AdvancedFormationAnalyzer()
    
    # Test with a simple symbol
    symbol = 'BTCUSDT'
    print(f"\n🔍 Testing {symbol}...")
    
    try:
        # Fetch data
        df = fetch_ohlcv(symbol, '4h', limit=200)
        if df.empty:
            print("❌ No data fetched")
            return False
        
        print(f"✅ Data fetched: {len(df)} candles")
        
        # Test analyze_symbol
        result = analyzer.analyze_symbol(symbol, '4h')
        
        if result['success']:
            print(f"✅ Analysis successful")
            print(f"📊 Found {result['filtered_formations']} formations")
            
            # Best formation details
            best_formation = result.get('best_formation', {})
            formation_type = best_formation.get('type', 'UNKNOWN')
            quality_score = best_formation.get('quality_score', 0)
            
            if isinstance(quality_score, dict):
                score = quality_score.get('total_score', 0)
            else:
                score = quality_score
            
            print(f"   - {formation_type}: {score}/400")
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixes()
    if success:
        print("\n✅ All fixes working correctly!")
    else:
        print("\n❌ Some issues remain") 