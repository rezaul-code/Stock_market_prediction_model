import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
import os
import joblib
import logging
from data.technical_indicators import add_indicators, get_feature_columns
from data.stock_data import get_stock_data
from data.multi_asset_fetcher import fetch_asset_data
from training.prepare_data import create_lstm_sequences
from .ensemble_utils import load_ensemble_models, ensemble_predict, ENSEMBLE_WEIGHTS, validate_prediction

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def predict_next_price():
    """Predict next price from processed data (backward compatible)."""
    logger.info("🔄 Loading Ensemble Models...")
    models = load_ensemble_models()
    scaler = models.pop('scaler')
    feature_columns = joblib.load('models/feature_columns.pkl')
    
    logger.info("📊 Preparing data...")
    df = pd.read_csv('data/processed_data.csv')
    
    seq_length = 60
    if len(df) < seq_length:
        raise ValueError("Dataset too short.")
    
    # Last seq_length for all models
    X_raw = df[feature_columns].tail(seq_length).values
    logger.info(f"  Input shape: {X_raw.shape}")
    
    X_scaled = scaler.transform(X_raw)
    
    # LSTM input
    X_lstm = X_scaled.reshape(1, seq_length, -1)
    
    # Tree input (flattened)
    X_tree = X_scaled.reshape(1, -1)
    
    logger.info("🎯 Ensemble Prediction...")
    prediction = ensemble_predict(X_lstm, X_tree, models, scaler)
    
    # Validate prediction
    recent_close = df['Close'].tail(100).values
    min_price = recent_close.min()
    max_price = recent_close.max()
    prediction = validate_prediction(prediction, min_price, max_price)
    
    logger.info(f"✅ Prediction: ₹{prediction:.2f} (Recent range: {min_price:.2f}-{max_price:.2f})")
    
    return prediction

def predict_asset(symbol):
    """Predict for new asset (fetch fresh data, add indicators)."""
    logger.info(f"🔄 Ensemble prediction for {symbol}...")
    
    models = load_ensemble_models()
    scaler = models.pop('scaler')
    feature_columns = joblib.load('models/feature_columns.pkl')
    
    # Fetch & enhance data using SAME pipeline as training
    try:
        df = get_stock_data(symbol)
    except Exception as e:
        logger.warning(f"  get_stock_data failed for {symbol}, trying fetch_asset_data: {e}")
        df = fetch_asset_data(symbol)

    # Add technical indicators if not already present
    if 'EMA_9' not in df.columns:
        df = add_indicators(df)
    
    seq_length = 60
    
    # Drop NaN and check length
    df_clean = df.dropna()
    if len(df_clean) < seq_length:
        raise ValueError(f"Need more data for {symbol}: {len(df_clean)} < {seq_length}")
    
    logger.info(f"  Data: {len(df_clean)} rows, {len(feature_columns)} features")
    
    # Prepare recent data - select only the features used during training
    recent_df = df_clean[feature_columns].tail(seq_length)
    X_raw = recent_df.values
    
    logger.info(f"  Input shape: {X_raw.shape}")
    
    X_scaled = scaler.transform(X_raw)
    X_lstm = X_scaled.reshape(1, seq_length, -1)
    X_tree = X_scaled.reshape(1, -1)
    
    # Get predictions from individual models first
    logger.info(f"  📊 Individual Model Predictions:")
    lstm_pred_scaled = models['lstm'].predict(X_lstm, verbose=0)[0, 0]
    xgb_pred_scaled = models['xgboost'].predict(X_tree)[0]
    rf_pred_scaled = models['randomforest'].predict(X_tree)[0]
    
    close_idx = 3
    dummy_lstm = np.zeros((1, scaler.n_features_in_))
    dummy_lstm[0, close_idx] = lstm_pred_scaled
    lstm_price = scaler.inverse_transform(dummy_lstm)[0, close_idx]
    
    dummy_xgb = np.zeros((1, scaler.n_features_in_))
    dummy_xgb[0, close_idx] = xgb_pred_scaled
    xgb_price = scaler.inverse_transform(dummy_xgb)[0, close_idx]
    
    dummy_rf = np.zeros((1, scaler.n_features_in_))
    dummy_rf[0, close_idx] = rf_pred_scaled
    rf_price = scaler.inverse_transform(dummy_rf)[0, close_idx]
    
    logger.info(f"     LSTM: ₹{lstm_price:.2f}")
    logger.info(f"     XGBoost: ₹{xgb_price:.2f}")
    logger.info(f"     RandomForest: ₹{rf_price:.2f}")
    
    # Get ensemble prediction
    prediction = ensemble_predict(X_lstm, X_tree, models, scaler)
    
    # Validate prediction with current price for reasonable bounds
    recent_close = df_clean['Close'].tail(100).values
    min_price = recent_close.min()
    max_price = recent_close.max()
    current_price = df_clean['Close'].iloc[-1]
    
    prediction = validate_prediction(prediction, min_price, max_price, current_price=current_price)
    
    # Calculate confidence based on model agreement
    from .ensemble_utils import calculate_model_confidence
    confidence, model_agreement = calculate_model_confidence(lstm_price, xgb_price, rf_price)
    
    change_pct = ((prediction - current_price) / current_price) * 100
    logger.info(f"  ✅ {symbol} FINAL PREDICTION: ₹{prediction:.2f} ({change_pct:+.2f}%)")
    logger.info(f"  📈 Confidence: {confidence:.1f}% (Model agreement: max divergence {model_agreement['max_divergence']:.2f}%)")
    logger.info("")
    
    return prediction

if __name__ == "__main__":
    pred = predict_next_price()
    logger.info(f"🎉 Ensemble Predicted Next Price: ₹{pred:.2f}")