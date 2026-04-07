import numpy as np
from typing import Dict
from .enhanced_signals import SmartSignalEngine  # Updated to new signals

class RiskManager:
    def __init__(self, risk_per_trade: float = 0.015, rr_ratio: float = 2.0):  # 1.5% default (1-2% range)
        """
        Enhanced Risk Manager.
        risk_per_trade: 0.01-0.02 (1-2%)
        rr_ratio: Risk:Reward (default 1:2)
        """
        self.risk_pct = np.clip(risk_per_trade, 0.01, 0.02)  # Enforce 1-2%
        self.rr_ratio = rr_ratio
        self.signal_engine = SmartSignalEngine()

    def calculate_levels(self, symbol: str, capital: float = 100000, risk_pct: float = None) -> Dict:
        "Calculate dynamic SL/TP/Position Size with configurable risk."
        if risk_pct is None:
            risk_pct = self.risk_pct
            
        sig_data = self.signal_engine.generate_smart_signal(symbol)
        ind = sig_data['indicators']
        close = ind['close']
        atr = ind['atr']
        
        # ATR-based levels (task spec)
        sl_distance = 2 * atr  # Stop Loss = 2x ATR
        tp_distance = self.rr_ratio * sl_distance  # Take Profit = 2x ATR
        
        if sig_data['signal'] in ['STRONG_BUY', 'BUY']:
            stop_loss = close - sl_distance
            take_profit = close + tp_distance
        else:  # SELL/STRONG_SELL
            stop_loss = close + sl_distance
            take_profit = close - tp_distance
        
        risk_amount = capital * risk_pct
        position_size = risk_amount / abs(sl_distance)  # Shares/contracts
        
        actual_rr = abs(tp_distance / sl_distance)
        
        return {
            'symbol': symbol,
            'capital': capital,
            'risk_per_trade_pct': f'{risk_pct*100:.1f}%',
            'entry_price': round(close, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'sl_distance': round(sl_distance, 2),
            'tp_distance': round(tp_distance, 2),
            'atr': round(atr, 2),
            'position_size': round(position_size, 0),
            'risk_amount': round(risk_amount, 2),
            'reward_amount': round(risk_amount * actual_rr, 2),
            'risk_reward_ratio': f'1:{actual_rr:.1f}',
            'signal': sig_data['signal'],
            'confidence': sig_data['confidence'],
            'risk_level': sig_data.get('risk_level', 'MEDIUM')
        }

    def get_recommendation(self, symbol: str, capital: float = 100000, risk_pct: float = None) -> Dict:
        "Full enhanced trade recommendation w/ intelligence layer."
        levels = self.calculate_levels(symbol, capital, risk_pct)
        sig_data = self.signal_engine.generate_smart_signal(symbol)
        
        # Enhanced risk level combining confidence + volatility
        conf_pct = sig_data['confidence_pct']
        vol_high = levels['atr'] / levels['entry_price'] > 0.05  # >5% ATR risky
        risk_level = 'LOW' if conf_pct > 70 and not vol_high else 'MEDIUM' if conf_pct > 50 else 'HIGH'
        
        return {
            **sig_data,  # Signal intelligence
            **levels,    # Risk management
            'market_trend': sig_data['trend'],
            'trade_readiness': 'EXECUTE' if risk_level == 'LOW' else 'CAUTION' if risk_level == 'MEDIUM' else 'AVOID',
            'capital_required': round(levels['position_size'] * levels['entry_price'], 2)
        }

# Global instances
risk_manager = RiskManager(risk_per_trade=0.015)  # 1.5% default
calculate_risk_levels = risk_manager.calculate_levels
get_trade_recommendation = risk_manager.get_recommendation

