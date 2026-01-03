import streamlit as st
from src.data_providers.yfinance_provider import YFinanceProvider

# --- Provider setup ---
provider = YFinanceProvider()

# --- UI ---
st.title("Stock Tracker - Live Metrics")

# Single ticker selection for MVP
ticker_symbol = st.selectbox(
    "Select a ticker:",
    ["AAPL", "NVDA", "TXN", "STM", "NXPI", "IFX.DE", "RACE"]  # NASDAQ 100 peers + Ferrari
)

# Fetch metrics
metrics = provider.get_core_metrics(ticker_symbol)

# Display core metrics
st.header(f"{ticker_symbol} - Core Metrics")
st.write(f"**Price:** ${metrics.price:,.2f}" if metrics.price else "Price: N/A")
st.write(f"**Market Cap:** ${metrics.market_cap:,.0f}" if metrics.market_cap else "Market Cap: N/A")
st.write(f"**P/E TTM:** {metrics.pe_ttm:.2f}" if metrics.pe_ttm else "P/E TTM: N/A")
st.write(f"**P/E Forward:** {metrics.pe_forward:.2f}" if metrics.pe_forward else "P/E Forward: N/A")
st.write(f"**Gross Margin:** {metrics.gross_margin:.2%}" if metrics.gross_margin else "Gross Margin: N/A")
st.write(f"**Net Income (last quarter):** ${metrics.net_income_last_quarter:,.0f}" if metrics.net_income_last_quarter else "Net Income: N/A")

st.subheader("Net Income - Last 4 Quarters")
if metrics.net_income_last_4_quarters:
    for i, val in enumerate(metrics.net_income_last_4_quarters, 1):
        st.write(f"Q-{i}: ${val:,.0f}")
else:
    st.write("Data not available")
