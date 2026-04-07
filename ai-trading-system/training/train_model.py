import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import tensorflow as tf
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
import joblib
import json
import os
from training.prepare_data import prepare_data, create_lstm_sequences

def train_ensemble_models():
    print("Hybrid Ensemble Training Pipeline")
    print("=" * 50)
    
    # Load & prepare data
    data_path = 'data/processed_data.csv'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Run 'python training/run_pipeline.py' first to generate {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"Loaded data shape: {df.shape}")
    
    # Prepare full features
    X, y, scaler, feature_columns = prepare_data(df)
    print(f"Features: {len(feature_columns)}")
    
    # LSTM sequences (3D)
    seq_length = 60
    X_lstm, y_lstm = create_lstm_sequences(X, y, seq_length)
    
    # Tree models use flattened sequences (2D)
    X_flat = X_lstm.reshape(X_lstm.shape[0], -1)  # samples x (seq * features)
    y_tree = y_lstm
    
    # Split (time-series aware)
    split_idx = int(0.8 * len(X_lstm))
    X_lstm_train, X_lstm_test = X_lstm[:split_idx], X_lstm[split_idx:]
    y_lstm_train, y_lstm_test = y_lstm[:split_idx], y_lstm[split_idx:]
    
    X_flat_train, X_flat_test = X_flat[:split_idx], X_flat[split_idx:]
    y_tree_train, y_tree_test = y_tree[:split_idx], y_tree[split_idx:]
    
    n_features = X_lstm.shape[2]
    print(f"LSTM train/test: {X_lstm_train.shape}/{X_lstm_test.shape}")
    print(f"Tree models input: {X_flat_train.shape}")
    
    # 1. Train LSTM
    print("\n1. Training LSTM...")
    model_lstm = tf.keras.Sequential([
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(50, return_sequences=True), input_shape=(seq_length, n_features)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(50, return_sequences=True),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(50),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(25, activation='relu'),
        tf.keras.layers.Dense(1)
    ])
    model_lstm.compile(optimizer='adam', loss='mse')
    
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5)
    ]
    
    history = model_lstm.fit(
        X_lstm_train, y_lstm_train,
        epochs=100, batch_size=32,
        validation_data=(X_lstm_test, y_lstm_test),
        callbacks=callbacks, verbose=1
    )
    
    # 2. Train XGBoost
    print("\n2. Training XGBoost...")
    model_xgb = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        random_state=42, n_jobs=-1
    )
    model_xgb.fit(X_flat_train, y_tree_train)
    
    # 3. Train RandomForest
    print("\n3. Training RandomForest...")
    model_rf = RandomForestRegressor(
        n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
    )
    model_rf.fit(X_flat_train, y_tree_train)
    
    # 4. Evaluate ALL models
    print("\n4. Evaluating models...")
    
    # Helper to unscale predictions (CRITICAL: Close is at INDEX 3, not 0)
    # Order: [Open=0, High=1, Low=2, Close=3, Volume=4, ...indicators...]
    def unscale_pred(pred_scaled, scaler, close_idx=3):
        dummy = np.zeros((len(pred_scaled), scaler.n_features_in_))
        dummy[:, close_idx] = pred_scaled.flatten()
        return scaler.inverse_transform(dummy)[:, close_idx]
    
    # LSTM eval
    lstm_pred_scaled = model_lstm.predict(X_lstm_test)
    lstm_pred = unscale_pred(lstm_pred_scaled, scaler)
    y_test_raw = unscale_pred(y_lstm_test, scaler)
    
    # XGB eval
    xgb_pred_scaled = model_xgb.predict(X_flat_test)
    xgb_pred = unscale_pred(xgb_pred_scaled, scaler)
    
    # RF eval
    rf_pred_scaled = model_rf.predict(X_flat_test)
    rf_pred = unscale_pred(rf_pred_scaled, scaler)
    
    # Ensemble: 0.4*LSTM + 0.3*XGB + 0.3*RF
    ensemble_pred = 0.4 * lstm_pred + 0.3 * xgb_pred + 0.3 * rf_pred
    
    # Metrics
    def calc_metrics(y_true, y_pred):
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        accuracy = np.mean(np.sign(y_true[1:] - y_true[:-1]) == np.sign(y_pred[1:] - y_pred[:-1]))  # Direction accuracy
        # Compare predictions with previous actual (numpy compatible)
        y_true_series = pd.Series(y_true.flatten() if isinstance(y_true, np.ndarray) else y_true)
        win_rate = np.mean(y_pred > y_true_series.shift(1).fillna(y_true_series.iloc[0]).values)
        return {'MAE': mae, 'RMSE': rmse, 'Accuracy': accuracy, 'WinRate': win_rate}
    
    metrics = {
        'lstm': calc_metrics(y_test_raw, lstm_pred),
        'xgboost': calc_metrics(y_test_raw, xgb_pred),
        'randomforest': calc_metrics(y_test_raw, rf_pred),
        'ensemble': calc_metrics(y_test_raw, ensemble_pred)
    }
    
    print("\n=== PERFORMANCE COMPARISON ===")
    for name, m in metrics.items():
        print(f"{name.upper()}:")
        print(f"  MAE: {m['MAE']:.4f}, RMSE: {m['RMSE']:.4f}")
        print(f"  Accuracy: {m['Accuracy']:.4f}, WinRate: {m['WinRate']:.4f}")
    
    # Load old metrics for comparison (if exists)
    old_metrics_path = 'models/old_metrics.json'
    if os.path.exists(old_metrics_path):
        with open(old_metrics_path, 'r') as f:
            old_metrics = json.load(f)
        print("\nOLD LSTM:", old_metrics)
    
    # Save new metrics
    os.makedirs('models', exist_ok=True)
    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
    with open(old_metrics_path, 'w') as f:
        json.dump({'old_lstm': metrics['lstm']}, f, indent=4)
    
    # Save models & scaler
    model_lstm.save('models/lstm_model.h5')
    joblib.dump(model_xgb, 'models/xgb_model.pkl')
    joblib.dump(model_rf, 'models/rf_model.pkl')
    joblib.dump(scaler, 'models/scaler.pkl')
    joblib.dump(feature_columns, 'models/feature_columns.pkl')
    
    print("\n✅ All models saved. Ensemble upgrade complete!")
    print("Files: lstm_model.h5, xgb_model.pkl, rf_model.pkl, scaler.pkl, feature_columns.pkl, metrics.json")
    
    return model_lstm, model_xgb, model_rf, scaler, history, metrics

if __name__ == "__main__":
    train_ensemble_models()

