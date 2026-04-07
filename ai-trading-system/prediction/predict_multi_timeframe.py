import numpy as np
import pandas as pd
import joblib
import logging
from data.multi_asset_fetcher import fetch_asset_data
from data.technical_indicators import add_indicators, get_feature_columns
from training.prepare_data import create_lstm_sequences
from .ensemble_utils import load_ensemble_models, ensemble_predict, ENSEMBLE_WEIGHTS, validate_prediction

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def predict_multi_timeframe_ensemble(symbol, models, scaler, feature_columns, seq_length=60, steps_max=60):
    """
    Multi-timeframe prediction with proper indicator recalculation.
    
    For each step:
    1. Make prediction using current 60-day window
    2. Append to temporary history
    3. Recalculate ALL technical indicators on extended history
    4. Continue with fresh indicators
    """
    logger.info(f"🌐 Multi-timeframe ENSEMBLE prediction for {symbol}...")
    
    df = fetch_asset_data(symbol)
    df_clean = df.dropna()
    
    if len(df_clean) < seq_length + 100:
        raise ValueError(f"Insufficient data for {symbol}: {len(df_clean)} < {seq_length + 100}")
    
    current_price = df_clean['Close'].iloc[-1]
    logger.info(f"  📌 Current price: ₹{current_price:.2f}")
    
    # Get recent price range for validation (minimum clipping only - avoid EXTREME outliers)
    recent_prices = df_clean['Close'].tail(100).values
    min_price = recent_prices.min()
    max_price = recent_prices.max()
    
    horizons = {
        'tomorrow': 1,
        'weekly': 5,
        'monthly': 20,
        'quarterly': 60
    }
    
    predictions = {}
    
    for tf_name, steps in horizons.items():
        logger.info(f"  📈 Predicting {tf_name.upper()} ({steps} days)...")
        
        # Start with current data (keep OHLCV only, drop indicators for recalc)
        ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        temp_history = df_clean[ohlcv_cols].tail(seq_length + 50).copy()
        temp_history = temp_history.reset_index(drop=True)
        
        # Autoregressive prediction
        for step in range(steps):
            # Recalculate all indicators on current history
            temp_with_indicators = add_indicators(temp_history.copy())
            
            # Get last seq_length with indicators
            if len(temp_with_indicators) < seq_length:
                logger.warning(f"    ⚠️  Step {step+1}: Insufficient data after indicator calc, using last price")
                pred_price = temp_history['Close'].iloc[-1]
            else:
                X_raw = temp_with_indicators[feature_columns].tail(seq_length).values
                
                # Check for NaN
                if np.isnan(X_raw).any():
                    logger.warning(f"    ⚠️  Step {step+1}: NaN in features, using last price")
                    pred_price = temp_history['Close'].iloc[-1]
                else:
                    try:
                        X_scaled = scaler.transform(X_raw)
                        X_lstm = X_scaled.reshape(1, seq_length, -1)
                        X_tree = X_scaled.reshape(1, -1)
                        
                        # Ensemble prediction (WITHOUT harsh clamping via validate_prediction)
                        pred_price = ensemble_predict(X_lstm, X_tree, models, scaler)
                        
                        # Only clip EXTREME outliers, not ±10%
                        pred_price = validate_prediction(pred_price, min_price, max_price)
                        
                    except Exception as e:
                        logger.warning(f"    ⚠️  Step {step+1} prediction error: {e}, using last price")
                        pred_price = temp_history['Close'].iloc[-1]
            
            # Add new row with predicted close
            new_row = pd.DataFrame({
                'Open': [pred_price],
                'High': [pred_price],
                'Low': [pred_price],
                'Close': [pred_price],
                'Volume': [temp_history['Volume'].iloc[-1]]
            })
            temp_history = pd.concat([temp_history, new_row], ignore_index=True)
            
            logger.debug(f"      Step {step+1}: ₹{pred_price:.2f}")
        
        final_pred = temp_history['Close'].iloc[-1]
        change_pct = ((final_pred - current_price) / current_price) * 100
        logger.info(f"    ✅ Results: ₹{final_pred:.2f} ({change_pct:+.2f}%)")
        
        predictions[tf_name] = float(final_pred)
    
    predictions['current_price'] = float(current_price)
    predictions['ensemble_weights'] = ENSEMBLE_WEIGHTS
    
    logger.info("✅ Multi-timeframe ensemble complete!\n")
    return predictions

def predict_multi_timeframe(symbol):
    """Main entry - backward compatible."""
    models = load_ensemble_models()
    scaler = models.pop('scaler')
    feature_columns = joblib.load('models/feature_columns.pkl')
    
    return predict_multi_timeframe_ensemble(symbol, models, scaler, feature_columns)

if __name__ == "__main__":
    preds = predict_multi_timeframe("RELIANCE.NS")
    logger.info("\nMulti-timeframe Ensemble Predictions:")
    for k, v in preds.items():
        if isinstance(v, float):
            logger.info(f"  {k}: ₹{v:.2f}")
        else:
            logger.info(f"  {k}: {v}")


