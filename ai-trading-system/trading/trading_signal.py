import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from prediction.predict import predict_next_price, predict_multi_timeframe


def generate_default_signal():
    """
    Generate trading signal using default RELIANCE dataset
    """
    try:
        print("Fetching latest price...")

        data_path = "data/processed_data.csv"

        if not os.path.exists(data_path):
            raise FileNotFoundError(
                f"Processed data not found at {data_path}. Please run preprocessing first."
            )

        df = pd.read_csv(data_path)

        if df.empty or "Close" not in df.columns:
            raise ValueError("Invalid dataset. 'Close' column missing.")

        current_price = float(df["Close"].iloc[-1])

        print(f"Current price: {current_price:.2f}")

        predicted_price = predict_next_price()

        return generate_signal(current_price, predicted_price)

    except Exception as e:
        print(f"Error generating default signal: {str(e)}")
        raise


def generate_signal(current_price, predicted_price):
    """
    Generate trading signal based on price comparison
    """

    # Trading logic
    if predicted_price > current_price * 1.005:
        signal = "BUY"
    elif predicted_price < current_price * 0.995:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = min(
        float(abs((predicted_price - current_price) / current_price) * 100), 50
    )

    return {
        "current_price": current_price,
        "predicted_price": predicted_price,
        "signal": signal,
        "confidence": f"{confidence:.2f}%",
        "confidence_float": confidence,
    }


def generate_multi_signal(predictions):
    """
    Generate multi timeframe trading signals
    """

    current = predictions["current_price"]

    signals = {}

    for timeframe in ["tomorrow", "weekly", "monthly", "quarterly"]:
        pred = predictions[timeframe]

        if pred > current * 1.005:
            signal = "BUY"
        elif pred < current * 0.995:
            signal = "SELL"
        else:
            signal = "HOLD"

        confidence = min(abs((pred - current) / current) * 100, 50)

        signals[f"{timeframe}_signal"] = signal
        signals[f"{timeframe}_confidence"] = f"{confidence:.2f}%"
        signals[f"{timeframe}_confidence_float"] = confidence

    return signals


if __name__ == "__main__":

    print("Testing Trading Signal...\n")

    signal_data = generate_default_signal()

    print(f"Trading Signal: {signal_data['signal']}")
    print(f"Current Price: {signal_data['current_price']:.2f}")
    print(f"Predicted Price: {signal_data['predicted_price']:.2f}")
    print(f"Confidence: {signal_data['confidence']}")