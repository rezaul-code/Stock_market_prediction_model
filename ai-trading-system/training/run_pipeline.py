import os
import sys
import pandas as pd
import joblib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.stock_data import get_stock_data
from data.technical_indicators import add_indicators
from training.prepare_data import prepare_data
from config.assets import TOP_25_STOCKS

def run_pipeline(symbols=None):
    """
    Fetch and prepare data for multiple stocks (default: TOP_25_STOCKS).
    Combines all data for unified model training.
    """
    if symbols is None:
        symbols = TOP_25_STOCKS
    
    print(f"🚀 Hybrid Ensemble Data Pipeline for {len(symbols)} Stocks...")
    print("=" * 60)
    
    all_data = []
    successful_symbols = []
    
    for symbol in symbols:
        try:
            print(f"📊 Processing {symbol}...")
            
            # Fetch raw stock data (2y for indicators)
            df = get_stock_data(symbol, period="2y")
            
            # Add ALL technical indicators
            df = add_indicators(df)
            
            # Add symbol column for tracking
            df['Symbol'] = symbol
            
            all_data.append(df)
            successful_symbols.append(symbol)
            print(f"  ✓ {symbol}: {len(df)} rows")
            
        except Exception as e:
            print(f"  ✗ {symbol}: {str(e)}")
    
    if not all_data:
        raise ValueError("❌ No data fetched for any symbols!")
    
    # Combine all data
    print(f"\n✅ Fetched data for {len(successful_symbols)} symbols")
    df_combined = pd.concat(all_data, ignore_index=True)
    print(f"Total rows: {len(df_combined)}")
    
    # Prepare FULL dataset using prepare_data
    print("\n3. Preparing training dataset...")
    X, y, scaler, feature_columns = prepare_data(df_combined)
    
    # Create processed_df with all columns (features + Target + Date + Symbol)
    df_prepared = pd.DataFrame(X, columns=feature_columns)
    df_prepared['Target'] = y.values
    
    # Add date and symbol if available
    if 'Date' in df_combined.columns:
        date_series = df_combined['Date'].iloc[len(df_combined) - len(df_prepared):].reset_index(drop=True)
        df_prepared['Date'] = date_series
    
    if 'Symbol' in df_combined.columns:
        symbol_series = df_combined['Symbol'].iloc[len(df_combined) - len(df_prepared):].reset_index(drop=True)
        df_prepared['Symbol'] = symbol_series
    
    # Sort by date
    if 'Date' in df_prepared.columns:
        df_prepared = df_prepared.sort_values('Date').reset_index(drop=True)
    else:
        df_prepared = df_prepared.sort_index().reset_index(drop=True)
    
    # Save
    os.makedirs('data', exist_ok=True)
    data_path = 'data/processed_data.csv'
    df_prepared.to_csv(data_path, index=False)
    
    print(f"\n✅ Processed data saved: {data_path}")
    print(f"Shape: {df_prepared.shape}")
    print(f"Features ({len(feature_columns)}): {feature_columns[:5]}...")
    print(f"Symbols: {successful_symbols[:5]}...")
    print("\nDataset Statistics:")
    print(f"  Rows: {len(df_prepared)}")
    print(f"  Date range: {df_prepared.get('Date', pd.Series(['N/A'])).iloc[0]} to {df_prepared.get('Date', pd.Series(['N/A'])).iloc[-1]}")
    print(f"  Target range: {df_prepared['Target'].min():.2f} to {df_prepared['Target'].max():.2f}")
    
    # Save scaler and features
    joblib.dump(scaler, 'models/scaler.pkl')  # Save to models folder
    joblib.dump(feature_columns, 'models/feature_columns.pkl')
    
    return df_prepared, scaler, feature_columns

if __name__ == "__main__":
    run_pipeline()

