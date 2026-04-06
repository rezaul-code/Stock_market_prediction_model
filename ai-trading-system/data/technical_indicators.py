import pandas as pd
import pandas_ta_classic as ta


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
    df['RSI_14'] = ta.rsi(df['Close'], length=14)
    
    # MACD (12, 26, 9)
    macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
    df = pd.concat([df, macd_df], axis=1)
    
    # EMA (20)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    
    # SMA (50)
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    
    return df

