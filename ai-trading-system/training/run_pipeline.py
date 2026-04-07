import os
import sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.stock_data import get_stock_data
from data.technical_indicators import add_indicators
from training.prepare_data import prepare_data  # Import for feature_cols logic, but we'll replicate save logic

def run_pipeline(symbol='RELIANCE.NS'):
    print(f"STEP 1: Running data pipeline for {symbol}...")
    
    # 1. Fetch raw stock data
    print("Fetching stock data...")
    df = get_stock_data(symbol)
    
    # 2. Add technical indicators
    print("Adding technical indicators...")
    df = add_indicators(df)
    
    # 3. Prepare dataset (replicate prepare_data logic for save)
    print("Preparing dataset...")
    df = df.dropna().copy()
    df['Target'] = df['Close'].shift(-1)
    df = df.dropna()
    
    # Feature columns (match prepare_data and task) - UPGRADED
    feature_columns = [
        'Close',
        'RSI_14',
        'EMA_20',
        'SMA_50',
        'Volume',
        'MACD',
        'ATR',
        'Bollinger_Width'
    ]
    
    # Select relevant columns: Date index + features + Target
    if 'Date' not in df.columns:
        df = df.reset_index()
    
    processed_df = df[feature_columns + ['Target'] + (['Date'] if 'Date' in df.columns else [])]
    
    # Ensure sorted by date
    if 'Date' in processed_df.columns:
        processed_df = processed_df.sort_values('Date').reset_index(drop=True)
    else:
        processed_df = processed_df.sort_index().reset_index(drop=True)
    
    # 4. Save processed data
    os.makedirs('data', exist_ok=True)
    data_path = 'data/processed_data.csv'
    processed_df.to_csv(data_path, index=False)
    print(f"Processed data saved to {data_path}")
    print(f"Shape: {processed_df.shape}")
    print("Features:", feature_columns)
    print("\nSample data:")
    print(processed_df.tail())
    
    return processed_df

if __name__ == "__main__":
    run_pipeline()

