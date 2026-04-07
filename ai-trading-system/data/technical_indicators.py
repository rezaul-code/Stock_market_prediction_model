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

def calculate_atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr

def calculate_stochrsi(rsi, window=14):
    stochrsi = (rsi - rsi.rolling(window).min()) / (rsi.rolling(window).max() - rsi.rolling(window).min()) * 100
    return stochrsi

try:
    import pandas_ta as ta
except ImportError:
    ta = None

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Add ALL technical indicators for Hybrid Ensemble Model.
    
    Indicators:
    Trend: EMA9/20/50, SMA50/200
    Momentum: RSI14, StochRSI, MACD/Signal/Hist, Momentum10, ROC10
    Volatility: ATR14, Bollinger Bands/Width
    Volume: Volume, VolMA20, VWAP, OBV
    Market Strength: ADX14, DI+/DI-
    Advanced: Pct_Change, Log_Returns, Roll_Mean20/Std20, Z_Score
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV columns
        
    Returns:
        pd.DataFrame: Enhanced DataFrame
    '''
    df = df.copy()
    
    # Trend Indicators
    ema_spans = [9, 20, 50]
    for span in ema_spans:
        col_name = f'EMA_{span}'
        if ta is not None:
            df[col_name] = ta.ema(df['Close'], length=span)
        else:
            df[col_name] = df['Close'].ewm(span=span, adjust=False).mean()
    
    sma_spans = [50, 200]
    for span in sma_spans:
        col_name = f'SMA_{span}'
        if ta is not None:
            df[col_name] = ta.sma(df['Close'], length=span)
        else:
            df[col_name] = df['Close'].rolling(window=span).mean()
    
    # Momentum Indicators
    # RSI14
    if ta is not None:
        df['RSI_14'] = ta.rsi(df['Close'], length=14)
    else:
        df['RSI_14'] = calculate_rsi(df['Close'], 14)
    
    # StochRSI
    if ta is not None:
        stochrsi = ta.stochrsi(df['Close'], rsi_length=14, length=14, k=3, d=3)
        df['StochRSI'] = stochrsi['STOCHRSIk_14_14_3_3']
    else:
        rsi = calculate_rsi(df['Close'], 14)
        df['StochRSI'] = calculate_stochrsi(rsi, 14)
    
    # MACD
    if ta is not None:
        macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd_df['MACD_12_26_9']
        df['MACD_signal'] = macd_df['MACDs_12_26_9']
        df['MACD_hist'] = macd_df['MACDh_12_26_9']
    else:
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # Momentum & ROC
    if ta is not None:
        df['Momentum_10'] = ta.mom(df['Close'], length=10)
        df['ROC_10'] = ta.roc(df['Close'], length=10)
    else:
        df['Momentum_10'] = df['Close'] - df['Close'].shift(10)
        df['ROC_10'] = df['Close'].pct_change(10) * 100
    
    # Volatility Indicators
    # ATR14
    if ta is not None:
        df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    else:
        df['ATR_14'] = calculate_atr(df['High'], df['Low'], df['Close'], 14)
    
    # Bollinger Bands (20,2)
    if ta is not None:
        bb = ta.bbands(df['Close'], length=20, std=2)
        df['BB_upper'] = bb['BBU_20_2.0']
        df['BB_lower'] = bb['BBL_20_2.0']
        df['BB_middle'] = bb['BBM_20_2.0']
    else:
        bb_middle = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_middle'] = bb_middle
        df['BB_upper'] = bb_middle + (bb_std * 2)
        df['BB_lower'] = bb_middle - (bb_std * 2)
    
    df['Bollinger_Width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
    
    # Volume Indicators
    df['VolMA_20'] = df['Volume'].rolling(20).mean()
    
    # VWAP (simple daily)
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    if ta is not None:
        df['OBV'] = ta.obv(df['Close'], df['Volume'])
    else:
        obv = [0]
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv
    
    # Market Strength
    if ta is not None:
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        df['ADX'] = adx_df['ADX_14']
        df['DI_plus'] = adx_df['DMP_14']
        df['DI_minus'] = adx_df['DMN_14']
    else:
        # Manual ADX (simplified)
        plus_dm = df['High'].diff()
        minus_dm = df['Low'].diff() * -1
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = calculate_atr(df['High'], df['Low'], df['Close'], 14)
        plus_di = 100 * (plus_dm.ewm(14).mean() / tr)
        minus_di = 100 * (minus_dm.ewm(14).mean() / tr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['DI_plus'] = plus_di
        df['DI_minus'] = minus_di
        df['ADX'] = dx.ewm(14).mean()
    
    # Advanced Features
    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Roll_Mean_20'] = df['Close'].rolling(20).mean()
    df['Roll_Std_20'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['Roll_Mean_20']) / df['Roll_Std_20']
    
    return df

def get_feature_columns():
    '''Full feature list excluding OHLCV (use these + OHLCV for total 33)'''
    return [
        'EMA_9', 'EMA_20', 'EMA_50', 'SMA_50', 'SMA_200',
        'RSI_14', 'StochRSI', 'MACD', 'MACD_signal', 'MACD_hist',
        'Momentum_10', 'ROC_10', 'ATR_14', 'BB_upper', 'BB_middle', 
        'BB_lower', 'Bollinger_Width', 'VolMA_20', 'VWAP', 'OBV',
        'ADX', 'DI_plus', 'DI_minus', 'Pct_Change', 'Log_Returns',
        'Roll_Mean_20', 'Roll_Std_20', 'Z_Score'
    ]

