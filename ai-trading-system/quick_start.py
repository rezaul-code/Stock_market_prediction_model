#!/usr/bin/env python3
"""
QUICK START SCRIPT - Run Complete Workflow
AI Trading System - One command to get everything working

Usage:
    python quick_start.py [train|test|dashboard|scan]
"""

import sys
import os
import subprocess
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║     🤖 AI TRADING SYSTEM - QUICK START                        ║
║                                                               ║
║          Fixed & Ready to Use!                              ║
╚═══════════════════════════════════════════════════════════════╝
"""

def run_train():
    """Train model on all stocks"""
    logger.info(BANNER)
    logger.info("\n📊 STEP 1: Building Data Pipeline...")
    logger.info("━" * 60)
    
    try:
        from training.run_pipeline import run_pipeline
        df, scaler, cols = run_pipeline()
        logger.info(f"✅ Data pipeline complete: {df.shape[0]} rows, {len(cols)} features\n")
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")
        return False
    
    logger.info("📈 STEP 2: Training Ensemble Model...")
    logger.info("━" * 60)
    
    try:
        from training.train_model import train_ensemble_models
        train_ensemble_models()
        logger.info("✅ Model training complete\n")
    except Exception as e:
        logger.error(f"❌ Training error: {e}")
        return False
    
    logger.info("🎉 TRAINING COMPLETE!")
    logger.info("\nNext step: python quick_start.py test")
    return True

def run_test():
    """Test predictions"""
    logger.info(BANNER)
    logger.info("\n🧪 RUNNING PREDICTION TESTS...")
    logger.info("━" * 60)
    
    try:
        exec(open("test_predictions.py").read())
        logger.info("\n✅ TESTS COMPLETE!")
        return True
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

def run_dashboard():
    """Launch dashboard"""
    logger.info(BANNER)
    logger.info("\n📊 LAUNCHING DASHBOARD...")
    logger.info("━" * 60)
    logger.info("💡 Open browser to: http://localhost:8501")
    logger.info("🔄 Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])
    except KeyboardInterrupt:
        logger.info("\n✅ Dashboard stopped")
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return False
    
    return True

def run_scan():
    """Run best trade scanner"""
    logger.info(BANNER)
    logger.info("\n🔍 SCANNING FOR BEST TRADES...")
    logger.info("━" * 60)
    
    try:
        from scanner.best_trade_scanner import scan_all
        results = scan_all()
        if not results.empty:
            logger.info("\n✅ SCAN COMPLETE!")
            return True
        else:
            logger.warning("\n⚠️  No results found")
            return False
    except Exception as e:
        logger.error(f"❌ Scan error: {e}")
        return False

def run_all():
    """Run all steps in sequence"""
    logger.info(BANNER)
    
    logger.info("\n" + "=" * 60)
    logger.info("RUNNING COMPLETE WORKFLOW")
    logger.info("=" * 60)
    
    steps = [
        ("Training Model", run_train),
        ("Testing Predictions", run_test),
        ("Scanning Trades", run_scan),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n### {step_name} ###")
        if not step_func():
            logger.error(f"❌ {step_name} failed!")
            return False
        logger.info(f"✅ {step_name} complete")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ALL STEPS COMPLETE!")
    logger.info("=" * 60)
    logger.info("\nNext: python quick_start.py dashboard")
    return True

def main():
    parser = argparse.ArgumentParser(description="AI Trading System - Quick Start")
    parser.add_argument(
        "action",
        nargs="?",
        default="help",
        choices=["train", "test", "dashboard", "scan", "all", "help"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.getcwd())
    
    if args.action == "train":
        run_train()
    elif args.action == "test":
        run_test()
    elif args.action == "dashboard":
        run_dashboard()
    elif args.action == "scan":
        run_scan()
    elif args.action == "all":
        run_all()
    else:
        logger.info(BANNER)
        logger.info("""
Available Commands:
──────────────────────────────────────────────────────────────

1. Train model on all 25 stocks:
   $ python quick_start.py train
   ⏱️  10-15 minutes (first time only)

2. Test predictions on sample stocks/crypto:
   $ python quick_start.py test
   ⏱️  5-10 minutes

3. Launch interactive dashboard:
   $ python quick_start.py dashboard
   🌐 Opens http://localhost:8501

4. Scan for best trading opportunities:
   $ python quick_start.py scan
   ⏱️  3-5 minutes

5. Run all steps in sequence:
   $ python quick_start.py all
   ⏱️  25-30 minutes (complete setup)

Quick Start Examples:
──────────────────────────────────────────────────────────────

First time setup (complete):
   $ python quick_start.py train
   $ python quick_start.py test
   $ python quick_start.py dashboard

Just use the dashboard:
   $ python quick_start.py dashboard

Automated everything:
   $ python quick_start.py all

Documentation:
   $ python FIX_GUIDE.py
        """)

if __name__ == "__main__":
    main()
