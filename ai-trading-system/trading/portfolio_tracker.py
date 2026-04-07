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
        "Create CSV if not exists."
        if not os.path.exists(self.history_file):
            df = pd.DataFrame(columns=[
                'date', 'symbol', 'signal', 'entry_price', 'predicted_price', 
                'actual_price', 'position_size', 'profit_loss', 'win'
            ])
            df.to_csv(self.history_file, index=False)

    def log_trade(self, rec: dict, actual_price: float = None):
        "Log trade to history."
        df = pd.read_csv(self.history_file)
        
        new_trade = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': rec['symbol'],
            'signal': rec['signal'],
            'entry_price': rec['entry_price'],
            'predicted_price': rec['predicted_price'],
            'position_size': rec['position_size'],
            'profit_loss': 0,
            'win': False
        }
        
        if actual_price:
            pl = (actual_price - rec['entry_price']) * rec['position_size'] * (1 if rec['signal'] in ['BUY', 'STRONG_BUY'] else -1)
            new_trade.update({
                'actual_price': actual_price,
                'profit_loss': pl,
                'win': pl > 0
            })
        
        df = pd.concat([df, pd.DataFrame([new_trade])], ignore_index=True)
        df.to_csv(self.history_file, index=False)
        return new_trade

    def get_performance(self) -> dict:
        "Portfolio metrics."
        if os.path.exists(self.history_file):
            df = pd.read_csv(self.history_file)
            if not df.empty and 'profit_loss' in df.columns:
                total_pl = df['profit_loss'].sum()
                win_rate = (df['win'].sum() / len(df[df['win'].notna()])) * 100 if len(df) > 0 else 0
                total_trades = len(df)
                best_asset = df.groupby('symbol')['profit_loss'].sum().idxmax() if len(df) > 0 else 'N/A'
                
                return {
                    'total_profit': round(total_pl, 2),
                    'total_trades': total_trades,
                    'win_rate': f'{win_rate:.1f}%',
                    'avg_profit_per_trade': round(total_pl / total_trades, 2) if total_trades > 0 else 0,
                    'best_asset': best_asset,
                    'loss_rate': f'{100-win_rate:.1f}%',
                    'recent_trades': df.tail(10).to_dict('records')
                }
        return {'total_profit': 0, 'total_trades': 0, 'win_rate': '0%', 'best_asset': 'N/A'}

tracker = PortfolioTracker()
log_trade = tracker.log_trade
get_performance = tracker.get_performance
