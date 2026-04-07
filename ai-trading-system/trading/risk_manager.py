import numpy as np
from typing import Dict
from .smart_signals import SmartSignalEngine

class RiskManager:
    def __init__(self, risk_per_trade: float = 0.01, rr_ratio: float = 2.0):
        "1% risk, 1:2 RR."
        self.risk_pct = risk_per_trade
        self.rr_ratio = rr_ratio
        self.signal_engine = SmartSignalEngine()

    def calculate_levels(self, symbol: str, capital: float = 100000) -> Dict:
        "Calculate SL/TP/Position Size."
        sig_data = self.signal_engine.generate_smart_signal(symbol)
        ind = sig_data['indicators']
        close = ind['close']
        atr = ind['atr']
        
        sl_distance = 2 * atr
        tp_distance = self.rr_ratio * sl_distance
        
        if sig_data['signal'] in ['STRONG_BUY', 'BUY']:
            stop_loss = close - sl_distance
            take_profit = close + tp_distance
        else:
            stop_loss = close + sl_distance
            take_profit = close - tp_distance
        
        risk_amount = capital * self.risk_pct
        position_size = risk_amount / sl_distance
        
        rr = abs(tp_distance / sl_distance)
        
        return {
            'symbol': symbol,
            'entry_price': close,
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'position_size': round(position_size, 0),
            'risk_amount': round(risk_amount, 2),
            'reward_amount': round(risk_amount * rr, 2),
            'risk_reward_ratio': f'1:{rr:.1f}',
            'signal': sig_data['signal'],
            'confidence': sig_data['confidence']
        }

    def get_recommendation(self, symbol: str, capital: float = 100000) -> Dict:
        "Full trade recommendation."
        levels = self.calculate_levels(symbol, capital)
        sig_data = self.signal_engine.generate_smart_signal(symbol)
        
        risk_level = 'LOW' if float(sig_data['confidence_pct']) > 70 else 'MEDIUM' if float(sig_data['confidence_pct']) > 50 else 'HIGH'
        
        return {
            **sig_data,
            **levels,
            'market_trend': sig_data['trend'],
            'risk_level': risk_level,
            'capital': capital
        }

risk_manager = RiskManager()
calculate_risk_levels = risk_manager.calculate_levels
get_trade_recommendation = risk_manager.get_recommendation
