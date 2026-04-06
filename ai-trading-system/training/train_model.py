import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os

def train_model():
    print("Loading data...")
    
    # Load processed dataset
    data_path = 'data/processed_data.csv'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run run_pipeline.py first.")
    
    df = pd.read_csv(data_path)
    
    feature_columns = [
        "Close",
        "RSI_14",
        "EMA_20",
        "SMA_50",
        "Volume"
    ]
    
    # Assuming the dataset has 'Close' price as target and previous prices/features
    # For LSTM, create sequences (using last 60 days to predict next day as example)
    def create_sequences(X_data, y_data, seq_length=60):
        X, y = [], []
        for i in range(seq_length, len(X_data)):
            X.append(X_data[i-seq_length:i, :])  # All features
            y.append(y_data[i])  # Target
        return np.array(X), np.array(y)
    
    # Load features and target
    if 'Target' not in df.columns:
        raise ValueError("Processed data must have 'Target' column. Run run_pipeline.py.")
    
    X_raw = df[feature_columns].values
    y = df['Target'].values
    
    # Scale features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X_raw)
    
    # Scale targets using same scaler (Close is first column)
    y_dummy = np.hstack((y.reshape(-1, 1), np.zeros((len(y), 4))))
    y_scaled = scaler.transform(y_dummy)[:, 0]
    
# Create sequences
    X, y_scaled = create_sequences(X_scaled, y_scaled)
    
    # Split dataset: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(X, y_scaled, test_size=0.2, random_state=42, shuffle=False)
    
    # Fix split for scaled y
    y_test_raw_full = scaler.inverse_transform(np.hstack((y_test.reshape(-1,1), np.zeros((len(y_test),4)))))[:,0]  # for eval already done
    
    # Reshape for LSTM [samples, timesteps, features]
    n_features = 5
    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], n_features))
    X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], n_features))
    
    print("Training model...")
    
    # Create LSTM Model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], n_features)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    
    # Compile model
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    # Train model
    history = model.fit(
        X_train, y_train,
        epochs=20,
        batch_size=32,
        validation_data=(X_test, y_test),
        verbose=1
    )
    
    # Evaluate model
    print("Evaluating model...")
    test_preds_scaled = model.predict(X_test, verbose=0)
    test_preds_dummy = np.hstack((test_preds_scaled, np.zeros((len(test_preds_scaled), 4))))
    test_preds = scaler.inverse_transform(test_preds_dummy)[:, 0]
    
    y_test_dummy = np.hstack((y_test.reshape(-1, 1), np.zeros((len(y_test), 4))))
    y_test_raw = scaler.inverse_transform(y_test_dummy)[:, 0]
    
    mse = mean_squared_error(y_test_raw, test_preds)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test_raw, test_preds)
    
    print("Model Accuracy Report")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MSE: {mse:.2f}")
    
    print("Saving model...")
    
    # Ensure models directory exists
    os.makedirs('models', exist_ok=True)
    
    # Save model
    model.save('models/lstm_model.h5')
    
    # Save scaler
    joblib.dump(scaler, 'models/scaler.pkl')
    
    print("Training completed")
    
    return model, history, scaler

if __name__ == "__main__":
    model, history, scaler = train_model()

