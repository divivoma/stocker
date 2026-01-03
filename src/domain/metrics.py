from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class MetricSet:
    price: Optional[float]
    market_cap: Optional[float]
    pe_trailing: Optional[float]
    pe_forward: Optional[float]
    revenue_growth_yoy: Optional[float]
    last_earnings_date: Optional[str]
    earnings_result: Optional[str]
