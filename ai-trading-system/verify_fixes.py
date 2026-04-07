#!/usr/bin/env python3
"""
Quick verification that all fixes are in place.
Run this BEFORE retraining to verify code updates.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

GREEN = '✅'
RED = '❌'

def check_file_content(filepath, search_text, description):
    """Check if file contains specific text"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if search_text in content:
                logger.info(f"{GREEN} {description}")
                return True
            else:
                logger.error(f"{RED} {description}")
                return False
    except Exception as e:
        logger.error(f"{RED} Cannot read {filepath}: {e}")
        return False

def main():
    logger.info("\n" + "="*70)
    logger.info("🔍 VERIFICATION: All Fixes Applied")
    logger.info("="*70 + "\n")
    
    checks = [
        # Fix 1: multi_asset_fetcher.py
        ("data/multi_asset_fetcher.py",
         "from data.technical_indicators import add_indicators",
         "Fix 1: multi_asset_fetcher uses full indicator pipeline"),
        
        # Fix 2: prepare_data.py
        ("training/prepare_data.py",
         "Close MUST be at index 3",
         "Fix 2: prepare_data.py documents Close at index 3"),
        
        # Fix 3: ensemble_utils.py
        ("prediction/ensemble_utils.py",
         "close_idx = 3",
         "Fix 3: ensemble_utils.py uses Close at index 3"),
        
        # Fix 4: train_model.py
        ("training/train_model.py",
         "close_idx=3",
         "Fix 4: train_model.py unscale with Close at index 3"),
        
        # Fix 5: predict_multi_timeframe.py
        ("prediction/predict_multi_timeframe.py",
         "temp_with_indicators = add_indicators",
         "Fix 5: predict_multi_timeframe recalculates indicators"),
        
        # Fix 6: predict.py
        ("prediction/predict.py",
         "current_price=current_price",
         "Fix 6: predict.py uses proper validation"),
        
        # Fix 7: ensemble_utils validation
        ("prediction/ensemble_utils.py",
         "current_price * 0.90",
         "Fix 7: Prediction validation with ±10% limit"),
    ]
    
    results = []
    for filepath, search_text, description in checks:
        if os.path.exists(filepath):
            result = check_file_content(filepath, search_text, description)
            results.append(result)
        else:
            logger.error(f"{RED} File not found: {filepath}")
            results.append(False)
    
    logger.info("\n" + "="*70)
    passed = sum(results)
    total = len(results)
    logger.info(f"RESULT: {passed}/{total} fixes verified\n")
    
    if all(results):
        logger.info("✅ All fixes are in place! Ready to retrain.\n")
        logger.info("Next: Run 'python retrain_all.py' to rebuild models\n")
        return True
    else:
        logger.error(f"❌ {total - passed} fixes are missing or incomplete!\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
