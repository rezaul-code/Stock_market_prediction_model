import yfinance as yf
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from technical_indicators import add_indicators

def get_stock_data(symbol="RELIANCE.NS", period="2y"):
    print(f"Fetching data for {symbol}...")

    df = yf.download(symbol, period=period)

    # Fix MultiIndex / ticker issue
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Select required columns
    df = df[['Close', 'Volume']]

    # Reset index
    df.reset_index(inplace=True)

    print("Data fetched successfully")

    return df


if __name__ == "__main__":

    data = get_stock_data("RELIANCE.NS")
    data = add_indicators(data)
    print(data.tail())
