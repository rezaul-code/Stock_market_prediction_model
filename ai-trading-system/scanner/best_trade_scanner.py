import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.assets import TOP_25_STOCKS, TOP_10_CRYPTO
from data.multi_asset_fetcher import fetch_asset_data
from prediction.predict import predict_multi_timeframe
from trading.trading_signal import generate_signal

def get_asset_name(symbol):
    """Clean asset name from symbol"""
    return symbol.replace('.NS', '').replace('-USD', '')

def scan_stocks():
    """Scan TOP_25_STOCKS, return ranked df"""
    results = []
    print("Scanning stocks...")
    for sym in TOP_25_STOCKS:
        try:
            df = fetch_asset_data(sym)
            current_price = df['Close'].iloc[-1]
            multi_preds = predict_multi_timeframe(sym)
            weekly_pred = multi_preds['weekly']
            sig_data = generate_signal(current_price, weekly_pred)
            predicted_price = weekly_pred
            results.append({
                'Symbol': sym,
                'Asset': get_asset_name(sym),
                'Type': 'Stock',
                'Current Price': current_price,
                'Predicted Price': predicted_price,
                'Signal': sig_data['signal'],
                'Confidence %': sig_data['confidence'],
                'Confidence': sig_data['confidence_float']
            })
            print(f"✓ {sym}: {sig_data['signal']} ({sig_data['confidence']})")
        except Exception as e:
            print(f"✗ {sym}: {e}")
    df = pd.DataFrame(results)
    return df.sort_values('Confidence', ascending=False)

def scan_crypto():
    """Scan TOP_10_CRYPTO, return ranked df"""
    results = []
    print("Scanning crypto...")
    for sym in TOP_10_CRYPTO:
        try:
            df = fetch_asset_data(sym)
            current_price = df['Close'].iloc[-1]
            multi_preds = predict_multi_timeframe(sym)
            weekly_pred = multi_preds['weekly']
            sig_data = generate_signal(current_price, weekly_pred)
            predicted_price = weekly_pred
            results.append({
                'Symbol': sym,
                'Asset': get_asset_name(sym),
                'Type': 'Crypto',
                'Current Price': current_price,
                'Predicted Price': predicted_price,
                'Signal': sig_data['signal'],
                'Confidence %': sig_data['confidence'],
                'Confidence': sig_data['confidence_float']
            })
            print(f"✓ {sym}: {sig_data['signal']} ({sig_data['confidence']})")
        except Exception as e:
            print(f"✗ {sym}: {e}")
    df = pd.DataFrame(results)
    return df.sort_values('Confidence', ascending=False)

def scan_all():
    """Scan all assets, return combined ranked df"""
    stocks_df = scan_stocks()
    crypto_df = scan_crypto()
    all_df = pd.concat([stocks_df, crypto_df], ignore_index=True)
    all_df = all_df[all_df['Confidence'] > 0.5]
    return all_df.sort_values('Confidence', ascending=False).reset_index(drop=True)

if __name__ == "__main__":
    print("=== Best Trade Scanner ===")
    best_trades = scan_all()
    print("\nTop 5 Best Trades:")
    print(best_trades.head()[['Asset', 'Type', 'Signal', 'Confidence']].round(2))

