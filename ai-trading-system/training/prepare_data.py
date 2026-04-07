import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


def prepare_data(df):
    """
    Prepare training data from stock DataFrame

    Parameters:
    df (pd.DataFrame): Input dataframe with technical indicators

    Returns:
    X : Features
    y : Target
    scaler : Fitted scaler for future predictions
    """

    # Remove NaN values
    df = df.dropna().copy()

    # Create target (Next day close price)
    df["Target"] = df["Close"].shift(-1)

    # Drop last row (NaN target)
    df = df.dropna()

    # Feature columns - UPGRADED for better accuracy
    feature_columns = [
        "Close",
        "RSI_14",
        "EMA_20",
        "SMA_50",
        "Volume",
        "MACD",
        "ATR",
        "Bollinger_Width"
    ]

    # Features and target
    X = df[feature_columns]
    y = df["Target"]

    # Normalize features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Convert back to dataframe
    X = pd.DataFrame(
        X_scaled,
        columns=feature_columns,
        index=X.index
    )

    return X, y, scaler