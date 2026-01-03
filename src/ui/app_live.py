import streamlit as st
from src.data_providers.yfinance_provider import YFinanceProvider

# --- Provider setup ---
provider = YFinanceProvider()

# --- UI ---
st.title("Stock Tracker - Live Metrics")


# Multiple tickers
available_tickers = [
    "AAPL",
    "NVDA",
    "TXN",
    "STM",
    "NXPI",
    "IFX.DE",
    "RACE",
]


selected_tickers = st.multiselect(
    "Select up to 10 tickers:",
    options=available_tickers,
    default=["NVDA"],
    max_selections=10,
)

if not selected_tickers:
    st.info("Select at least one ticker.")
    st.stop()

for ticker in selected_tickers:
    metrics = provider.get_core_metrics(ticker)

    st.divider()
    st.header(ticker)

    col1, col2, col3 = st.columns(3)

    col1.metric("Price", f"${metrics.price:,.2f}" if metrics.price else "N/A")
    col1.metric("Market Cap", f"${metrics.market_cap:,.0f}" if metrics.market_cap else "N/A")

    col2.metric("P/E TTM", f"{metrics.pe_ttm:.2f}" if metrics.pe_ttm else "N/A")
    col2.metric("P/E Forward", f"{metrics.pe_forward:.2f}" if metrics.pe_forward else "N/A")

    col3.metric("Gross Margin", f"{metrics.gross_margin:.2%}" if metrics.gross_margin else "N/A")
    col3.metric(
        "Net Income (Last Q)",
        f"${metrics.net_income_last_quarter:,.0f}"
        if metrics.net_income_last_quarter
        else "N/A",
    )

    st.subheader("Net Income – Last 4 Quarters")
    if metrics.net_income_last_4_quarters:
        for i, value in enumerate(metrics.net_income_last_4_quarters, 1):
            st.write(f"Q-{i}: ${value:,.0f}")
    else:
        st.write("Data not available")

