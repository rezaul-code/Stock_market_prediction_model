from .smart_signals import SmartSignalEngine
from .risk_manager import risk_manager
from .portfolio_tracker import tracker

def get_full_recommendation(symbol: str = 'RELIANCE.NS', capital: float = 100000.0) -> dict:
    "Full recommendation w/ signal + risk + history."
    sig = SmartSignalEngine().generate_smart_signal(symbol)
    rec = risk_manager.get_recommendation(symbol, capital)
    
    full_rec = {**sig, **rec}
    
    tracker.log_trade(full_rec)
    
    return full_rec

recommend_trade = get_full_recommendation
