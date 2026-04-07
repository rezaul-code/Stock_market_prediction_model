import numpy as np
import tensorflow as tf
import os
import joblib
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ENSEMBLE_WEIGHTS = {'lstm': 0.4, 'xgboost': 0.3, 'randomforest': 0.3}

def load_ensemble_models():
    """Load all trained models and scaler."""
    model_paths = {
        'lstm': 'models/lstm_model.h5',
        'xgboost': 'models/xgb_model.pkl',
        'randomforest': 'models/rf_model.pkl',
        'scaler': 'models/scaler.pkl',
        'features': 'models/feature_columns.pkl'
    }
    
    models = {}
    for name, path in model_paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} not found at {path}. Run train_model.py first.")
        if name == 'lstm':
            models[name] = tf.keras.models.load_model(path, compile=False)
        else:
            models[name] = joblib.load(path)
    
    return models

def validate_prediction(pred_price, min_price, max_price, current_price=None):
    """
    Validate prediction against realistic range (NOT aggressive clamping).
    
    This prevents EXTREME outliers (e.g., 99999 or 0.001) while allowing
    real model predictions through.
    
    Args:
        pred_price: Predicted price
        min_price: Recent minimum price 
        max_price: Recent maximum price
        current_price: Current price (optional, for info only)
    
    Returns:
        Validated prediction price (may be slightly adjusted for extreme outliers only)
    """
    # Allow reasonable volatility: ±30% from current or ±20% from historical range
    price_range = max_price - min_price
    reasonable_lower = min_price * 0.70
    reasonable_upper = max_price * 1.30
    
    # Clamp only EXTREME outliers
    clamped = np.clip(pred_price, reasonable_lower, reasonable_upper)
    
    if clamped != pred_price:
        logger.warning(f"⚠️  OUTLIER prediction clamped: ₹{pred_price:.2f} → ₹{clamped:.2f}")
    
    return float(clamped)

def calculate_model_confidence(lstm_pred, xgb_pred, rf_pred):
    """
    Calculate confidence based on model agreement.
    
    - If all models close (~±2%): HIGH confidence (80-100%)
    - If models moderately aligned (±5%): MEDIUM confidence (50-80%)
    - If models diverge (>±5%): LOW confidence (20-50%)
    
    Args:
        lstm_pred: LSTM prediction (unscaled price)
        xgb_pred: XGBoost prediction (unscaled price)
        rf_pred: RandomForest prediction (unscaled price)
    
    Returns:
        confidence (0-100): float
        model_agreement_pct: dict with individual model % changes
    """
    avg_pred = (lstm_pred + xgb_pred + rf_pred) / 3
    
    # Calculate % difference from ensemble average
    lstm_diff = abs(lstm_pred - avg_pred) / avg_pred * 100
    xgb_diff = abs(xgb_pred - avg_pred) / avg_pred * 100
    rf_diff = abs(rf_pred - avg_pred) / avg_pred * 100
    
    max_diff = max(lstm_diff, xgb_diff, rf_diff)
    
    # Confidence scoring
    if max_diff < 2:
        confidence = 90 + (2 - max_diff) * 5  # 90-100%
    elif max_diff < 5:
        confidence = 60 + (5 - max_diff) * 6  # 60-90%
    elif max_diff < 10:
        confidence = 40 + (10 - max_diff) * 2  # 40-60%
    else:
        confidence = max(20, 50 - max_diff)  # 20-50%
    
    confidence = float(np.clip(confidence, 10, 100))
    
    model_agreement = {
        'lstm_pct': float(lstm_diff),
        'xgb_pct': float(xgb_diff),
        'rf_pct': float(rf_diff),
        'max_divergence': float(max_diff)
    }
    
    return confidence, model_agreement

def ensemble_predict(X_lstm_input, X_tree_input, models, scaler):
    """
    Generate ensemble prediction with unscaling and validation.
    
    Returns:
        Unscaled predicted price
    """
    logger.debug(f"LSTM input shape: {X_lstm_input.shape}")
    logger.debug(f"Tree input shape: {X_tree_input.shape}")
    logger.debug(f"Scaler features: {scaler.n_features_in_}")
    
    # LSTM
    lstm_pred_scaled = models['lstm'].predict(X_lstm_input, verbose=0)[0, 0]
    logger.debug(f"LSTM scaled pred: {lstm_pred_scaled:.6f}")
    
    # Trees
    xgb_pred_scaled = models['xgboost'].predict(X_tree_input)[0]
    rf_pred_scaled = models['randomforest'].predict(X_tree_input)[0]
    
    logger.debug(f"XGB scaled pred: {xgb_pred_scaled:.6f}, RF scaled pred: {rf_pred_scaled:.6f}")
    
    # Weighted ensemble (scaled)
    ensemble_scaled = (ENSEMBLE_WEIGHTS['lstm'] * lstm_pred_scaled + 
                      ENSEMBLE_WEIGHTS['xgboost'] * xgb_pred_scaled + 
                      ENSEMBLE_WEIGHTS['randomforest'] * rf_pred_scaled)
    
    logger.debug(f"Ensemble scaled pred: {ensemble_scaled:.6f}")
    
    # Unscale: Close column is ALWAYS at index 3 (Open=0, High=1, Low=2, Close=3, Volume=4)
    # This is guaranteed by prepare_data.py which puts OHLCV first
    close_idx = 3
    
    # Create dummy array to unscale INDIVIDUAL predictions
    dummy_lstm = np.zeros((1, scaler.n_features_in_))
    dummy_lstm[0, close_idx] = lstm_pred_scaled
    lstm_price = scaler.inverse_transform(dummy_lstm)[0, close_idx]
    
    dummy_xgb = np.zeros((1, scaler.n_features_in_))
    dummy_xgb[0, close_idx] = xgb_pred_scaled
    xgb_price = scaler.inverse_transform(dummy_xgb)[0, close_idx]
    
    dummy_rf = np.zeros((1, scaler.n_features_in_))
    dummy_rf[0, close_idx] = rf_pred_scaled
    rf_price = scaler.inverse_transform(dummy_rf)[0, close_idx]
    
    dummy_ensemble = np.zeros((1, scaler.n_features_in_))
    dummy_ensemble[0, close_idx] = ensemble_scaled
    pred_price = scaler.inverse_transform(dummy_ensemble)[0, close_idx]
    
    logger.info(f"  🤖 Model Predictions (UNSCALED):")
    logger.info(f"     LSTM: ₹{lstm_price:.2f}")
    logger.info(f"     XGBoost: ₹{xgb_price:.2f}")
    logger.info(f"     RandomForest: ₹{rf_price:.2f}")
    logger.info(f"     ✅ ENSEMBLE (Weighted): ₹{pred_price:.2f}")
    
    return float(pred_price)