import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from prediction.predict import predict_next_price
from trading.trading_signal import generate_signal

st.set_page_config(page_title="AI Trading Dashboard", layout="wide")

@st.cache_data
def load_data():
    try:
        return pd.read_csv('data/processed_data.csv')
    except FileNotFoundError:
        st.error("Run `python training/run_pipeline.py` first!")
        st.stop()

data = load_data()
data['Close'] = data['Close'].astype(float)

st.title("🤖 AI Trading System Dashboard")

st.markdown("**Stock Prediction & Trading Signals**")

# Sidebar
st.sidebar.header("Controls")
if st.sidebar.button("🔄 Refresh Prediction & Signal"):
    st.cache_data.clear()
    st.rerun()

# Metrics
col1, col2, col3 = st.columns(3)
current_price = data['Close'].iloc[-1]

with col1:
    st.metric("Current Price", f"${current_price:.2f}")

with col2:
    next_price = float(predict_next_price())
    st.metric("Predicted Next Price", f"${next_price:.2f}", delta=f"{((next_price / current_price - 1)*100):+.1f}%")


try:
    signal_data = generate_signal()
    with col3:
        st.metric("Signal", signal_data['signal'], delta=signal_data['confidence'])
        
    st.success(f"**Trading Signal: {signal_data['signal']}** (Confidence: {signal_data['confidence']})")
except:
    st.warning("Run `python training/train_model.py` first!")

# Charts
st.subheader("📈 Price History (Last 100 days)")
fig = px.line(data.tail(100), y='Close', title="Actual Close Price")
fig.add_hline(y=next_price, line_dash="dash", line_color="green", annotation_text="Predicted Next")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📊 Feature Overview (Latest)")
latest = data.iloc[-1]
st.bar_chart({
    'Close': latest['Close'],
    'RSI_14': latest['RSI_14'],
    'EMA_20': latest['EMA_20'],
    'SMA_50': latest['SMA_50'],
    'Volume': latest['Volume'] / 1e6  # Scale for viz
})

st.info("💡 **To run:** `streamlit run dashboard/app.py`")

