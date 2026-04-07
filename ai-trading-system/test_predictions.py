#!/usr/bin/env python3
"""
Test script to verify predictions are working correctly and realistic.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from config.assets import TOP_25_STOCKS, TOP_10_CRYPTO
from prediction.predict import predict_asset
from data.multi_asset_fetcher import fetch_asset_data
from prediction.predict_multi_timeframe import predict_multi_timeframe

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_predictions():
    """Test predictions on multiple stocks and crypto."""
    
    logger.info("=" * 70)
    logger.info("🧪 AI TRADING SYSTEM - PREDICTION TEST")
    logger.info("=" * 70)
    
    # Test stocks
    test_stocks = TOP_25_STOCKS[:5]  # Test first 5 stocks
    
    logger.info("\n📊 TESTING STOCKS")
    logger.info("-" * 70)
    
    stock_results = []
    
    for symbol in test_stocks:
        try:
            logger.info(f"\n🔍 Testing {symbol}...")
            
            # Fetch current data
            df = fetch_asset_data(symbol)
            current_price = df['Close'].iloc[-1]
            recent_min = df['Close'].tail(100).min()
            recent_max = df['Close'].tail(100).max()
            
            # Get prediction
            pred_price = predict_asset(symbol)
            
            # Check if realistic
            change_pct = ((pred_price - current_price) / current_price) * 100
            is_realistic = (recent_min * 0.7 <= pred_price <= recent_max * 1.3)
            
            logger.info(f"  Current: ₹{current_price:.2f}")
            logger.info(f"  Predicted: ₹{pred_price:.2f}")
            logger.info(f"  Change: {change_pct:+.2f}%")
            logger.info(f"  Range: ₹{recent_min:.2f} - ₹{recent_max:.2f}")
            logger.info(f"  Valid: {'✅ YES' if is_realistic else '❌ NO'}")
            
            stock_results.append({
                'symbol': symbol,
                'current': current_price,
                'predicted': pred_price,
                'change': change_pct,
                'realistic': is_realistic
            })
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}")
    
    # Test crypto
    test_crypto = TOP_10_CRYPTO[:3]
    
    logger.info("\n\n₿ TESTING CRYPTO")
    logger.info("-" * 70)
    
    crypto_results = []
    
    for symbol in test_crypto:
        try:
            logger.info(f"\n🔍 Testing {symbol}...")
            
            # Fetch current data
            df = fetch_asset_data(symbol)
            current_price = df['Close'].iloc[-1]
            recent_min = df['Close'].tail(100).min()
            recent_max = df['Close'].tail(100).max()
            
            # Get prediction
            pred_price = predict_asset(symbol)
            
            # Check if realistic
            change_pct = ((pred_price - current_price) / current_price) * 100
            is_realistic = (recent_min * 0.7 <= pred_price <= recent_max * 1.3)
            
            logger.info(f"  Current: ${current_price:.2f}")
            logger.info(f"  Predicted: ${pred_price:.2f}")
            logger.info(f"  Change: {change_pct:+.2f}%")
            logger.info(f"  Range: ${recent_min:.2f} - ${recent_max:.2f}")
            logger.info(f"  Valid: {'✅ YES' if is_realistic else '❌ NO'}")
            
            crypto_results.append({
                'symbol': symbol,
                'current': current_price,
                'predicted': pred_price,
                'change': change_pct,
                'realistic': is_realistic
            })
            
        except Exception as e:
            logger.error(f"  ❌ Error: {str(e)}")
    
    # Test multi-timeframe
    logger.info("\n\n📅 TESTING MULTI-TIMEFRAME")
    logger.info("-" * 70)
    
    test_symbol = TOP_25_STOCKS[0]
    
    try:
        logger.info(f"\nTesting multi-timeframe for {test_symbol}...")
        
        multi_preds = predict_multi_timeframe(test_symbol)
        
        logger.info(f"\nCurrent Price: ₹{multi_preds['current_price']:.2f}")
        
        for tf, pred in [('tomorrow', multi_preds['tomorrow']),
                         ('weekly', multi_preds['weekly']),
                         ('monthly', multi_preds['monthly']),
                         ('quarterly', multi_preds['quarterly'])]:
            change = ((pred - multi_preds['current_price']) / multi_preds['current_price']) * 100
            logger.info(f"  {tf.upper():10}: ₹{pred:8.2f} ({change:+.2f}%)")
        
    except Exception as e:
        logger.error(f"Multi-timeframe error: {str(e)}")
    
    # Summary
    logger.info("\n\n" + "=" * 70)
    logger.info("📈 SUMMARY")
    logger.info("=" * 70)
    
    all_results = stock_results + crypto_results
    realistic_count = sum(1 for r in all_results if r['realistic'])
    total_count = len(all_results)
    
    logger.info(f"✅ Realistic predictions: {realistic_count}/{total_count}")
    
    if realistic_count == total_count:
        logger.info("🎉 All predictions are realistic!")
    else:
        logger.warning(f"⚠️  {total_count - realistic_count} predictions need review")
    
    logger.info("\n" + "=" * 70)

if __name__ == "__main__":
    test_predictions()
