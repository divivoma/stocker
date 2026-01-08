"""
Currency conversion for normalizing financial data to USD.
Rates are approximate annual averages - update yearly.
Last updated: January 2026
"""

from typing import Optional

# Exchange rates to USD (1 unit of foreign currency = X USD)
# These are approximate rates - update annually
# Source: Use average rates for the fiscal year
CURRENCY_TO_USD = {
    "USD": 1.0,
    "TWD": 0.031,    # Taiwan Dollar (~32 TWD = 1 USD)
    "HKD": 0.128,    # Hong Kong Dollar (~7.8 HKD = 1 USD)
    "CNY": 0.137,    # Chinese Yuan (~7.3 CNY = 1 USD)
    "KRW": 0.00069,  # Korean Won (~1450 KRW = 1 USD)
    "EUR": 1.08,     # Euro
    "GBP": 1.25,     # British Pound
    "JPY": 0.0064,   # Japanese Yen (~156 JPY = 1 USD)
    "INR": 0.012,    # Indian Rupee
    "CHF": 1.12,     # Swiss Franc
    "CAD": 0.71,     # Canadian Dollar
    "AUD": 0.64,     # Australian Dollar
    "SGD": 0.74,     # Singapore Dollar
}

# Last update date for reference
RATES_LAST_UPDATED = "2026-01"


def get_usd_rate(currency: str) -> float:
    """
    Get the conversion rate from a currency to USD.
    Returns 1.0 for unknown currencies (assumes USD).
    """
    return CURRENCY_TO_USD.get(currency.upper(), 1.0)


def convert_to_usd(amount: Optional[float], from_currency: str) -> Optional[float]:
    """
    Convert an amount from a given currency to USD.
    Returns None if amount is None.
    """
    if amount is None:
        return None
    
    rate = get_usd_rate(from_currency)
    return amount * rate


def normalize_earnings_to_usd(
    earnings: list, 
    financial_currency: str
) -> list:
    """
    Normalize a list of earnings values to USD.
    
    Args:
        earnings: List of earnings values in original currency
        financial_currency: The currency code (e.g., 'TWD', 'HKD', 'USD')
    
    Returns:
        List of earnings values converted to USD
    """
    if not earnings:
        return []
    
    rate = get_usd_rate(financial_currency)
    
    # If already USD, no conversion needed
    if rate == 1.0:
        return earnings
    
    return [e * rate if e is not None else None for e in earnings]


def is_currency_supported(currency: str) -> bool:
    """Check if we have a conversion rate for this currency."""
    return currency.upper() in CURRENCY_TO_USD


def get_currency_symbol(currency: str) -> str:
    """Get the display symbol for a currency."""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CNY": "¥",
        "KRW": "₩",
        "TWD": "NT$",
        "HKD": "HK$",
        "INR": "₹",
        "CHF": "CHF",
        "CAD": "C$",
        "AUD": "A$",
        "SGD": "S$",
    }
    return symbols.get(currency.upper(), currency)
