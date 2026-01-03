import sys
import os

# Add project root to Python path so 'src' modules can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
from typing import Optional, List
from src.domain.metrics import MetricSet
from src.domain.metric_definitions import METRIC_DEFINITIONS


# Mock data
mock_data = {
    "NVDA": {
        "price": 123.45,
        "market_cap": 1.2e12,
        "pe_trailing": 45.2,
        "pe_forward": 32.1,
        "revenue_growth_yoy": 18.3,
        "last_earnings_date": "2025-02-10",
        "earnings_result": "Beat"
    },
    "MSFT": {
        "price": 320.12,
        "market_cap": 2.4e12,
        "pe_trailing": 35.4,
        "pe_forward": 30.1,
        "revenue_growth_yoy": 12.1,
        "last_earnings_date": "2025-02-15",
        "earnings_result": "Meet"
    },
    "AAPL": {
        "price": 195.78,
        "market_cap": 3.0e12,
        "pe_trailing": 28.9,
        "pe_forward": 25.3,
        "revenue_growth_yoy": 8.7,
        "last_earnings_date": "2025-02-12",
        "earnings_result": "Beat"
    }
}

# Default top 10 tickers (use as needed)
DEFAULT_TICKERS = list(mock_data.keys())

st.title("Nasdaq-100 Stock Tracker Prototype")

# Multi-select ticker
selected_tickers: List[str] = st.multiselect(
    "Select up to 10 tickers:",
    options=list(mock_data.keys()),
    default=DEFAULT_TICKERS[:3],
    max_selections=10
)

if not selected_tickers:
    st.info("Select one or more tickers to view metrics.")
else:
    # Build comparison table
    rows = []
    metric_order = sorted(METRIC_DEFINITIONS, key=lambda x: x["order"])
    for metric_def in metric_order:
        row = {"Metric": metric_def["label"]}
        for ticker in selected_tickers:
            ticker_data = mock_data.get(ticker, {})
            value = ticker_data.get(metric_def["key"])
            if value is None:
                display_value = "—"
            else:
                fmt = metric_def["format"]
                if fmt == "currency":
                    display_value = f"${value:,.2f}"
                elif fmt == "market_cap":
                    if value >= 1e12:
                        display_value = f"{value/1e12:.2f} T"
                    elif value >= 1e9:
                        display_value = f"{value/1e9:.1f} B"
                    elif value >= 1e6:
                        display_value = f"{value/1e6:.1f} M"
                    else:
                        display_value = str(value)
                elif fmt == "ratio":
                    display_value = f"{value:.1f}"
                elif fmt == "percent":
                    display_value = f"{value:.1f} %"
                elif fmt == "date":
                    display_value = str(value)
                elif fmt == "enum":
                    display_value = str(value)
                else:
                    display_value = str(value)
            row[ticker] = display_value
        rows.append(row)

    df = pd.DataFrame(rows)
    st.table(df)
