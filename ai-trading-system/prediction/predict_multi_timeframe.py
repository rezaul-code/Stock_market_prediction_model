import numpy as np
import pandas as pd
import tensorflow as tf
import os
import joblib
from data.multi_asset_fetcher import fetch_asset_data

def predict_multi_timeframe(symbol):
    """
    Multi-timeframe prediction using autoregressive forecasting.
    
    Returns:
    {
        'tomorrow': 1-step pred,
        'weekly': 5-step pred,
        'monthly': 20-step pred, 
        'quarterly': 60-step pred,
        'current_price': float
    }
    """
    print(f"Multi-timeframe prediction for {symbol}...")
    
    # Load model and scaler (shared)
    model_path = 'models/lstm_model.h5'
    scaler_path = 'models/scaler.pkl'
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError("Run training first.")
    
    model = tf.keras.models.load_model(model_path)
    scaler = joblib.load(scaler_path)
    
    feature_columns = [
        "Close",
        "RSI_14",
        "MACD",
        "ATR",
        "Bollinger_Width"
    ]
    
    seq_length = 60
    
    # Fetch data
    df = fetch_asset_data(symbol)
    if len(df) < seq_length:
        raise ValueError(f"Insufficient data for {symbol}")
    
    current_price = df['Close'].iloc[-1]
    
    # History for autoregression: last seq_length rows
    history = df[feature_columns].tail(seq_length).copy().reset_index(drop=True)
    
    horizons = {
        'tomorrow': 1,
        'weekly': 5, 
        'monthly': 20,
        'quarterly': 60
    }
    
    predictions = {}
    
    temp_history = history.copy()
    
    for tf_name, steps in horizons.items():
        print(f"  Predicting {tf_name} ({steps} steps)...")
        
        for step in range(steps):
            # Take last seq_length for prediction
            X_raw = temp_history[feature_columns].tail(seq_length).values
            X_scaled = scaler.transform(X_raw)
            X_input = X_scaled.reshape(1, seq_length, 5)
            
            pred_scaled = model.predict(X_input, verbose=0)[0, 0]
            
            # Inverse
            dummy_pred = np.array([[pred_scaled, 0.0, 0.0, 0.0, 0.0]])
            pred_price = scaler.inverse_transform(dummy_pred)[0, 0]
            
            # Create new row: copy last, update Close
            new_row = temp_history.iloc[-1].copy()
            new_row['Close'] = pred_price
            # Carry forward other features (approximation)
            
            temp_history = pd.concat([temp_history, new_row.to_frame().T], ignore_index=True)
        
        predictions[tf_name] = float(pred_price)
    
    predictions['current_price'] = float(current_price)
    
    print("Multi-timeframe prediction complete")
    return predictions

if __name__ == "__main__": 
    preds = predict_multi_timeframe("RELIANCE.NS")
    print(preds)

