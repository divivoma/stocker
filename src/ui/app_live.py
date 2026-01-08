"""
Stock Tracker - Professional Comparison UI
Following PRD Chapter 7 UI Requirements:
- Comparison-first matrix view (no single-ticker cards)
- Dense, structured data presentation
- Stable layout across ticker changes
- Descriptive only (no recommendations)
"""

import streamlit as st
import pandas as pd
#import sys
#from pathlib import Path


# Add project root to path for imports
#project_root = Path(__file__).parent.parent.parent
#if str(project_root) not in sys.path:
#    sys.path.insert(0, str(project_root))

from src.data_providers.cached_provider import CachedDataProvider
from src.domain.earnings_momentum import classify_earnings_momentum
from src.domain.position import Position, format_trigger_status

# --- Page Configuration ---
st.set_page_config(
    page_title="Stock Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Custom CSS for professional look ---
st.markdown("""
<style>
    /* Tighter spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Header styling */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #1f2937 !important;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.5rem;
    }
    
    h2 {
        font-size: 1.2rem !important;
        font-weight: 500 !important;
        color: #374151 !important;
        margin-top: 1.5rem !important;
    }
    
    /* Matrix tables */
    .dataframe {
        font-size: 0.85rem !important;
    }
    
    /* Metric cards in sidebar */
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 500;
    }
    
    /* Positive/negative colors for streaks */
    .streak-up { color: #10b981; font-weight: 600; }
    .streak-down { color: #ef4444; font-weight: 600; }
    
    /* Dense info text */
    .info-dense {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: -0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Provider setup ---
provider = CachedDataProvider()

# --- Session state ---
if "positions" not in st.session_state:
    st.session_state.positions = {}

# --- Favorites Management (Client-side persistence via URL query params) ---
DEFAULT_FAVORITES = ["NVDA", "AAPL"]  # Default if no favorites saved

def get_saved_favorites():
    """Get favorites from URL query params."""
    params = st.query_params
    if "favorites" in params:
        # Parse comma-separated tickers
        favorites_str = params["favorites"]
        return [f.strip() for f in favorites_str.split(",") if f.strip()][:10]
    return None

def save_favorites(tickers):
    """Save favorites to URL query params."""
    if tickers:
        st.query_params["favorites"] = ",".join(tickers[:10])
    elif "favorites" in st.query_params:
        del st.query_params["favorites"]

# Initialize favorites from URL or defaults
saved_favorites = get_saved_favorites()
if "favorites_initialized" not in st.session_state:
    st.session_state.favorites_initialized = True
    st.session_state.current_favorites = saved_favorites or DEFAULT_FAVORITES

# --- Header ---
st.title("Stock Tracker")

# --- Rate Limit Warning Banner ---
cache_stats = provider.get_cache_stats()
if cache_stats.get("rate_limited", False):
    last_update = cache_stats.get("last_update")
    if last_update:
        update_str = last_update.strftime("%Y-%m-%d %H:%M")
        st.warning(
            f"⚠️ **Live data temporarily unavailable** (Yahoo Finance rate limit). "
            f"Showing cached data from: **{update_str}**"
        )
    else:
        st.warning(
            "⚠️ **Live data temporarily unavailable** (Yahoo Finance rate limit). "
            "Showing cached data."
        )

# --- Ticker Selection (Top Bar) ---
available_tickers = [
    ("AAPL", "Apple Inc"),
    ("GOOGL", "Alphabet Inc"),
    ("META", "Meta Platforms"),
    ("TSLA", "Tesla Inc"),
    ("NVDA", "NVIDIA Corp"),
    ("TSM", "Taiwan Semiconductor"),
    ("QCOM", "Qualcomm"),
    ("MU", "Micron Technology"),
    ("SNPS", "Synopsys"),
    ("TXN", "Texas Instruments"),
    ("STM", "STMicroelectronics"),
    ("NXPI", "NXP Semiconductors"),
    ("005930.KS", "Samsung Electronics"),
    ("RGTI", "Rigetti Computing"),
    ("1810.HK", "Xiaomi Corp"),
    ("IFX.DE", "Infineon Technologies"),
    ("RACE", "Ferrari NV"),
]

ticker_options = [f"{t[0]} - {t[1]}" for t in available_tickers]
ticker_map = {f"{t[0]} - {t[1]}": t[0] for t in available_tickers}
reverse_ticker_map = {t[0]: f"{t[0]} - {t[1]}" for t in available_tickers}

# Convert saved favorites to display format
def get_default_selection():
    """Get default selection from favorites."""
    defaults = []
    for ticker in st.session_state.current_favorites:
        if ticker in reverse_ticker_map:
            defaults.append(reverse_ticker_map[ticker])
    return defaults if defaults else ["NVDA - NVIDIA Corp", "AAPL - Apple Inc"]

col_select, col_fav = st.columns([3, 1])
with col_select:
    selected_display = st.multiselect(
        "Select tickers to compare (max 10):",
        options=ticker_options,
        default=get_default_selection(),
        max_selections=10,
        help="Select 2+ tickers for comparison view. Use ⭐ to save as favorites."
    )

selected_tickers = [ticker_map[s] for s in selected_display]

with col_fav:
    st.markdown(f"**{len(selected_tickers)}** of 10 selected")
    
    # Save as favorites button
    if st.button("⭐ Save as Favorites", help="Save current selection as your default favorites"):
        st.session_state.current_favorites = selected_tickers
        save_favorites(selected_tickers)
        st.success("Favorites saved!")
        st.rerun()
    
    # Show current favorites status
    if saved_favorites:
        st.caption(f"📌 {len(saved_favorites)} favorites loaded")

if not selected_tickers:
    st.info("Select at least one ticker to begin.")
    st.stop()

# --- Fetch all metrics once ---
@st.cache_data(ttl=300)
def fetch_metrics(tickers):
    """Fetch metrics for all tickers."""
    results = {}
    for ticker in tickers:
        results[ticker] = provider.get_core_metrics(ticker)
    return results

metrics_data = fetch_metrics(tuple(selected_tickers))

# --- Tab Navigation ---
tab_fundamental, tab_earnings, tab_price_history, tab_positions = st.tabs([
    "📊 Fundamental Snapshot",
    "📈 Earnings History", 
    "📉 Price Change History",
    "💼 Position Tracker"
])

# =============================================================================
# TAB 1: FUNDAMENTAL SNAPSHOT (Matrix A per PRD)
# =============================================================================
with tab_fundamental:
    st.markdown("## Matrix A: Fundamental Snapshot")
    st.markdown('<p class="info-dense">Compare valuation and profitability across tickers. Earnings normalized to USD for comparison.</p>', unsafe_allow_html=True)
    
    # Build matrix: Columns = Tickers, Rows = Metrics
    fundamental_data = {}
    for ticker in selected_tickers:
        m = metrics_data[ticker]
        momentum = classify_earnings_momentum(m.net_income_last_4_quarters)
        
        # Use USD-normalized earnings if available, otherwise original
        net_income_display = m.net_income_last_quarter_usd if m.net_income_last_quarter_usd else m.net_income_last_quarter
        currency_note = f" ({m.financial_currency})" if m.financial_currency != "USD" else ""
        
        fundamental_data[ticker] = {
            "Price": f"${m.price:,.2f}" if m.price else "--",
            "Market Cap": f"${m.market_cap/1e9:,.1f}B" if m.market_cap else "--",
            "P/E (TTM)": f"{m.pe_ttm:.1f}" if m.pe_ttm else "--",
            "P/E (Forward)": f"{m.pe_forward:.1f}" if m.pe_forward else "--",
            "Gross Margin": f"{m.gross_margin:.1%}" if m.gross_margin else "--",
            "Net Income (USD)": f"${net_income_display/1e9:.2f}B" if net_income_display else "--",
            "Orig. Currency": m.financial_currency if m.financial_currency != "USD" else "USD",
            "Earnings Momentum": momentum,
        }
    
    fundamental_df = pd.DataFrame(fundamental_data)
    
    # Style the dataframe
    st.dataframe(
        fundamental_df,
        height=350,
    )

# =============================================================================
# TAB 2: EARNINGS HISTORY (Matrix B per PRD)
# =============================================================================
with tab_earnings:
    st.markdown("## Matrix B: Earnings History (USD Normalized)")
    st.markdown('<p class="info-dense">Last 4 quarters of net income, normalized to USD for cross-currency comparison.</p>', unsafe_allow_html=True)
    
    quarter_labels = ["Q-1 (Latest)", "Q-2", "Q-3", "Q-4"]
    earnings_rows = []
    
    for ticker in selected_tickers:
        m = metrics_data[ticker]
        row = {"Ticker": ticker}
        
        # Use USD-normalized quarters if available
        quarters_usd = m.net_income_last_4_quarters_usd or []
        quarters_orig = m.net_income_last_4_quarters or []
        quarters = quarters_usd if quarters_usd else quarters_orig
        
        for i, q in enumerate(quarter_labels):
            if i < len(quarters) and quarters[i] is not None:
                row[q] = f"${quarters[i]/1e9:.2f}B"
            else:
                row[q] = "--"
        
        # Add original currency column
        row["Currency"] = m.financial_currency if m.financial_currency else "USD"
        
        earnings_rows.append(row)
    
    earnings_df = pd.DataFrame(earnings_rows).set_index("Ticker")
    
    st.dataframe(earnings_df)
    
    # Trend visualization (subordinate to matrix per PRD)
    st.markdown("### Earnings Trend Visualization (USD)")
    st.markdown('<p class="info-dense">Derived from the Earnings History matrix above. All values in USD billions.</p>', unsafe_allow_html=True)
    
    # Build numeric data for chart - ensure all arrays have exactly 4 elements, use USD values
    trend_data = {}
    for ticker in selected_tickers:
        m = metrics_data[ticker]
        # Prefer USD-normalized values
        quarters = m.net_income_last_4_quarters_usd or m.net_income_last_4_quarters or []
        # Pad to 4 quarters if less, reverse for chronological order
        padded = [None] * (4 - len(quarters)) + list(reversed(quarters))
        trend_data[ticker] = [q/1e9 if q else None for q in padded]
    
    trend_df = pd.DataFrame(trend_data, index=["Q-4", "Q-3", "Q-2", "Q-1 (Latest)"])
    st.line_chart(trend_df)

# =============================================================================
# TAB 3: PRICE CHANGE HISTORY (User Story 3.4)
# =============================================================================
with tab_price_history:
    st.markdown("## Price Change History (Last 10 Trading Days)")
    st.markdown('<p class="info-dense">Daily % change from open to close. Analyze streaks and trends across tickers.</p>', unsafe_allow_html=True)
    
    # Fetch price history for all tickers
    price_history_data = {}
    for ticker in selected_tickers:
        ph = provider.get_price_history(ticker, days=10)
        if ph:
            price_history_data[ticker] = ph
    
    if price_history_data:
        # Summary matrix
        st.markdown("### Summary")
        summary_rows = []
        for ticker, ph in price_history_data.items():
            streak_icon = "📈" if ph.streak_direction == "up" else "📉" if ph.streak_direction == "down" else "➡️"
            avg_icon = "+" if ph.avg_change >= 0 else ""
            
            summary_rows.append({
                "Ticker": ticker,
                "Avg Daily Change": f"{avg_icon}{ph.avg_change:.2f}%",
                "Current Streak": f"{streak_icon} {ph.streak_days} days {ph.streak_direction}",
                "Latest Change": f"{'+' if ph.daily_changes[0] >= 0 else ''}{ph.daily_changes[0]:.2f}%",
            })
        
        summary_df = pd.DataFrame(summary_rows).set_index("Ticker")
        st.dataframe(summary_df)
        
        # Detailed daily changes matrix
        st.markdown("### Daily Changes Matrix")
        st.markdown('<p class="info-dense">% change from open to close for each trading day (most recent first).</p>', unsafe_allow_html=True)
        
        # Find common dates (use first ticker's dates as reference)
        first_ticker = list(price_history_data.keys())[0]
        date_labels = price_history_data[first_ticker].dates[:10]
        
        daily_rows = []
        for ticker, ph in price_history_data.items():
            row = {"Ticker": ticker}
            for i, date in enumerate(date_labels):
                if i < len(ph.daily_changes):
                    val = ph.daily_changes[i]
                    row[date] = f"{'+' if val >= 0 else ''}{val:.2f}%"
                else:
                    row[date] = "--"
            daily_rows.append(row)
        
        daily_df = pd.DataFrame(daily_rows).set_index("Ticker")
        st.dataframe(daily_df)
        
        # Trend chart
        st.markdown("### Price Change Trend")
        chart_data = {}
        for ticker, ph in price_history_data.items():
            # Reverse to show chronological order (oldest to newest)
            chart_data[ticker] = list(reversed(ph.daily_changes))
        
        # Use dates from first ticker, reversed
        chart_dates = list(reversed(date_labels))
        chart_df = pd.DataFrame(chart_data, index=chart_dates)
        st.line_chart(chart_df)
        
    else:
        st.warning("Unable to fetch price history data.")

# =============================================================================
# TAB 4: POSITION TRACKER
# =============================================================================
with tab_positions:
    st.markdown("## Position Tracker")
    st.markdown('<p class="info-dense">Track your positions with entry/exit rules. Descriptive only - no trading recommendations.</p>', unsafe_allow_html=True)
    
    # Default settings
    col1, col2 = st.columns(2)
    with col1:
        default_tp = st.number_input("Default Take Profit %", min_value=1.0, max_value=100.0, value=20.0, step=1.0)
    with col2:
        default_sl = st.number_input("Default Stop Loss %", min_value=1.0, max_value=100.0, value=10.0, step=1.0)
    
    st.markdown("---")
    
    # Position inputs for selected tickers
    for ticker in selected_tickers:
        m = metrics_data[ticker]
        current_price = m.price
        
        with st.expander(f"**{ticker}** - Current: ${current_price:,.2f}" if current_price else f"**{ticker}** - Price N/A", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                entry = st.number_input(
                    "Entry Price ($)",
                    min_value=0.01,
                    value=st.session_state.positions.get(ticker, {}).get("entry_price", current_price or 100.0),
                    step=0.01,
                    key=f"entry_{ticker}"
                )
            with c2:
                qty = st.number_input(
                    "Quantity",
                    min_value=0.0,
                    value=st.session_state.positions.get(ticker, {}).get("quantity", 0.0),
                    step=1.0,
                    key=f"qty_{ticker}"
                )
            with c3:
                tp = st.number_input(
                    "Take Profit %",
                    min_value=1.0, max_value=100.0,
                    value=st.session_state.positions.get(ticker, {}).get("take_profit_pct", default_tp),
                    step=1.0,
                    key=f"tp_{ticker}"
                )
            with c4:
                sl = st.number_input(
                    "Stop Loss %",
                    min_value=1.0, max_value=100.0,
                    value=st.session_state.positions.get(ticker, {}).get("stop_loss_pct", default_sl),
                    step=1.0,
                    key=f"sl_{ticker}"
                )
            
            if qty > 0:
                st.session_state.positions[ticker] = {
                    "entry_price": entry,
                    "quantity": qty,
                    "take_profit_pct": tp,
                    "stop_loss_pct": sl,
                }
                
                pos = Position(ticker, entry, qty, tp/100, sl/100)
                pnl = pos.calculate_pnl(current_price)
                
                pc1, pc2, pc3, pc4 = st.columns(4)
                with pc1:
                    if pnl["unrealized_pnl"] is not None:
                        st.metric("Unrealized P&L", f"${pnl['unrealized_pnl']:,.2f}", f"{pnl['unrealized_pnl_pct']*100:+.2f}%")
                    else:
                        st.metric("Unrealized P&L", "--")
                with pc2:
                    st.metric("Take Profit @", f"${pnl['take_profit_price']:,.2f}" if pnl['take_profit_price'] else "--")
                with pc3:
                    st.metric("Stop Loss @", f"${pnl['stop_loss_price']:,.2f}" if pnl['stop_loss_price'] else "--")
                with pc4:
                    st.metric("Status", format_trigger_status(pnl['trigger_status'], pnl['trigger_proximity_pct']))
    
    # Positions summary
    if st.session_state.positions:
        st.markdown("### Active Positions Summary")
        pos_rows = []
        for ticker, pos_data in st.session_state.positions.items():
            if pos_data["quantity"] > 0 and ticker in metrics_data:
                m = metrics_data[ticker]
                pos = Position(ticker, pos_data["entry_price"], pos_data["quantity"], 
                              pos_data["take_profit_pct"]/100, pos_data["stop_loss_pct"]/100)
                pnl = pos.calculate_pnl(m.price)
                
                pos_rows.append({
                    "Ticker": ticker,
                    "Entry": f"${pos_data['entry_price']:,.2f}",
                    "Current": f"${m.price:,.2f}" if m.price else "--",
                    "Qty": pos_data["quantity"],
                    "P&L ($)": f"${pnl['unrealized_pnl']:,.2f}" if pnl['unrealized_pnl'] else "--",
                    "P&L (%)": f"{pnl['unrealized_pnl_pct']*100:+.2f}%" if pnl['unrealized_pnl_pct'] else "--",
                    "Status": format_trigger_status(pnl['trigger_status'], pnl['trigger_proximity_pct']),
                })
        
        if pos_rows:
            st.dataframe(pd.DataFrame(pos_rows).set_index("Ticker"))

# --- Sidebar with cache stats ---
with st.sidebar:
    st.markdown("### System Status")
    sidebar_stats = provider.get_cache_stats()
    st.metric("Cached Tickers", sidebar_stats["prices_count"])
    st.metric("Cache Hit Rate", sidebar_stats["hit_rate"])
    
    # Show last update time
    last_update = sidebar_stats.get("last_update")
    if last_update:
        st.caption(f"Last update: {last_update.strftime('%m/%d %H:%M')}")
    
    # Show rate limit status
    if sidebar_stats.get("rate_limited"):
        st.error("⚠️ Rate Limited")
    else:
        st.success("✅ Live Data")
    
    st.caption(f"DB: {sidebar_stats['db_size_kb']:.1f} KB")
    
    st.markdown("---")
    st.markdown("### About")
    st.caption("Stock Tracker v0.3.0")
    st.caption("Descriptive financial data only.")
    st.caption("No buy/sell recommendations.")
