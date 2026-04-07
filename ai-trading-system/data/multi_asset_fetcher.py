import yfinance as yf
import pandas as pd
import numpy as np
from data.technical_indicators import add_indicators

def fetch_asset_data(symbol, period="2y"):
    print(f"Fetching data for {symbol}...")
    df = yf.download(symbol, period=period)
    
    # Fix MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Core columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df.reset_index(inplace=True)
    
    # Add indicators
    df = add_indicators(df)
    
    print(f"Data fetched: {len(df)} rows")
    return df

if __name__ == "__main__":
    # Test
    df = fetch_asset_data("RELIANCE.NS")
    print(df.tail())

