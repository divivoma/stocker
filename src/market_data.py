import yfinance as yf
import pandas as pd
from configparser import ConfigParser
from pathlib import Path
import yaml

#CONFIG_FILE = Path("config/tickers.yaml")
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "tickers.yaml"


def load_tickers():
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f)
    return data["stocks"]

def collect_market_data():
    rows = []

    for ticker in load_tickers():
        stock = yf.Ticker(ticker)
        info = stock.info

        rows.append({
            "Ticker": ticker,
            "Price": info.get("currentPrice"),
            "PE": info.get("trailingPE"),
            "Forward_PE": info.get("forwardPE"),
            "EPS_TTM": info.get("trailingEps"),
            "EPS_FWD": info.get("forwardEps"),
            "MarketCap": info.get("marketCap"),
            "EarningsDate": info.get("earningsDate")
        })

    return pd.DataFrame(rows)
