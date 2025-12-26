import pandas as pd
from pathlib import Path
from datetime import date

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def write_report(market_df, news_df):
    filename = DATA_DIR / f"weekly_stock_review_{date.today()}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        market_df.to_excel(writer, sheet_name="Overview", index=False)
        news_df.to_excel(writer, sheet_name="News", index=False)
