import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CURRENCY = "₹"

from prediction.predict import predict_next_price, predict_asset
from prediction.predict_multi_timeframe import predict_multi_timeframe
from trading.trading_signal import generate_signal, generate_multi_signal
from trading.profit_calculator import calculate_profit
from config.assets import TOP_25_STOCKS, TOP_10_CRYPTO
from data.multi_asset_fetcher import fetch_asset_data
from scanner.best_trade_scanner import scan_all

st.set_page_config(page_title="AI Trading Dashboard", layout="wide")

# Cache functions with longer TTL for better performance
@st.cache_data(ttl=300)
def cached_fetch_data(symbol):
    df = fetch_asset_data(symbol)
    return df.tail(100)

@st.cache_data(ttl=300)
def cached_predict(symbol):
    return predict_asset(symbol)

@st.cache_data(ttl=300)
def cached_predict_multi(symbol):
    return predict_multi_timeframe(symbol)

@st.cache_data(ttl=120)
def cached_scan():
    return scan_all()

# Sidebar Controls
st.sidebar.header("🎮 Controls")

if st.sidebar.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("🔍 Re-scan Markets"):
    st.cache_data.clear()
    st.rerun()

st.title("🤖 AI Trading System Dashboard")
st.markdown("*Multi-Asset Trading Predictions with Ensemble ML*")

# Main Dashboard
st.markdown("## 🌟 Multi-Asset Trading Dashboard")

tab1, tab2, tab3 = st.tabs(["📈 Stocks", "₿ Crypto", "🎯 Best Trades"])

# ==========================================
# TAB 1: STOCKS
# ==========================================
with tab1:
    st.header("📈 Stock Analysis")
    
    selected_stock = st.selectbox("Select Stock", TOP_25_STOCKS, key="stock_select")
    
    if selected_stock:
        try:
            # Fetch data
            df_stock = cached_fetch_data(selected_stock)
            current_price_stock = df_stock['Close'].iloc[-1]
            
            # Predict
            pred_price_stock = cached_predict(selected_stock)
            sig_stock = generate_signal(current_price_stock, pred_price_stock)
            
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Current Price", f"{CURRENCY}{current_price_stock:.2f}")
            
            with col2:
                st.metric(
                    "🎯 Predicted Price",
                    f"{CURRENCY}{pred_price_stock:.2f}",
                    delta=f"{((pred_price_stock / current_price_stock - 1)*100):+.1f}%"
                )
            
            with col3:
                color = "🟢" if sig_stock['signal'] == "BUY" else "🔴" if sig_stock['signal'] == "SELL" else "🟡"
                st.metric(f"{color} Signal", sig_stock['signal'], delta=sig_stock['confidence'])
            
            st.success(f"**Signal: {sig_stock['signal']}** (Confidence: {sig_stock['confidence']})")
            
            st.markdown("---")
            
            # Multi-timeframe predictions
            st.subheader("📊 Multi-Timeframe Predictions")
            
            multi_preds = cached_predict_multi(selected_stock)
            multi_sig = generate_multi_signal(multi_preds)
            
            capital = st.number_input(
                f"Capital ({CURRENCY})",
                value=10000.0,
                min_value=1000.0,
                key="capital_stock"
            )
            
            st.markdown("**Predictions by Timeframe:**")
            
            timeframes = [
                ('tomorrow', 'Tomorrow (1 day)'),
                ('weekly', 'Weekly (5 days)'),
                ('monthly', 'Monthly (20 days)'),
                ('quarterly', 'Quarterly (60 days)')
            ]
            
            # Create columns for each timeframe
            for tf_key, tf_label in timeframes:
                col1, col2, col3, col4 = st.columns(4)
                
                pred = multi_preds[tf_key]
                current = multi_preds['current_price']
                pct = ((pred - current) / current) * 100
                profit_info = calculate_profit(current, pred, capital)
                
                with col1:
                    st.metric(
                        tf_label,
                        f"{CURRENCY}{pred:.2f}",
                        delta=f"{pct:+.1f}%"
                    )
                
                with col2:
                    signal = multi_sig[f'{tf_key}_signal']
                    color = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
                    st.metric(f"{color} Signal", signal)
                
                with col3:
                    st.metric(
                        "Expected Profit",
                        f"{CURRENCY}{profit_info['profit']:.0f}",
                        delta=f"{profit_info['percent']:+.1f}%"
                    )
                
                with col4:
                    confidence = multi_sig[f'{tf_key}_confidence']
                    st.text(f"Confidence:\n{confidence}")
            
            st.markdown("---")
            
            # Graph
            st.subheader("📉 Historical vs Prediction")
            
            fig_stock = go.Figure()
            
            # Historical data
            fig_stock.add_trace(
                go.Scatter(
                    x=df_stock.index,
                    y=df_stock['Close'],
                    mode='lines',
                    name='Historical',
                    line=dict(color='#4FC3F7', width=2)
                )
            )
            
            # Prediction line
            pred_x = [df_stock.index[-1], df_stock.index[-1] + 1]
            pred_y = [df_stock['Close'].iloc[-1], pred_price_stock]
            
            fig_stock.add_trace(
                go.Scatter(
                    x=pred_x,
                    y=pred_y,
                    mode='lines+markers',
                    name='Tomorrow Prediction',
                    line=dict(color='#00E676', dash='dash', width=3),
                    marker=dict(size=10)
                )
            )
            
            fig_stock.update_layout(
                title=f"{selected_stock} - Price Analysis",
                xaxis_title="Days",
                yaxis_title=f"Price ({CURRENCY})",
                template="plotly_dark",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_stock, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ==========================================
# TAB 2: CRYPTO
# ==========================================
with tab2:
    st.header("₿ Cryptocurrency Analysis")
    
    selected_crypto = st.selectbox("Select Crypto", TOP_10_CRYPTO, key="crypto_select")
    
    if selected_crypto:
        try:
            # Fetch data
            df_crypto = cached_fetch_data(selected_crypto)
            current_price_crypto = df_crypto['Close'].iloc[-1]
            
            # Predict
            pred_price_crypto = cached_predict(selected_crypto)
            sig_crypto = generate_signal(current_price_crypto, pred_price_crypto)
            
            # Display key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💹 Current Price", f"${current_price_crypto:.2f}")
            
            with col2:
                st.metric(
                    "🎯 Predicted Price",
                    f"${pred_price_crypto:.2f}",
                    delta=f"{((pred_price_crypto / current_price_crypto - 1)*100):+.1f}%"
                )
            
            with col3:
                color = "🟢" if sig_crypto['signal'] == "BUY" else "🔴" if sig_crypto['signal'] == "SELL" else "🟡"
                st.metric(f"{color} Signal", sig_crypto['signal'], delta=sig_crypto['confidence'])
            
            st.info(f"**Signal: {sig_crypto['signal']}** (Confidence: {sig_crypto['confidence']})")
            
            st.markdown("---")
            
            # Multi-timeframe predictions for crypto
            st.subheader("📊 Multi-Timeframe Predictions")
            
            multi_preds_crypto = cached_predict_multi(selected_crypto)
            multi_sig_crypto = generate_multi_signal(multi_preds_crypto)
            
            capital = st.number_input(
                "$USD Capital",
                value=10000.0,
                min_value=1000.0,
                key="capital_crypto"
            )
            
            st.markdown("**Predictions by Timeframe:**")
            
            for tf_key, tf_label in timeframes:
                col1, col2, col3, col4 = st.columns(4)
                
                pred = multi_preds_crypto[tf_key]
                current = multi_preds_crypto['current_price']
                pct = ((pred - current) / current) * 100
                profit_info = calculate_profit(current, pred, capital)
                
                with col1:
                    st.metric(
                        tf_label,
                        f"${pred:.2f}",
                        delta=f"{pct:+.1f}%"
                    )
                
                with col2:
                    signal = multi_sig_crypto[f'{tf_key}_signal']
                    color = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
                    st.metric(f"{color} Signal", signal)
                
                with col3:
                    st.metric(
                        "Expected Profit",
                        f"${profit_info['profit']:.0f}",
                        delta=f"{profit_info['percent']:+.1f}%"
                    )
                
                with col4:
                    confidence = multi_sig_crypto[f'{tf_key}_confidence']
                    st.text(f"Confidence:\n{confidence}")
            
            st.markdown("---")
            
            # Graph
            st.subheader("📉 Historical vs Prediction")
            
            fig_crypto = go.Figure()
            
            fig_crypto.add_trace(
                go.Scatter(
                    x=df_crypto.index,
                    y=df_crypto['Close'],
                    mode='lines',
                    name='Historical',
                    line=dict(color='#FFD700', width=2)
                )
            )
            
            pred_x_c = [df_crypto.index[-1], df_crypto.index[-1] + 1]
            pred_y_c = [df_crypto['Close'].iloc[-1], pred_price_crypto]
            
            fig_crypto.add_trace(
                go.Scatter(
                    x=pred_x_c,
                    y=pred_y_c,
                    mode='lines+markers',
                    name='Tomorrow Prediction',
                    line=dict(color='#FF6B6B', dash='dash', width=3),
                    marker=dict(size=10)
                )
            )
            
            fig_crypto.update_layout(
                title=f"{selected_crypto} - Price Analysis",
                xaxis_title="Days",
                yaxis_title="Price (USD)",
                template="plotly_dark",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_crypto, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ==========================================
# TAB 3: BEST TRADES
# ==========================================
with tab3:
    st.header("🎯 Best Trade Opportunities")
    st.markdown("*Scanning all assets for top opportunities...*")
    
    if st.button("🔍 Scan Now", key="scan_button"):
        with st.spinner("🔄 Scanning markets..."):
            try:
                scan_results = cached_scan()
                
                if scan_results.empty:
                    st.warning("⚠️ No trades found! Try refreshing the data.")
                else:
                    # Display statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    buy_signals = len(scan_results[scan_results['Signal'] == 'BUY'])
                    sell_signals = len(scan_results[scan_results['Signal'] == 'SELL'])
                    hold_signals = len(scan_results[scan_results['Signal'] == 'HOLD'])
                    total_profit = scan_results['Profit ₹'].sum()
                    
                    with col1:
                        st.metric("🟢 BUY Signals", buy_signals)
                    with col2:
                        st.metric("🔴 SELL Signals", sell_signals)
                    with col3:
                        st.metric("🟡 HOLD Signals", hold_signals)
                    with col4:
                        st.metric("💰 Total Potential", f"₹{total_profit:.0f}")
                    
                    st.markdown("---")
                    
                    # Top BUY opportunities
                    st.subheader("🟢 Top BUY Opportunities")
                    
                    buy_df = scan_results[scan_results['Signal'] == 'BUY'].head(5)
                    if not buy_df.empty:
                        for idx, row in buy_df.iterrows():
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.write(f"**{row['Asset']}**")
                            with col2:
                                st.write(f"Current: {CURRENCY}{row['Current Price']:.2f}")
                            with col3:
                                st.write(f"Predicted: {CURRENCY}{row['Predicted Price']:.2f}")
                            with col4:
                                profit_text = f"₹{row['Profit ₹']:.0f}" if row['Type'] == 'Stock' else f"${row['Profit ₹']:.0f}"
                                st.write(f"Profit: {profit_text} ({row['Profit %']:+.1f}%)")
                            with col5:
                                st.write(f"Conf: {row['Confidence %']}")
                    else:
                        st.info("No BUY signals at this time")
                    
                    st.markdown("---")
                    
                    # Top SELL opportunities
                    st.subheader("🔴 Top SELL Opportunities")
                    
                    sell_df = scan_results[scan_results['Signal'] == 'SELL'].head(5)
                    if not sell_df.empty:
                        for idx, row in sell_df.iterrows():
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.write(f"**{row['Asset']}**")
                            with col2:
                                st.write(f"Current: {CURRENCY}{row['Current Price']:.2f}")
                            with col3:
                                st.write(f"Predicted: {CURRENCY}{row['Predicted Price']:.2f}")
                            with col4:
                                profit_text = f"₹{row['Profit ₹']:.0f}" if row['Type'] == 'Stock' else f"${row['Profit ₹']:.0f}"
                                st.write(f"Loss: {profit_text} ({row['Profit %']:+.1f}%)")
                            with col5:
                                st.write(f"Conf: {row['Confidence %']}")
                    else:
                        st.info("No SELL signals at this time")
                    
                    st.markdown("---")
                    
                    # Full results table
                    st.subheader("📊 Full Scan Results")
                    
                    display_cols = ['Asset', 'Type', 'Current Price', 'Predicted Price', 'Change %', 'Signal', 'Profit %', 'Confidence %']
                    st.dataframe(scan_results[display_cols], use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Scan error: {str(e)}")
    else:
        st.info("👉 Click 'Scan Now' to find the best trading opportunities")

# Footer
st.markdown("---")
st.info("💡 **To run:** `streamlit run dashboard/app.py`")
st.markdown("🔍 *Updates every 5 minutes | Refresh to get latest predictions*")