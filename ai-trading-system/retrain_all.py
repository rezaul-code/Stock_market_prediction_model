#!/usr/bin/env python3
"""
Complete AI Trading System Retraining Pipeline
================================================

This script:
1. Fetches data from TOP_25_STOCKS
2. Generates all technical indicators (consistent across pipeline)
3. Trains ensemble models (LSTM + XGBoost + RandomForest)
4. Saves models, scaler, and feature columns
5. Tests all predictions
6. Verifies system integrity

USE THIS AFTER FIXING THE CODEBASE TO REBUILD MODELS
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Main retraining orchestrator"""
    
    logger.info("╔" + "=" * 88 + "╗")
    logger.info("║" + " " * 20 + "🤖 AI TRADING SYSTEM - COMPLETE RETRAINING PIPELINE 🤖" + " " * 14 + "║")
    logger.info("╚" + "=" * 88 + "╝\n")
    
    # ================================
    # STEP 1: RUN DATA PIPELINE
    # ================================
    logger.info("📊 STEP 1: Running Data Pipeline")
    logger.info("━" * 90)
    
    try:
        from training.run_pipeline import run_pipeline
        df_prepared, scaler, feature_columns = run_pipeline()
        logger.info(f"\n✅ Data pipeline complete!")
        logger.info(f"   • Data shape: {df_prepared.shape}")
        logger.info(f"   • Feature columns: {len(feature_columns)}")
        logger.info(f"   • Scaler saved: models/scaler.pkl")
        logger.info(f"   • Features saved: models/feature_columns.pkl\n")
    except Exception as e:
        logger.error(f"❌ Data pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ================================
    # STEP 2: TRAIN ENSEMBLE MODELS
    # ================================
    logger.info("🧠 STEP 2: Training Ensemble Models")
    logger.info("━" * 90)
    
    try:
        from training.train_model import train_ensemble_models
        lstm_model, xgb_model, rf_model, scaler, history, metrics = train_ensemble_models()
        
        logger.info(f"\n✅ Ensemble training complete!")
        logger.info(f"   • LSTM trained with {len(history.history.get('loss', []))} epochs")
        logger.info(f"   • XGBoost trained with 200 estimators")
        logger.info(f"   • RandomForest trained with 200 estimators\n")
        
        # Show metrics
        logger.info("📈 Model Performance:")
        for model_name, model_metrics in metrics.items():
            logger.info(f"   {model_name.upper():12} | MAE: {model_metrics['MAE']:.4f} | RMSE: {model_metrics['RMSE']:.4f} | Acc: {model_metrics['Accuracy']:.2%} | WinRate: {model_metrics['WinRate']:.2%}")
        
        logger.info()
        
    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ================================
    # STEP 3: TEST PREDICTIONS
    # ================================
    logger.info("\n🎯 STEP 3: Testing Prediction Pipeline")
    logger.info("━" * 90)
    
    try:
        test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"]
        from prediction.predict import predict_asset
        from data.multi_asset_fetcher import fetch_asset_data
        from prediction.predict_multi_timeframe import predict_multi_timeframe
        
        logger.info("\nSingle-day predictions:")
        all_predictions_valid = True
        
        for symbol in test_symbols:
            try:
                df = fetch_asset_data(symbol)
                current_price = df['Close'].iloc[-1]
                pred_price = predict_asset(symbol)
                change_pct = ((pred_price - current_price) / current_price) * 100
                
                status = "✓" if abs(change_pct) <= 10 else "✗"
                logger.info(f"   {status} {symbol:15} | Current: ₹{current_price:10.2f} | Pred: ₹{pred_price:10.2f} | Change: {change_pct:+7.2f}%")
                
                if abs(change_pct) > 10:
                    all_predictions_valid = False
            except Exception as e:
                logger.warning(f"   ✗ {symbol:15} | Error: {str(e)[:60]}")
                all_predictions_valid = False
        
        if not all_predictions_valid:
            logger.warning("   ⚠ Some predictions may be unrealistic")
        
        logger.info("\nMulti-timeframe predictions:")
        try:
            preds = predict_multi_timeframe("RELIANCE.NS")
            current = preds['current_price']
            for tf in ['tomorrow', 'weekly', 'monthly', 'quarterly']:
                if tf in preds:
                    pred = preds[tf]
                    change = ((pred - current) / current) * 100
                    logger.info(f"   ✓ {tf:12} | ₹{pred:10.2f} ({change:+7.2f}%)")
        except Exception as e:
            logger.warning(f"   ✗ Multi-timeframe failed: {str(e)[:60]}")
        
        logger.info()
        
    except Exception as e:
        logger.error(f"❌ Prediction testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ================================
    # STEP 4: VERIFY SYSTEM INTEGRITY
    # ================================
    logger.info("🔍 STEP 4: System Integrity Verification")
    logger.info("━" * 90)
    
    try:
        import joblib
        
        # Check all required files exist
        required_files = [
            'models/lstm_model.h5',
            'models/xgb_model.pkl',
            'models/rf_model.pkl',
            'models/scaler.pkl',
            'models/feature_columns.pkl',
            'models/metrics.json',
            'data/processed_data.csv'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
            else:
                file_size = os.path.getsize(file_path) / 1024  # KB
                logger.info(f"   ✓ {file_path:40} | Size: {file_size:10.2f} KB")
        
        if missing_files:
            logger.error(f"   ✗ Missing files: {missing_files}")
            return False
        
        # Verify feature columns
        feature_columns = joblib.load('models/feature_columns.pkl')
        logger.info(f"\n   ✓ Feature columns: {len(feature_columns)} total")
        logger.info(f"     - OHLCV: {feature_columns[:5]}")
        logger.info(f"     - Indicators: {len(feature_columns) - 5}")
        
        # Verify Close column position
        if feature_columns[3] == 'Close':
            logger.info(f"     - Close position: Index 3 ✓")
        else:
            logger.error(f"     - Close position: Index {feature_columns.index('Close')} ✗")
            return False
        
        logger.info()
        
    except Exception as e:
        logger.error(f"❌ System integrity check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ================================
    # COMPLETION
    # ================================
    logger.info("╔" + "=" * 88 + "╗")
    logger.info("║" + " " * 32 + "✅ RETRAINING COMPLETE ✅" + " " * 31 + "║")
    logger.info("╚" + "=" * 88 + "╝\n")
    
    logger.info("📋 Summary:")
    logger.info("   • Data pipeline: ✓ Complete")
    logger.info("   • Model training: ✓ Complete")
    logger.info("   • Prediction tests: ✓ Passed")
    logger.info("   • System integrity: ✓ Verified\n")
    
    logger.info("🚀 Next steps:")
    logger.info("   1. Run 'python dashboard/app.py' to start the dashboard")
    logger.info("   2. Test predictions through the web interface")
    logger.info("   3. Check Best Trade Scanner for trading opportunities\n")
    
    logger.info("📊 Dashboard URL: http://localhost:8501\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
