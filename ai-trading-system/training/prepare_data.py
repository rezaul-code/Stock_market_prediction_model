import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from data.technical_indicators import get_feature_columns, add_indicators

def prepare_data(df, include_ohlcv=True):
    """
    Prepare training data from stock DataFrame with FULL indicators for Hybrid Ensemble.
    
    Uses CONSISTENT feature ordering:
    - OHLCV first: [Open, High, Low, Close, Volume]
    - Then Technical Indicators (from get_feature_columns)
    
    CRITICAL: This ensures Close is always at index 3 for inverse_transform!
    
    Parameters:
    df (pd.DataFrame): Input dataframe (OHLCV min)
    include_ohlcv (bool): Include OHLCV in features
    
    Returns:
    X : Features (DataFrame)
    y : Target (next Close)
    scaler : Fitted scaler
    feature_columns : list used (consistent ordering)
    """
    
    # Add indicators if not already enhanced
    if 'RSI_14' not in df.columns:
        df = add_indicators(df)
    
    # Remove NaN values (indicators create NaNs)
    df = df.dropna().copy()
    
    # Create target (Next day close price)
    df["Target"] = df["Close"].shift(-1)
    df = df.dropna()
    
    # Define CONSISTENT feature columns (IMPORTANT: OHLCV first for unscaling)
    # Close MUST be at index 3 for proper inverse_transform!
    ohlcv_features = ['Open', 'High', 'Low', 'Close', 'Volume'] if include_ohlcv else []
    indicator_features = get_feature_columns()
    feature_columns = ohlcv_features + indicator_features
    
    # Features and target
    X = df[feature_columns].copy()
    y = df["Target"]
    
    # Normalize features only (target scaled separately in train_model)
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Convert back to dataframe for inspection
    X = pd.DataFrame(
        X_scaled,
        columns=feature_columns,
        index=X.index
    )
    
    print(f"✅ Prepared {len(feature_columns)} features")
    print(f"   • OHLCV (5): {ohlcv_features}")
    print(f"   • Indicators ({len(indicator_features)}): {sorted(indicator_features)}")
    print(f"   • Close column index: 3")
    
    return X, y, scaler, feature_columns

def create_lstm_sequences(X, y, seq_length=60):
    """
    Create 3D sequences for LSTM from 2D features.
    """
    X_seq, y_seq = [], []
    for i in range(seq_length, len(X)):
        X_seq.append(X.iloc[i-seq_length:i].values)
        y_seq.append(y.iloc[i])
    return np.array(X_seq), np.array(y_seq)

if __name__ == "__main__":
    from data.stock_data import get_stock_data
    df = get_stock_data()
    X, y, scaler, cols = prepare_data(df)
    print("Sample prepared:", X.head())

