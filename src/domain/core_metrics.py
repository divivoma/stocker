from dataclasses import dataclass
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
