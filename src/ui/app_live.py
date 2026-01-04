import streamlit as st
from src.data_providers.yfinance_provider import YFinanceProvider
from src.domain.earnings_momentum import classify_earnings_momentum
from src.domain.position import Position, format_trigger_status
import pandas as pd

# --- Provider setup ---
provider = YFinanceProvider()

# --- Session state for positions ---
if "positions" not in st.session_state:
    st.session_state.positions = {}

# --- UI ---
st.title("Stock Tracker - Live Metrics")


# Multiple tickers
available_tickers = [
    # Big Tech
    "AAPL",
    "GOOGL",  # Alphabet Inc
    "META",   # Meta Platforms
    "TSLA",   # Tesla
    # Semiconductors
    "NVDA",
    "TSM",    # TSMC
    "QCOM",   # Qualcomm
    "MU",     # Micron
    "SNPS",   # Synopsys
    "TXN",
    "STM",
    "NXPI",
    "005930.KS",  # Samsung Electronics (Korea)
    # Quantum Computing
    "RGTI",   # Rigetti Computing
    # Asian Markets
    "1810.HK",  # Xiaomi
    # European
    "IFX.DE",
    # Other
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


# ------------------------
# Matrix 1 — Core Metrics
# ------------------------
#adding a matrix view to get side by side comparison of key metrics 
#across different tickers but not historical earning per quarter

st.subheader("Core Financial Metrics")

core_rows = []

for ticker in selected_tickers:
    m = provider.get_core_metrics(ticker)
    earnings_momentum = classify_earnings_momentum(
        m.net_income_last_4_quarters
    )

    core_rows.append({
        "Ticker": ticker,
        "Price ($)": m.price,
        "Market Cap ($)": m.market_cap,
        "P/E (TTM)": m.pe_ttm,
        "P/E (Forward)": m.pe_forward,
        "Gross Margin": m.gross_margin,
        "Net Income (Last Q)": m.net_income_last_quarter,
        "Earnings Momentum": earnings_momentum,
        })

core_df = (
    pd.DataFrame(core_rows)
    .set_index("Ticker")
)

st.dataframe(
    core_df,
    use_container_width=True,
)



# --------------------------------
# Matrix 2 — Net Income by Quarter
# --------------------------------

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

# --------------------------------
# Position Tracker
# --------------------------------

st.divider()
st.subheader("Position Tracker")
st.caption("Track your positions with entry/exit rules. Configure take-profit and stop-loss thresholds.")

# Default exit rules (configurable)
col_tp, col_sl = st.columns(2)
with col_tp:
    default_take_profit = st.number_input(
        "Default Take Profit %",
        min_value=1.0,
        max_value=100.0,
        value=20.0,
        step=1.0,
        help="Default take-profit threshold for new positions"
    )
with col_sl:
    default_stop_loss = st.number_input(
        "Default Stop Loss %",
        min_value=1.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
        help="Default stop-loss threshold for new positions"
    )

st.markdown("---")

# Position input for each selected ticker
for ticker in selected_tickers:
    metrics = provider.get_core_metrics(ticker)
    current_price = metrics.price

    with st.expander(f"📊 {ticker} - Current: ${current_price:,.2f}" if current_price else f"📊 {ticker} - Price N/A"):
        col1, col2, col3 = st.columns(3)

        with col1:
            entry_price = st.number_input(
                "Entry Price ($)",
                min_value=0.01,
                value=st.session_state.positions.get(ticker, {}).get("entry_price", current_price or 100.0),
                step=0.01,
                key=f"entry_{ticker}",
            )

        with col2:
            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=st.session_state.positions.get(ticker, {}).get("quantity", 0.0),
                step=1.0,
                key=f"qty_{ticker}",
            )

        with col3:
            tp_pct = st.number_input(
                "Take Profit %",
                min_value=1.0,
                max_value=100.0,
                value=st.session_state.positions.get(ticker, {}).get("take_profit_pct", default_take_profit),
                step=1.0,
                key=f"tp_{ticker}",
            )
            sl_pct = st.number_input(
                "Stop Loss %",
                min_value=1.0,
                max_value=100.0,
                value=st.session_state.positions.get(ticker, {}).get("stop_loss_pct", default_stop_loss),
                step=1.0,
                key=f"sl_{ticker}",
            )

        # Save position to session state
        if quantity > 0:
            st.session_state.positions[ticker] = {
                "entry_price": entry_price,
                "quantity": quantity,
                "take_profit_pct": tp_pct,
                "stop_loss_pct": sl_pct,
            }

            # Calculate P&L
            position = Position(
                ticker=ticker,
                entry_price=entry_price,
                quantity=quantity,
                take_profit_pct=tp_pct / 100,
                stop_loss_pct=sl_pct / 100,
            )
            pnl_data = position.calculate_pnl(current_price)

            # Display P&L metrics
            st.markdown("**Position Summary:**")
            pcol1, pcol2, pcol3, pcol4 = st.columns(4)

            with pcol1:
                if pnl_data["unrealized_pnl"] is not None:
                    pnl_color = "green" if pnl_data["unrealized_pnl"] >= 0 else "red"
                    st.metric(
                        "Unrealized P&L",
                        f"${pnl_data['unrealized_pnl']:,.2f}",
                        f"{pnl_data['unrealized_pnl_pct']*100:+.2f}%",
                    )
                else:
                    st.metric("Unrealized P&L", "--")

            with pcol2:
                st.metric(
                    "Take Profit @",
                    f"${pnl_data['take_profit_price']:,.2f}" if pnl_data["take_profit_price"] else "--"
                )

            with pcol3:
                st.metric(
                    "Stop Loss @",
                    f"${pnl_data['stop_loss_price']:,.2f}" if pnl_data["stop_loss_price"] else "--"
                )

            with pcol4:
                trigger_text = format_trigger_status(
                    pnl_data["trigger_status"],
                    pnl_data["trigger_proximity_pct"]
                )
                st.metric("Trigger Status", trigger_text)
        else:
            st.info("Enter quantity > 0 to track this position")

# --------------------------------
# Positions Summary Table
# --------------------------------

if st.session_state.positions:
    st.divider()
    st.subheader("Active Positions Summary")

    position_rows = []
    for ticker, pos_data in st.session_state.positions.items():
        if pos_data["quantity"] > 0:
            metrics = provider.get_core_metrics(ticker)
            current_price = metrics.price

            position = Position(
                ticker=ticker,
                entry_price=pos_data["entry_price"],
                quantity=pos_data["quantity"],
                take_profit_pct=pos_data["take_profit_pct"] / 100,
                stop_loss_pct=pos_data["stop_loss_pct"] / 100,
            )
            pnl_data = position.calculate_pnl(current_price)

            position_rows.append({
                "Ticker": ticker,
                "Entry": f"${pos_data['entry_price']:,.2f}",
                "Current": f"${current_price:,.2f}" if current_price else "--",
                "Qty": pos_data["quantity"],
                "P&L ($)": f"${pnl_data['unrealized_pnl']:,.2f}" if pnl_data["unrealized_pnl"] else "--",
                "P&L (%)": f"{pnl_data['unrealized_pnl_pct']*100:+.2f}%" if pnl_data["unrealized_pnl_pct"] else "--",
                "Status": format_trigger_status(pnl_data["trigger_status"], pnl_data["trigger_proximity_pct"]),
            })

    if position_rows:
        positions_df = pd.DataFrame(position_rows).set_index("Ticker")
        st.dataframe(positions_df, use_container_width=True)

