import numpy as np
import pandas as pd
import tensorflow as tf
import os
import joblib
from sklearn.preprocessing import MinMaxScaler
from data.multi_asset_fetcher import fetch_asset_data
from .predict_multi_timeframe import predict_multi_timeframe

def predict_next_price():
    print("Loading model...")
    
    # Load trained model
    model_path = 'models/lstm_model.h5'
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Run train_model.py first.")
    
    model = tf.keras.models.load_model(model_path)
    
    print("Loading scaler...")
    scaler_path = 'models/scaler.pkl'
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found at {scaler_path}. Run train_model.py first.")
    scaler = joblib.load(scaler_path)
    
    print("Preparing data...")
    
    # Load processed dataset
    data_path = 'data/processed_data.csv'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run run_pipeline.py first.")
    
    df = pd.read_csv(data_path)
    
    feature_columns = [
        "Close",
        "RSI_14",
        "MACD",
        "ATR",
        "Bollinger_Width"
    ]
    
    # Use 'Close' column and last 60 days for prediction
    seq_length = 60
    if len(df) < seq_length:
        raise ValueError("Dataset too short for prediction. Need at least 60 data points.")
    
    X_raw = df[feature_columns].tail(seq_length).values
    
    # Scale with loaded scaler
    X_scaled = scaler.transform(X_raw)
    
    # Prepare input
    X = X_scaled.reshape(1, seq_length, 5)
    
    print("Predicting...")
    
    # Predict next price
    predicted_scaled = model.predict(X, verbose=0)[0, 0]
    
    # Inverse transform
    dummy_pred = np.array([[predicted_scaled, 0.0, 0.0, 0.0, 0.0]])
    predicted_price = scaler.inverse_transform(dummy_pred)[0, 0]
    
    print("Prediction completed")
    
    return float(predicted_price)


def predict_asset(symbol):
    """
    Predict next price for given asset symbol using loaded model.
    """
    print(f"Predicting for {symbol}...")
    
    # Load trained model (shared)
    model_path = 'models/lstm_model.h5'
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Run train_model.py first.")
    model = tf.keras.models.load_model(model_path)
    
    # Load scaler (shared)
    scaler_path = 'models/scaler.pkl'
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found at {scaler_path}. Run train_model.py first.")
    scaler = joblib.load(scaler_path)
    
    # Fetch fresh data
    df = fetch_asset_data(symbol)
    
    feature_columns = [
        "Close",
        "RSI_14",
        "MACD",
        "ATR",
        "Bollinger_Width"
    ]
    
    seq_length = 60
    if len(df) < seq_length:
        raise ValueError(f"Dataset too short for {symbol}. Need at least {seq_length} data points.")
    
    # Prepare input (same as existing)
    X_raw = df[feature_columns].tail(seq_length).values
    X_scaled = scaler.transform(X_raw)
    X = X_scaled.reshape(1, seq_length, 5)
    
    print("Predicting...")
    predicted_scaled = model.predict(X, verbose=0)[0, 0]
    
    # Inverse transform
    dummy_pred = np.array([[predicted_scaled, 0.0, 0.0, 0.0, 0.0]])
    predicted_price = scaler.inverse_transform(dummy_pred)[0, 0]
    
    print("Prediction completed")
    return float(predicted_price)

if __name__ == "__main__":
    next_price = predict_next_price()
    print(f"Predicted next stock price: ${next_price:.2f}")

