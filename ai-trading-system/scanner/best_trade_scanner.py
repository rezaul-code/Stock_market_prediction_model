import pandas as pd
import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.assets import TOP_25_STOCKS, TOP_10_CRYPTO
from data.multi_asset_fetcher import fetch_asset_data
from prediction.predict_multi_timeframe import predict_multi_timeframe
from trading.trading_signal import generate_signal
from trading.profit_calculator import calculate_profit

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_asset_name(symbol):
    """Clean asset name from symbol"""
    return symbol.replace('.NS', '').replace('-USD', '')

def scan_stocks():
    """Scan TOP_25_STOCKS, return ranked df"""
    results = []
    logger.info("🔍 Scanning stocks...")
    
    for sym in TOP_25_STOCKS:
        try:
            df = fetch_asset_data(sym)
            current_price = df['Close'].iloc[-1]
            
            # Use weekly prediction for scanning
            multi_preds = predict_multi_timeframe(sym)
            weekly_pred = multi_preds['weekly']
            
            sig_data = generate_signal(current_price, weekly_pred)
            
            profit_info = calculate_profit(current_price, weekly_pred, capital=10000)
            
            change_pct = ((weekly_pred - current_price) / current_price) * 100
            
            results.append({
                'Symbol': sym,
                'Asset': get_asset_name(sym),
                'Type': 'Stock',
                'Current Price': current_price,
                'Predicted Price': weekly_pred,
                'Change %': change_pct,
                'Signal': sig_data['signal'],
                'Confidence %': sig_data['confidence'],
                'Confidence': sig_data['confidence_float'],
                'Profit ₹': profit_info['profit'],
                'Profit %': profit_info['percent']
            })
            logger.info(f"  ✓ {sym}: {sig_data['signal']} (₹{profit_info['profit']:.0f}, {sig_data['confidence']})")
            
        except Exception as e:
            logger.warning(f"  ✗ {sym}: {str(e)}")
    
    if not results:
        logger.warning("No stock results!")
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    # Rank by profit potential, then confidence
    df = df.sort_values('Profit %', key=abs, ascending=False)
    
    return df

def scan_crypto():
    """Scan TOP_10_CRYPTO, return ranked df"""
    results = []
    logger.info("🔍 Scanning crypto...")
    
    for sym in TOP_10_CRYPTO:
        try:
            df = fetch_asset_data(sym)
            current_price = df['Close'].iloc[-1]
            
            multi_preds = predict_multi_timeframe(sym)
            weekly_pred = multi_preds['weekly']
            
            sig_data = generate_signal(current_price, weekly_pred)
            
            profit_info = calculate_profit(current_price, weekly_pred, capital=10000)
            
            change_pct = ((weekly_pred - current_price) / current_price) * 100
            
            results.append({
                'Symbol': sym,
                'Asset': get_asset_name(sym),
                'Type': 'Crypto',
                'Current Price': current_price,
                'Predicted Price': weekly_pred,
                'Change %': change_pct,
                'Signal': sig_data['signal'],
                'Confidence %': sig_data['confidence'],
                'Confidence': sig_data['confidence_float'],
                'Profit ₹': profit_info['profit'],
                'Profit %': profit_info['percent']
            })
            logger.info(f"  ✓ {sym}: {sig_data['signal']} (${profit_info['profit']:.0f}, {sig_data['confidence']})")
            
        except Exception as e:
            logger.warning(f"  ✗ {sym}: {str(e)}")
    
    if not results:
        logger.warning("No crypto results!")
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    df = df.sort_values('Profit %', key=abs, ascending=False)
    
    return df

def scan_all():
    """Scan all assets, return combined ranked df"""
    logger.info("=" * 60)
    logger.info("🚀 BEST TRADE SCANNER")
    logger.info("=" * 60)
    
    stocks_df = scan_stocks()
    crypto_df = scan_crypto()
    
    if stocks_df.empty and crypto_df.empty:
        logger.error("❌ No scan results!")
        return pd.DataFrame()
    
    all_df = pd.concat([stocks_df, crypto_df], ignore_index=True)
    
    # Filter by minimum confidence
    all_df = all_df[all_df['Confidence'] > 0.5]
    
    # Sort by profit potential
    all_df = all_df.sort_values('Profit %', key=abs, ascending=False)
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 TOP BUY OPPORTUNITIES")
    logger.info("=" * 60)
    
    buy_df = all_df[all_df['Signal'] == 'BUY'].head(5)
    if not buy_df.empty:
        for idx, row in buy_df.iterrows():
            logger.info(
                f"{row['Asset']:8} | Current: ₹{row['Current Price']:8.2f} | "
                f"Pred: ₹{row['Predicted Price']:8.2f} | "
                f"Profit: ₹{row['Profit ₹']:7.0f} ({row['Profit %']:+.1f}%) | "
                f"Conf: {row['Confidence %']}"
            )
    else:
        logger.info("No strong BUY signals")
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 TOP SELL OPPORTUNITIES")
    logger.info("=" * 60)
    
    sell_df = all_df[all_df['Signal'] == 'SELL'].head(5)
    if not sell_df.empty:
        for idx, row in sell_df.iterrows():
            logger.info(
                f"{row['Asset']:8} | Current: ₹{row['Current Price']:8.2f} | "
                f"Pred: ₹{row['Predicted Price']:8.2f} | "
                f"Loss: ₹{row['Profit ₹']:7.0f} ({row['Profit %']:+.1f}%) | "
                f"Conf: {row['Confidence %']}"
            )
    else:
        logger.info("No strong SELL signals")
    
    return all_df.reset_index(drop=True)

if __name__ == "__main__":
    best_trades = scan_all()
    if not best_trades.empty:
        logger.info("\n✅ Scan complete!")
    else:
        logger.error("\n❌ Scan failed!")

