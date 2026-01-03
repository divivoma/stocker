from typing import TypedDict, Literal, List

FormatType = Literal[
    "currency",
    "market_cap",
    "ratio",
    "percent",
    "date",
    "enum"
]

class MetricDefinition(TypedDict):
    key: str
    label: str
    format: FormatType
    order: int


METRIC_DEFINITIONS: List[MetricDefinition] = [
    {
        "key": "price",
        "label": "Price",
        "format": "currency",
        "order": 1
    },
    {
        "key": "market_cap",
        "label": "Market Cap",
        "format": "market_cap",
        "order": 2
    },
    {
        "key": "pe_trailing",
        "label": "P/E (Trailing)",
        "format": "ratio",
        "order": 3
    },
    {
        "key": "pe_forward",
        "label": "P/E (Forward)",
        "format": "ratio",
        "order": 4
    },
    {
        "key": "revenue_growth_yoy",
        "label": "Revenue Growth (YoY)",
        "format": "percent",
        "order": 5
    },
    {
        "key": "last_earnings_date",
        "label": "Last Earnings",
        "format": "date",
        "order": 6
    },
    {
        "key": "earnings_result",
        "label": "Earnings Result",
        "format": "enum",
        "order": 7
    }
]
