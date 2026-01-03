import yfinance as yf
from src.domain.core_metrics import CoreMetrics


class YFinanceProvider:
    def get_core_metrics(self, ticker_symbol: str) -> CoreMetrics:
        t = yf.Ticker(ticker_symbol)

        info = t.info
        qf = t.quarterly_financials

        net_income_series = []
        if "Net Income" in qf.index:
            net_income_series = (
                qf.loc["Net Income"]
                .dropna()
                .head(4)
                .tolist()
            )

        return CoreMetrics(
            ticker=ticker_symbol,
            price=info.get("currentPrice"),
            market_cap=info.get("marketCap"),
            pe_ttm=info.get("trailingPE"),
            pe_forward=info.get("forwardPE"),
            gross_margin=info.get("grossMargins"),
            net_income_last_quarter=net_income_series[0] if net_income_series else None,
            net_income_last_4_quarters=net_income_series,
        )
