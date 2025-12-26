import yfinance as yf
import pandas as pd
from src.market_data import load_tickers
from src.sentiment import sentiment_score

def collect_news(limit=10):
    rows = []

    for ticker in load_tickers():
        stock = yf.Ticker(ticker)
        news = stock.news or []

        for item in news[:limit]:
            rows.append({
                "Ticker": ticker,
                "Date": item.get("providerPublishTime"),
                "Source": item.get("publisher"),
                "Title": item.get("title"),
                "Sentiment": sentiment_score(item.get("title", ""))
            })

    return pd.DataFrame(rows)
