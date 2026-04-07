import sys
import os
import pandas as pd
import numpy as np
from typing import Dict

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.technical_indicators import add_indicators
from data.multi_asset_fetcher import fetch_asset_data
from prediction.predict import predict_asset
from data.stock_data import get_stock_data

class SmartSignalEngine:
    def __init__(self):
        self.signal_strength = {
            'STRONG_BUY': 5,
            'BUY': 3,
            'HOLD': 0,
            'SELL': -3,
            'STRONG_SELL': -5
        }

    def get_latest_indicators(self, symbol: str = 'RELIANCE.NS') -> Dict:
        "Fetch latest OHLCV + add all indicators."
        try:
            df = fetch_asset_data(symbol) if 'fetch_asset_data' in globals() else get_stock_data(symbol)
            df = add_indicators(df)
            latest = df.iloc[-1]
            return {
                'close': float(latest['Close']),
                'rsi': float(latest.get('RSI_14', 50)),
                'macd': float(latest.get('MACD', 0)),
                'macd_signal': float(latest.get('MACD_signal', 0)),
                'macd_hist': float(latest.get('MACD_hist', 0)),
                'ema50': float(latest.get('SMA_50', latest['Close'])),
                'ema200': float(latest.get('SMA_200', latest['Close'])),
                'atr': float(latest.get('ATR_14', latest['Close']*0.01)),
                'adx': float(latest.get('ADX', 20)),
                'volume': float(latest.get('Volume', 0))
            }
        except Exception as e:
            print(f"Error fetching indicators: {e}")
            return {}

    def _trend_signal(self, ema50: float, ema200: float, adx: float) -> str:
        "Detect trend."
        if ema50 > ema200 and adx > 25:
            return 'BULLISH'
        elif ema50 < ema200 and adx > 25:
            return 'BEARISH'
        return 'SIDEWAYS'

    def _momentum_signal(self, rsi: float, macd: float, macd_signal: float, macd_hist: float) -> str:
        "RSI + MACD momentum."
        rsi_signal = 'OVERBOUGHT' if rsi > 70 else 'OVERSOLD' if rsi < 30 else 'NEUTRAL'
        macd_bull = macd > macd_signal and macd_hist > 0
        macd_bear = macd < macd_signal and macd_hist < 0
        if macd_bull and rsi_signal != 'OVERBOUGHT':
            return 'BULLISH'
        elif macd_bear and rsi_signal != 'OVERSOLD':
            return 'BEARISH'
        return 'NEUTRAL'

    def generate_smart_signal(self, symbol: str = 'RELIANCE.NS') -> Dict:
        "Main smart signal."
        indicators = self.get_latest_indicators(symbol)
        close = indicators['close']
        
        pred_price = predict_asset(symbol)
        pred_pct = (pred_price - close) / close * 100
        
        pred_signal = 'STRONG_BUY' if pred_pct > 2 else 'BUY' if pred_pct > 1 else \
                      'STRONG_SELL' if pred_pct < -2 else 'SELL' if pred_pct < -1 else 'HOLD'
        
        trend = self._trend_signal(indicators['ema50'], indicators['ema200'], indicators['adx'])
        momentum = self._momentum_signal(indicators['rsi'], indicators['macd'], 
                                       indicators['macd_signal'], indicators['macd_hist'])
        
        score = self.signal_strength[pred_signal] + \
                (2 if trend == 'BULLISH' else -2 if trend == 'BEARISH' else 0) + \
                (1 if momentum == 'BULLISH' else -1 if momentum == 'BEARISH' else 0)
        
        if score >= 6: final_signal = 'STRONG_BUY'
        elif score >= 3: final_signal = 'BUY'
        elif score <= -6: final_signal = 'STRONG_SELL'
        elif score <= -3: final_signal = 'SELL'
        else: final_signal = 'HOLD'
        
        pred_conf = abs(pred_pct) * 10
        vol_factor = 100 / (indicators['atr']/close * 100 + 1)
        trend_conf = min(indicators['adx'], 50)
        confidence = min((pred_conf + vol_factor*0.3 + trend_conf*0.3), 100)
        
        return {
            'symbol': symbol,
            'current_price': close,
            'predicted_price': pred_price,
            'prediction_pct': pred_pct,
            'signal': final_signal,
            'score': score,
            'trend': trend,
            'momentum': momentum,
            'confidence': f'{confidence:.1f}%',
            'confidence_pct': confidence,
            'indicators': indicators
        }

generate_signal = SmartSignalEngine().generate_smart_signal
generate_default_signal = lambda: SmartSignalEngine().generate_smart_signal()
