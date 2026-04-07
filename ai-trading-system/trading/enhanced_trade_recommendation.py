from .enhanced_signals import SmartSignalEngine
from .enhanced_risk_manager import risk_manager
from .portfolio_tracker import tracker, get_performance
from typing import Dict, Optional

def get_full_recommendation(
    symbol: str = 'RELIANCE.NS', 
    capital: float = 100000.0,
    risk_pct: float = None
) -> Dict:
    """
    Enhanced Trade Recommendation Engine - Full Intelligence Layer.
    
    Outputs task-required:
    - Current Trend
    - Prediction
    - Signal
    - Confidence
    - Stop Loss / Take Profit
    - Risk Level / Position Size
    - Performance History
    """
    # Step 1: Get smart signal
    sig = SmartSignalEngine().generate_smart_signal(symbol)
    
    # Step 2: Get risk management levels
    rec = risk_manager.get_recommendation(symbol, capital, risk_pct)
    
    # Step 3: Get performance context
    perf = get_performance()
    
    # Combine into comprehensive recommendation
    full_rec = {
        **sig,      # Signal Intelligence (trend, conf, strict rules)
        **rec,      # Risk Management (SL/TP/size/R:R)
        'portfolio': {
            'total_profit': perf.get('total_profit', 0),
            'win_rate': perf.get('win_rate', '0%'),
            'total_trades': perf.get('total_trades', 0),
            'best_asset': perf.get('best_asset', 'N/A'),
            'recent_trades': perf.get('recent_trades', [])
        }
    }
    
    # Log to history
    tracker.log_trade(full_rec)
    
    return full_rec

def get_multi_asset_recommendations(
    symbols: list = None,
    capital: float = 100000.0
) -> Dict:
    """Multi-asset scanner for top stocks/crypto."""
    from config.assets import TOP_25_STOCKS, TOP_10_CRYPTO
    
    if symbols is None:
        symbols = TOP_25_STOCKS[:5] + TOP_10_CRYPTO[:3]  # Top performers
    
    recs = {}
    for sym in symbols:
        try:
            recs[sym] = get_full_recommendation(sym, capital)
        except:
            recs[sym] = {'error': 'Data unavailable'}
    
    # Sort by confidence/score
    sorted_recs = dict(sorted(recs.items(), key=lambda x: x[1].get('confidence_pct', 0) if 'error' not in x[1] else -1, reverse=True))
    
    return {
        'recommendations': sorted_recs,
        'best_trade': list(sorted_recs.values())[0] if sorted_recs else None
    }

# Convenience exports
recommend_trade = get_full_recommendation
scan_multi_assets = get_multi_asset_recommendations

