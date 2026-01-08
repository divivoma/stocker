from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CoreMetrics:
    ticker: str
    price: Optional[float]
    market_cap: Optional[int]
    pe_ttm: Optional[float]
    pe_forward: Optional[float]
    gross_margin: Optional[float]
    net_income_last_quarter: Optional[float]
    net_income_last_4_quarters: List[float]
    # Currency information
    price_currency: str = "USD"  # Currency for price/market cap
    financial_currency: str = "USD"  # Currency for earnings/financials
    # USD-normalized earnings (for comparison)
    net_income_last_quarter_usd: Optional[float] = None
    net_income_last_4_quarters_usd: List[float] = field(default_factory=list)
