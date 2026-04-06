import pandas as pd
import numpy as np
import os
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

def load_data(data_path):
    """Load and validate processed data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run training pipeline first.")
    
    df = pd.read_csv(data_path, parse_dates=['Date'], index_col='Date')
    if df.empty or 'Close' not in df.columns:
        raise ValueError("Data must contain 'Close' column and be non-empty.")
    
    return df

def historical_predict(model, hist_df):
    """Predict next price using historical data slice (no future leakage)."""
    seq_length = 60
    if len(hist_df) < seq_length:
        raise ValueError("Historical data too short for prediction.")
    
    close_prices = hist_df['Close'].tail(seq_length).values.reshape(-1, 1)
    scaler = MinMaxScaler()
    close_prices_scaled = scaler.fit_transform(close_prices)
    X = close_prices_scaled.reshape(1, seq_length, 1)
    
    predicted_scaled = model.predict(X, verbose=0)
    predicted_price = scaler.inverse_transform(predicted_scaled)[0, 0]
    
    return float(predicted_price)

def run_backtest():
    print("Running Backtest...")
    
    data_path = 'data/processed_data.csv'
    model_path = 'models/lstm_model.h5'
    
    try:
        df = load_data(data_path)
        if len(df) < 61:
            raise ValueError("Dataset too short for backtesting. Need at least 61 data points.")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Run train_model.py first.")
        
        model = tf.keras.models.load_model(model_path)
        
        print("Simulating trades...")
        
        initial_capital = 10000.0
        capital = initial_capital
        position = 0.0  # shares
        entry_price = 0.0
        total_trades = 0
        winning_trades = 0
        
        for i in range(60, len(df) - 1):
            current_price = df['Close'].iloc[i]
            hist_df = df.iloc[:i + 1]
            
            predicted_price = historical_predict(model, hist_df)
            
            if predicted_price > current_price * 1.001:  # Small threshold for noise
                signal = "BUY"
            elif predicted_price < current_price * 0.999:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            if signal == "BUY" and position == 0:
                position = capital / current_price
                entry_price = current_price
                print(f"BUY at day {i}: ${current_price:.2f}")
            
            elif signal == "SELL" and position > 0:
                next_price = df['Close'].iloc[i + 1]
                capital = position * next_price
                trade_profit = (next_price - entry_price) * position
                total_trades += 1
                if trade_profit > 0:
                    winning_trades += 1
                print(f"SELL at day {i+1}: ${next_price:.2f}, P/L: ${trade_profit:.2f}")
                position = 0.0
                entry_price = 0.0
        
        # Close any open position at final price
        if position > 0:
            final_price = df['Close'].iloc[-1]
            capital = position * final_price
            print(f"Final close at: ${final_price:.2f}")
        
        total_profit = capital - initial_capital
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        print("Backtest completed!")
        print(f"Initial Capital: ${initial_capital:.2f}")
        print(f"Final Capital: ${capital:.2f}")
        print(f"Total Profit: ${total_profit:.2f}")
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.2%}")
        
        return {
            "final_capital": round(capital, 2),
            "profit": round(total_profit, 2),
            "total_trades": total_trades,
            "win_rate": round(win_rate, 4)
        }
    
    except Exception as e:
        print(f"Backtest failed: {str(e)}")
        raise

if __name__ == "__main__":
    result = run_backtest()
    print("\n" + "="*50)
    print("BACKTEST RESULTS:")
    print(result)
    print("="*50)

