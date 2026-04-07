"""
Comprehensive test of the AI Trading System pipeline.
Tests: Data loading, feature engineering, prediction, multi-timeframe, and trading signals.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_data_loading():
    """Test 1: Data loading and indicator generation"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Data Loading & Indicator Generation")
    logger.info("=" * 70)
    
    try:
        from data.multi_asset_fetcher import fetch_asset_data
        from data.technical_indicators import get_feature_columns, add_indicators
        
        test_symbols = ["RELIANCE.NS", "TCS.NS", "BTC-USD"]
        
        for symbol in test_symbols:
            logger.info(f"\n  Testing {symbol}...")
            df = fetch_asset_data(symbol)
            
            # Check OHLCV
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"    ✗ Missing OHLCV columns!")
                return False
            
            logger.info(f"    ✓ OHLCV present ({len(df)} rows)")
            
            # Check indicators
            feature_cols = get_feature_columns()
            missing_features = [col for col in feature_cols if col not in df.columns]
            
            if missing_features:
                logger.error(f"    ✗ Missing features: {missing_features}")
                return False
            
            logger.info(f"    ✓ All {len(feature_cols)} indicators present")
            
            # Check for NaN
            nan_count = df.isna().sum().sum()
            if nan_count > 0:
                logger.warning(f"    ⚠ {nan_count} NaN values (expected after dropna)")
        
        logger.info("\n✅ TEST 1 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prepare_data():
    """Test 2: Data preparation with consistent features"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Data Preparation")
    logger.info("=" * 70)
    
    try:
        from data.multi_asset_fetcher import fetch_asset_data
        from training.prepare_data import prepare_data
        from data.technical_indicators import get_feature_columns
        
        df = fetch_asset_data("RELIANCE.NS")
        X, y, scaler, feature_columns = prepare_data(df)
        
        # Verify structure
        expected_cols = 5 + len(get_feature_columns())  # OHLCV + indicators
        
        if len(feature_columns) != expected_cols:
            logger.error(f"  ✗ Feature count mismatch: {len(feature_columns)} vs {expected_cols}")
            return False
        
        logger.info(f"  ✓ Feature count: {len(feature_columns)}")
        
        # Verify Close is at index 3
        if feature_columns[3] != 'Close':
            logger.error(f"  ✗ Close not at index 3: {feature_columns[3]}")
            return False
        
        logger.info(f"  ✓ Close column at index 3")
        
        # Verify scaler
        if scaler.n_features_in_ != len(feature_columns):
            logger.error(f"  ✗ Scaler mismatch: {scaler.n_features_in_} vs {len(feature_columns)}")
            return False
        
        logger.info(f"  ✓ Scaler features: {scaler.n_features_in_}")
        logger.info(f"  ✓ Data shape: X={X.shape}, y={y.shape}")
        
        logger.info("\n✅ TEST 2 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction():
    """Test 3: Single day prediction"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Single Day Prediction")
    logger.info("=" * 70)
    
    try:
        from prediction.predict import predict_asset
        from data.multi_asset_fetcher import fetch_asset_data
        
        test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
        
        for symbol in test_symbols:
            logger.info(f"\n  Predicting {symbol}...")
            
            # Get current price
            df = fetch_asset_data(symbol)
            current_price = df['Close'].iloc[-1]
            
            # Get prediction
            pred_price = predict_asset(symbol)
            
            # Validate
            change_pct = ((pred_price - current_price) / current_price) * 100
            
            if abs(change_pct) > 10:
                logger.error(f"    ✗ Unrealistic prediction: {change_pct:+.2f}%")
                return False
            
            logger.info(f"    ✓ Current: ₹{current_price:.2f} → Pred: ₹{pred_price:.2f} ({change_pct:+.2f}%)")
        
        logger.info("\n✅ TEST 3 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_timeframe():
    """Test 4: Multi-timeframe predictions"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Multi-Timeframe Predictions")
    logger.info("=" * 70)
    
    try:
        from prediction.predict_multi_timeframe import predict_multi_timeframe
        from data.multi_asset_fetcher import fetch_asset_data
        
        symbol = "RELIANCE.NS"
        logger.info(f"\n  Testing {symbol}...")
        
        # Get current price
        df = fetch_asset_data(symbol)
        current_price = df['Close'].iloc[-1]
        
        # Get multi-timeframe predictions
        preds = predict_multi_timeframe(symbol)
        
        # Validate each timeframe
        timeframes = ['tomorrow', 'weekly', 'monthly', 'quarterly']
        all_valid = True
        
        for tf in timeframes:
            if tf not in preds:
                logger.error(f"    ✗ Missing {tf} prediction")
                all_valid = False
                continue
            
            pred = preds[tf]
            change_pct = ((pred - current_price) / current_price) * 100
            
            max_change = {
                'tomorrow': 10,
                'weekly': 20,
                'monthly': 35,
                'quarterly': 50
            }
            
            if abs(change_pct) > max_change.get(tf, 50):
                logger.error(f"    ✗ {tf}: {change_pct:+.2f}% exceeds limit")
                all_valid = False
            else:
                logger.info(f"    ✓ {tf}: ₹{pred:.2f} ({change_pct:+.2f}%)")
        
        if not all_valid:
            return False
        
        logger.info("\n✅ TEST 4 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trading_signals():
    """Test 5: Trading signals and profit calculation"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Trading Signals & Profit Calculation")
    logger.info("=" * 70)
    
    try:
        from trading.trading_signal import generate_signal
        from trading.profit_calculator import calculate_profit
        
        test_cases = [
            (100, 110, "BUY"),      # +10%
            (100, 95, "SELL"),      # -5%
            (100, 100.5, "HOLD"),   # +0.5%
        ]
        
        for current, pred, expected_signal in test_cases:
            sig = generate_signal(current, pred)
            profit_info = calculate_profit(current, pred, 10000)
            
            logger.info(
                f"  Current: ₹{current:.2f} → Pred: ₹{pred:.2f} | "
                f"Signal: {sig['signal']} | Profit: ₹{profit_info['profit']:.0f}"
            )
            
            if sig['signal'] != expected_signal:
                logger.error(f"    ✗ Expected {expected_signal}, got {sig['signal']}")
                return False
        
        logger.info("\n✅ TEST 5 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_best_trade_scanner():
    """Test 6: Best trade scanner"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: Best Trade Scanner")
    logger.info("=" * 70)
    
    try:
        from scanner.best_trade_scanner import scan_stocks, scan_crypto
        
        logger.info("\n  Scanning stocks...")
        stocks_df = scan_stocks()
        
        if not stocks_df.empty:
            logger.info(f"  ✓ Found {len(stocks_df)} stock trades")
            logger.info(f"    Top BUY: {stocks_df[stocks_df['Signal']=='BUY'].head(1).get('Asset', 'N/A').values}")
        else:
            logger.warning("  ⚠ No stock trades found (may be normal)")
        
        logger.info("\n  Scanning crypto...")
        crypto_df = scan_crypto()
        
        if not crypto_df.empty:
            logger.info(f"  ✓ Found {len(crypto_df)} crypto trades")
            logger.info(f"    Top BUY: {crypto_df[crypto_df['Signal']=='BUY'].head(1).get('Asset', 'N/A').values}")
        else:
            logger.warning("  ⚠ No crypto trades found (may be normal)")
        
        logger.info("\n✅ TEST 6 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    logger.info("\n\n╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "AI TRADING SYSTEM PIPELINE TEST" + " " * 22 + "║")
    logger.info("╚" + "=" * 68 + "╝\n")
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Data Preparation", test_prepare_data),
        ("Single Day Prediction", test_prediction),
        ("Multi-Timeframe Prediction", test_multi_timeframe),
        ("Trading Signals", test_trading_signals),
        ("Best Trade Scanner", test_best_trade_scanner),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Unhandled error in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        logger.info(f"  {test_name:.<45} {status}")
    
    logger.info("=" * 70)
    logger.info(f"RESULT: {passed}/{total} tests passed")
    logger.info("=" * 70 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
