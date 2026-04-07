import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
# from trading.smart_signals import generate_signal, generate_multi_signal  # generate_signal is local, multi_signal defined below
from trading.risk_manager import get_trade_recommendation
from trading.portfolio_tracker import get_performance


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
    Generate trading signal based on price comparison.
    
    Args:
        current_price: Current market price
        predicted_price: Model's predicted price
    
    Returns:
        Trading signal dict with signal, confidence, etc.
    """
    
    # Calculate prediction change
    price_change = ((predicted_price - current_price) / current_price) * 100
    
    # Trading logic - now with relaxed thresholds since we have real models
    if price_change > 1.0:  # >1% up move
        signal = "BUY"
    elif price_change < -1.0:  # >1% down move
        signal = "SELL"
    else:
        signal = "HOLD"
    
    # Confidence based on prediction magnitude AND conviction
    # Higher % change = higher conviction (model is more confident)
    confidence = min(abs(price_change) * 2, 95)  # Cap at 95% for humility
    
    return {
        "current_price": current_price,
        "predicted_price": predicted_price,
        "signal": signal,
        "confidence": f"{confidence:.2f}%",
        "confidence_float": confidence,
        "change_pct": price_change,
    }


def generate_multi_signal(predictions):
    """
    Generate multi timeframe trading signals with proper confidence.
    
    Args:
        predictions: Dict with predictions for different timeframes
    
    Returns:
        Dict with signals and confidence for each timeframe
    """
    current = predictions["current_price"]
    signals = {}

    for timeframe in ["tomorrow", "weekly", "monthly", "quarterly"]:
        pred = predictions[timeframe]
        price_change = ((pred - current) / current) * 100

        # Trading logic with relaxed thresholds
        if price_change > 1.0:
            signal = "BUY"
        elif price_change < -1.0:
            signal = "SELL"
        else:
            signal = "HOLD"

        # Confidence scales with magnitude of predicted move
        confidence = min(abs(price_change) * 1.5, 95)  # Cap at 95%

        signals[f"{timeframe}_signal"] = signal
        signals[f"{timeframe}_confidence"] = f"{confidence:.2f}%"
        signals[f"{timeframe}_confidence_float"] = confidence
        signals[f"{timeframe}_change_pct"] = price_change

    return signals


if __name__ == "__main__":

    print("Testing Trading Signal...\n")

    signal_data = generate_default_signal()

    print(f"Trading Signal: {signal_data['signal']}")
    print(f"Current Price: {signal_data['current_price']:.2f}")
    print(f"Predicted Price: {signal_data['predicted_price']:.2f}")
    print(f"Confidence: {signal_data['confidence']}")