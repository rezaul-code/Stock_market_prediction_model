import pandas as pd
import numpy as np
import os
from prediction.predict import predict_next_price

def generate_signal():
    """
    Generate trading signal based on predicted vs current price.
    Returns dict with current_price, predicted_price, and signal (BUY/SELL/HOLD).
    """
    try:
        print("Fetching latest price...")
        
        # Load processed data to get current close price
        data_path = 'data/processed_data.csv'
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Processed data not found at {data_path}. Please run data preprocessing first.")
        
        df = pd.read_csv(data_path)
        if df.empty or 'Close' not in df.columns:
            raise ValueError("Invalid data format. 'Close' column missing or empty.")
        
        current_price = float(df['Close'].iloc[-1])
        print(f"Current price: ${current_price:.2f}")
        
        print("Getting prediction...")
        predicted_price = predict_next_price()
        print(f"Predicted price: ${predicted_price:.2f}")
        
        print("Generating signal...")
        
        # Trading logic with 0.5% threshold
        if predicted_price > current_price * 1.005:
            signal = "BUY"
        elif predicted_price < current_price * 0.995:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        confidence = abs(predicted_price / current_price - 1) * 100
        confidence_str = f"{confidence:.2f}%"
        
        print("Signal generated")
        
        return {
            "current_price": current_price,
            "predicted_price": predicted_price,
            "signal": signal,
            "confidence": confidence_str
        }
    
    except Exception as e:
        print(f"Error generating signal: {str(e)}")
        raise

if __name__ == "__main__":
    signal_data = generate_signal()
    print(f"\nTrading Signal: {signal_data['signal']}")
    print(f"Current: ${signal_data['current_price']:.2f}")
    print(f"Predicted: ${signal_data['predicted_price']:.2f}")

