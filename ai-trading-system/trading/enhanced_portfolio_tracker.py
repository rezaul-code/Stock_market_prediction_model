import pandas as pd
import os
from datetime import datetime
import numpy as np

HISTORY_FILE = 'data/trade_history.csv'

class PortfolioTracker:
    def __init__(self):
        self.history_file = HISTORY_FILE
        self.ensure_csv()

    def ensure_csv(self):
        "Create enhanced CSV with all fields."
        if not os.path.exists(self.history_file):
            df = pd.DataFrame(columns=[
                'date', 'symbol', 'signal', 'confidence_pct', 'trend', 'risk_level',
                'entry_price', 'predicted_price', 'actual_price', 
                'stop_loss', 'take_profit', 'position_size', 
                'risk_amount', 'reward_amount', 'profit_loss', 'win'
            ])
            df.to_csv(self.history_file, index=False)

    def log_trade(self, rec: dict, actual_price: float = None):
        "Enhanced logging for intelligence layer."
        df = pd.read_csv(self.history_file) if os.path.exists(self.history_file) else pd.DataFrame()
        
        new_trade = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': rec['symbol'],
            'signal': rec['signal'],
            'confidence_pct': rec.get('confidence_pct', 0),
            'trend': rec.get('trend', 'UNKNOWN'),
            'risk_level': rec.get('risk_level', 'MEDIUM'),
            'entry_price': rec['entry_price'],
            'predicted_price': rec.get('predicted_price', 0),
            'stop_loss': rec.get('stop_loss', 0),
            'take_profit': rec.get('take_profit', 0),
            'position_size': rec.get('position_size', 0),
            'risk_amount': rec.get('risk_amount', 0),
            'reward_amount': rec.get('reward_amount', 0),
            'profit_loss': 0,
            'win': False
        }
        
        if actual_price:
            # Calculate P&L vs entry
            multiplier = 1 if new_trade['signal'] in ['BUY', 'STRONG_BUY'] else -1
            pl = (actual_price - new_trade['entry_price']) * new_trade['position_size'] * multiplier
            new_trade.update({
                'actual_price': actual_price,
                'profit_loss': round(pl, 2),
                'win': pl > 0
            })
        
        # Append and save
        new_df = pd.DataFrame([new_trade])
        df = pd.concat([df, new_df], ignore_index=True) if not df.empty else new_df
        df.to_csv(self.history_file, index=False)
        
        print(f"✅ Logged trade: {new_trade['symbol']} {new_trade['signal']} (Conf: {new_trade['confidence_pct']:.1f}%)")
        return new_trade

    def get_performance(self) -> dict:
        "Enhanced performance tracker per task spec."
        if os.path.exists(self.history_file):
            df = pd.read_csv(self.history_file)
            if not df.empty:
                closed_trades = df[df['actual_price'].notna()]
                
                total_pl = df['profit_loss'].sum()
                total_trades = len(df)
                winning_trades = len(closed_trades[closed_trades['win'] == True]) if len(closed_trades) > 0 else 0
                win_rate = (winning_trades / len(closed_trades)) * 100 if len(closed_trades) > 0 else 0
                loss_rate = 100 - win_rate
                
                # Best performing asset
                if 'profit_loss' in df.columns:
                    asset_perf = df.groupby('symbol')['profit_loss'].sum().sort_values(ascending=False)
                    best_asset = asset_perf.index[0] if len(asset_perf) > 0 else 'N/A'
                    best_asset_profit = asset_perf.iloc[0]
                else:
                    best_asset = 'N/A'
                    best_asset_profit = 0
                
                return {
                    'total_profit': round(total_pl, 2),
                    'total_trades': total_trades,
                    'closed_trades': len(closed_trades),
                    'win_rate': f'{win_rate:.1f}%',
                    'loss_rate': f'{loss_rate:.1f}%',
                    'avg_profit_per_trade': round(total_pl / total_trades, 2) if total_trades > 0 else 0,
                    'best_asset': best_asset,
                    'best_asset_profit': round(best_asset_profit, 2),
                    'recent_trades': df.tail(10)[['date', 'symbol', 'signal', 'profit_loss', 'win']].to_dict('records')
                }
        return {
            'total_profit': 0, 'total_trades': 0, 'closed_trades': 0,
            'win_rate': '0%', 'loss_rate': '0%', 'best_asset': 'N/A',
            'recent_trades': []
        }

tracker = PortfolioTracker()
log_trade = tracker.log_trade
get_performance = tracker.get_performance

