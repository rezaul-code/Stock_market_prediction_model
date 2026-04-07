import pandas as pd

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(span=window, adjust=False).mean()
    avg_loss = loss.ewm(span=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

try:
    import pandas_ta as ta
except ImportError:
    ta = None


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Add technical indicators to the stock dataframe.
    
    Indicators added:
    - RSI (14 periods)
    - MACD (12, 26, 9)
    - EMA (20 periods)
    - SMA (50 periods)
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV columns including 'Close'
        
    Returns:
        pd.DataFrame: DataFrame with added indicator columns
    '''
    
    # RSI (14)
    if ta is not None:
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
    else:
        df['RSI_14'] = calculate_rsi(df['Close'], 14)
    
# MACD (12, 26, 9)
    try:
        macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd_df['MACD_12_26_9']
    except:
        df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
    
    # EMA (20)
    if ta is not None:
        df['EMA_20'] = ta.ema(df['Close'], length=20)
    else:
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
# SMA (50) - Keep for compatibility if needed, but we'll use BB
    if ta is not None:
        df['SMA_50'] = ta.sma(df['Close'], length=50)
    else:
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # ATR (14)
    if ta is not None:
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    else:
        df['ATR'] = calculate_atr(df['High'], df['Low'], df['Close'], 14)
    
    # Bollinger Bands (20, 2 std)
    if ta is not None:
        bb = ta.bbands(df['Close'], length=20, std=2)
        df['BB_upper'] = bb['BBU_20_2.0']
        df['BB_lower'] = bb['BBL_20_2.0']
        df['BB_middle'] = bb['BBM_20_2.0']
    else:
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    
    # Bollinger Width
    df['Bollinger_Width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
    
    return df

def calculate_atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr

