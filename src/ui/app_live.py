import streamlit as st
from src.data_providers.yfinance_provider import YFinanceProvider
import pandas as pd

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


#adding a matrix view to get side by side comparison of key metrics 
#across different tickers but not historical earning per quarter

st.subheader("Core Financial Metrics")

core_rows = []

for ticker in selected_tickers:
    m = provider.get_core_metrics(ticker)

    core_rows.append({
        "Ticker": ticker,
        "Price ($)": m.price,
        "Market Cap ($)": m.market_cap,
        "P/E (TTM)": m.pe_ttm,
        "P/E (Forward)": m.pe_forward,
        "Gross Margin": m.gross_margin,
        "Net Income (Last Q)": m.net_income_last_quarter,
        "Net Income (Last 4Q Total)": (
            sum(m.net_income_last_4_quarters)
            if m.net_income_last_4_quarters
            else None
        ),
    })

core_df = (
    pd.DataFrame(core_rows)
    .set_index("Ticker")
)

st.dataframe(
    core_df,
    use_container_width=True,
)

st.divider()
st.subheader("Net Income — Last 4 Quarters")

earnings_rows = []
quarter_labels = ["Q-1 (Most Recent)", "Q-2", "Q-3", "Q-4"]

for ticker in selected_tickers:
    m = provider.get_core_metrics(ticker)

    row = {"Ticker": ticker}

    if m.net_income_last_4_quarters:
        for i, q in enumerate(quarter_labels):
            row[q] = m.net_income_last_4_quarters[i]
    else:
        for q in quarter_labels:
            row[q] = None

    earnings_rows.append(row)

earnings_df = (
    pd.DataFrame(earnings_rows)
    .set_index("Ticker")
)

st.dataframe(
    earnings_df,
    use_container_width=True,
)

#adding trend line for historical earnings

st.subheader("Net Income Trend — Last 4 Quarters")

trend_df = earnings_df.copy()

# reverse columns so time flows left → right
trend_df = trend_df[quarter_labels[::-1]]

st.line_chart(
    trend_df.T,
    use_container_width=True,
)

