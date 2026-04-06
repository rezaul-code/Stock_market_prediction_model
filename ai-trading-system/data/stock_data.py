import yfinance as yf
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from technical_indicators import add_indicators

def get_stock_data(symbol="RELIANCE.NS"):

    print(f"Fetching data for {symbol}...")

    df = yf.download(
        symbol,
        period="2y",
        interval="1d"
    )

    print("Data fetched successfully")

    return df


if __name__ == "__main__":

    data = get_stock_data("RELIANCE.NS")
    data = add_indicators(data)
    print(data.tail())
