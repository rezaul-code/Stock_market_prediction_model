import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(span=window, adjust=False).mean()
    avg_loss = loss.ewm(span=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # RSI
    df['RSI_14'] = calculate_rsi(df['Close'], 14)
    
    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    
    # EMA20, SMA50
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # ATR (Average True Range)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()
    
    # Bollinger Bands & Width
    bb_period = 20
    df['BB_middle'] = df['Close'].rolling(bb_period).mean()
    bb_std = df['Close'].rolling(bb_period).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    df['Bollinger_Width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle'] * 100
    
    # Drop NaNs from all indicators
    df = df.dropna()
    return df

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

