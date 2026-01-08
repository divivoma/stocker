import yfinance as yf
from src.domain.core_metrics import CoreMetrics
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when Yahoo Finance rate limit is hit."""
    pass


@dataclass
class PriceHistory:
    """Daily price change history for a ticker."""
    ticker: str
    daily_changes: List[float]  # % changes from open, most recent first
    dates: List[str]  # Date labels
    streak_days: int  # Consecutive days in same direction
    streak_direction: str  # "up", "down", or "mixed"
    avg_change: float  # Average % change over period


class YFinanceProvider:
    def get_core_metrics(self, ticker_symbol: str) -> CoreMetrics:
        """
        Fetch core metrics from Yahoo Finance.
        Raises RateLimitError if rate limited.
        """
        try:
            t = yf.Ticker(ticker_symbol)
            info = t.info
            qf = t.quarterly_financials

            net_income_series = []
            if not qf.empty and "Net Income" in qf.index:
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
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                logger.warning(f"Rate limit hit for {ticker_symbol}")
                raise RateLimitError(f"Rate limit exceeded for {ticker_symbol}")
            raise

    def get_price_history(self, ticker_symbol: str, days: int = 10) -> Optional[PriceHistory]:
        """
        Get historical daily price changes for the last N trading days.
        Returns % change from open to close for each day.
        """
        try:
            t = yf.Ticker(ticker_symbol)
            # Fetch extra days to ensure we get enough trading days
            hist = t.history(period=f"{days + 5}d")
            
            if hist.empty or len(hist) < 2:
                return None
            
            # Calculate daily % change (close vs open)
            hist = hist.tail(days)  # Get last N days
            daily_changes = []
            dates = []
            
            for idx, row in hist.iterrows():
                if row["Open"] > 0:
                    pct_change = ((row["Close"] - row["Open"]) / row["Open"]) * 100
                    daily_changes.append(round(pct_change, 2))
                    dates.append(idx.strftime("%m/%d"))
            
            # Reverse to have most recent first
            daily_changes = daily_changes[::-1]
            dates = dates[::-1]
            
            # Calculate streak
            streak_days, streak_direction = self._calculate_streak(daily_changes)
            avg_change = sum(daily_changes) / len(daily_changes) if daily_changes else 0
            
            return PriceHistory(
                ticker=ticker_symbol,
                daily_changes=daily_changes,
                dates=dates,
                streak_days=streak_days,
                streak_direction=streak_direction,
                avg_change=round(avg_change, 2),
            )
        except Exception:
            return None
    
    def _calculate_streak(self, changes: List[float]) -> tuple:
        """Calculate consecutive days in same direction from most recent."""
        if not changes:
            return 0, "mixed"
        
        streak = 1
        direction = "up" if changes[0] >= 0 else "down"
        
        for i in range(1, len(changes)):
            current_dir = "up" if changes[i] >= 0 else "down"
            if current_dir == direction:
                streak += 1
            else:
                break
        
        return streak, direction
