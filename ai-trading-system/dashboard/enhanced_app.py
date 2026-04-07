import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CURRENCY = "₹"

# === ENHANCED IMPORTS - Trading Intelligence Layer ===
from trading.enhanced_signals import generate_signal as generate_enhanced_signal
from trading.enhanced_trade_recommendation import recommend_trade, get_multi_asset_recommendations
from trading.enhanced_portfolio_tracker import get_performance
from trading.enhanced_risk_manager import calculate_risk_levels
from prediction.predict import predict_next_price, predict_asset
from prediction.predict_multi_timeframe import predict_multi_timeframe
from config.assets import TOP_25_STOCKS, TOP_10_CRYPTO
from data.multi_asset_fetcher import fetch_asset_data
from scanner.best_trade_scanner import scan_all

st.set_page_config(page_title="🤖 AI Trading Intelligence Dashboard", layout="wide")

@st.cache_data(ttl=300)
def cached_fetch_data(symbol):
    return fetch_asset_data(symbol).tail(100)

@st.cache_data(ttl=300)
def cached_predict(symbol):
    return predict_asset(symbol)

@st.cache_data(ttl=300)
def cached_predict_multi(symbol):
    return predict_multi_timeframe(symbol)

@st.cache_data(ttl=60)
def cached_enhanced_rec(symbol, capital=100000):
    return recommend_trade(symbol, capital)

st.title("🚀 AI Trading Intelligence System")
st.markdown("**Smart Signals + Risk Management + Performance Tracking**")

# === SIDE BAR CONTROLS ===
st.sidebar.header("🎛️ Trading Controls")
capital = st.sidebar.number_input("Portfolio Capital", value=100000.0, step=10000.0)
risk_pct = st.sidebar.slider("Risk per Trade", 1.0, 2.0, 1.5) / 100
selected_asset = st.sidebar.selectbox("Monitor Asset", TOP_25_STOCKS + TOP_10_CRYPTO)

if st.sidebar.button("🔄 Refresh Intelligence", type="primary"):
    st.cache_data.clear()
    st.rerun()

# === INTELLIGENCE OVERVIEW ===
col1, col2, col3, col4 = st.columns(4)
rec = cached_enhanced_rec(selected_asset, capital)

with col1:
    st.metric("🧠 Signal", rec.get('signal', 'HOLD'), delta=rec.get('confidence', '0%'))

with col2:
    st.metric("📈 Trend", rec.get('trend', 'N/A'), delta=rec.get('prediction_pct', 0))

with col3:
    st.metric("⚠️ Risk Level", rec.get('risk_level', 'MEDIUM'))

with col4:
    st.metric("💰 Position Size", f"{rec.get('position_size', 0):,.0f} shares")

# === TRADING INTELLIGENCE PANEL ===
st.markdown("### 🎯 Trading Intelligence Panel")
col_a, col_b = st.columns([2,1])

with col_a:
    st.success(f"**{rec.get('signal', 'HOLD')}** | Conf: {rec.get('confidence', '0%')} | Trend: {rec.get('trend', 'N/A')}")
    st.info(f"**Entry**: {CURRENCY}{rec.get('entry_price', 0):,.2f} | **SL**: {CURRENCY}{rec.get('stop_loss', 0):,.2f} | **TP**: {CURRENCY}{rec.get('take_profit', 0):,.2f}")
    st.warning(f"R:R {rec.get('risk_reward_ratio', 'N/A')} | Risk: {rec.get('risk_per_trade_pct', 'N/A')}")

with col_b:
    conf_pct = rec.get('confidence_pct', 50)
    conf_color = "🟢" if conf_pct > 70 else "🟡" if conf_pct > 50 else "🔴"
    st.metric(conf_color + " Confidence", f"{conf_pct:.0f}%")
    
    trend_icon = "📈" if rec.get('trend') == 'BULLISH' else "📉" if rec.get('trend') == 'BEARISH' else "➡️"
    st.metric(trend_icon + " Market", rec.get('trend', 'N/A'))

# === RISK MANAGEMENT PANEL ===
st.markdown("### 🛡️ Risk Management")
risk_col1, risk_col2, risk_col3 = st.columns(3)
risk_levels = calculate_risk_levels(selected_asset, capital, risk_pct)

with risk_col1:
    st.metric("Stop Loss", f"{CURRENCY}{risk_levels.get('stop_loss', 0):,.2f}")
with risk_col2:
    st.metric("Take Profit", f"{CURRENCY}{risk_levels.get('take_profit', 0):,.2f}")
with risk_col3:
    st.metric("Position Size", f"{risk_levels.get('position_size', 0):,.0f}")

st.metric("Risk Amount", f"{CURRENCY}{risk_levels.get('risk_amount', 0):,.2f}")
st.metric("Expected Reward", f"{CURRENCY}{risk_levels.get('reward_amount', 0):,.2f}")

# === PERFORMANCE TRACKER ===
st.markdown("### 📊 Performance Tracker")
perf = get_performance()
perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)

with perf_col1:
    st.metric("💰 Total P&L", f"{CURRENCY}{perf.get('total_profit', 0):,.2f}")
with perf_col2:
    st.metric("🏆 Win Rate", perf.get('win_rate', '0%'))
with perf_col3:
    st.metric("📉 Loss Rate", perf.get('loss_rate', '0%'))
with perf_col4:
    st.metric("⭐ Best Asset", perf.get('best_asset', 'N/A'))

# Recent trades table
st.subheader("Recent Trades")
recent = pd.DataFrame(perf.get('recent_trades', []))
if not recent.empty:
    st.dataframe(recent[['symbol', 'signal', 'profit_loss', 'win']], use_container_width=True)

# === MULTI-ASSET INTELLIGENCE ===
st.markdown("### 🌐 Multi-Asset Scanner")
if st.button("🔍 Scan Top Assets"):
    multi_rec = get_multi_asset_recommendations()
    best = multi_rec.get('best_trade', {})
    
    st.success(f"**Top Pick: {best.get('symbol', 'N/A')}** - {best.get('signal', 'HOLD')} ({best.get('confidence', '0%')})")
    
    # Top 5 table
    top_recs = list(multi_rec.get('recommendations', {}).items())[:5]
    df_top = pd.DataFrame([
        {'Asset': k, 'Signal': v.get('signal'), 'Conf': v.get('confidence'), 'Risk': v.get('risk_level')} 
        for k,v in top_recs
    ])
    st.dataframe(df_top, use_container_width=True)

# === CHARTS ===
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    # Price prediction chart
    df_asset = cached_fetch_data(selected_asset)
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df_asset.index, y=df_asset['Close'], name='Close'))
    fig_price.add_hline(y=rec.get('stop_loss'), line_dash="dash", line_color="red", annotation_text="SL")
    fig_price.add_hline(y=rec.get('take_profit'), line_dash="dash", line_color="green", annotation_text="TP")
    fig_price.update_layout(title=f"{selected_asset} Price Action + Levels", template="plotly_dark")
    st.plotly_chart(fig_price, use_container_width=True)

with col_chart2:
    # Performance pie
    if perf.get('total_trades', 0) > 0:
        wins = len([t for t in perf.get('recent_trades', []) if t.get('win')])
        fig_pie = px.pie(values=[wins, perf.get('total_trades', 0)-wins], names=['Wins', 'Losses'])
        fig_pie.update_layout(title="Trade Outcomes")
        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")
st.info("""
**✅ Trading Intelligence Layer COMPLETE**
- Smart Signals: ✅ Ensemble + RSI/MACD/Trend rules  
- Risk Management: ✅ ATR SL/TP + Position Sizing
- Performance Tracking: ✅ Win Rate + History + Best Assets
- Multi-Asset: ✅ Stocks + Crypto scanner

**Run:** `streamlit run dashboard/enhanced_app.py`
**Test Core:** `python -c "from trading.enhanced_trade_recommendation import recommend_trade; print(recommend_trade('TCS.NS'))"`
""")

