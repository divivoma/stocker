"""
Cached data provider that wraps YFinanceProvider with SQLite caching.
Implements tiered caching strategy for optimal performance.
"""

from typing import Optional
from src.data_providers.yfinance_provider import YFinanceProvider
from src.data_providers.cache import StockCache
from src.domain.core_metrics import CoreMetrics


class CachedDataProvider:
    """
    Data provider with SQLite caching layer.
    
    Caching strategy:
    - Tier 1 (Price, Market Cap): 1 hour TTL
    - Tier 2 (P/E ratios, Gross Margin): 24 hour TTL
    - Tier 3 (Quarterly earnings): 90 day TTL
    """
    
    def __init__(self, db_path: str = None):
        self.cache = StockCache(db_path)
        self.yfinance = YFinanceProvider()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_core_metrics(self, ticker_symbol: str) -> CoreMetrics:
        """
        Get core metrics with caching.
        Checks cache first, falls back to yfinance if stale/missing.
        """
        # Try to get all data from cache
        cached_price = self.cache.get_price(ticker_symbol)
        cached_valuation = self.cache.get_valuation(ticker_symbol)
        cached_earnings = self.cache.get_earnings(ticker_symbol)
        
        # If all cache hits, return cached data
        if cached_price and cached_valuation and cached_earnings:
            self._cache_hits += 1
            return CoreMetrics(
                ticker=ticker_symbol,
                price=cached_price.price,
                market_cap=cached_price.market_cap,
                pe_ttm=cached_valuation.pe_ttm,
                pe_forward=cached_valuation.pe_forward,
                gross_margin=cached_valuation.gross_margin,
                net_income_last_quarter=cached_earnings[0] if cached_earnings else None,
                net_income_last_4_quarters=cached_earnings or [],
            )
        
        # Cache miss - fetch from yfinance
        self._cache_misses += 1
        fresh_metrics = self.yfinance.get_core_metrics(ticker_symbol)
        
        # Update cache with fresh data
        self.cache.set_price(
            ticker_symbol,
            fresh_metrics.price,
            fresh_metrics.market_cap
        )
        self.cache.set_valuation(
            ticker_symbol,
            fresh_metrics.pe_ttm,
            fresh_metrics.pe_forward,
            fresh_metrics.gross_margin
        )
        if fresh_metrics.net_income_last_4_quarters:
            self.cache.set_earnings(
                ticker_symbol,
                fresh_metrics.net_income_last_4_quarters
            )
        
        return fresh_metrics
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics including hit rate."""
        stats = self.cache.get_cache_stats()
        total = self._cache_hits + self._cache_misses
        stats["cache_hits"] = self._cache_hits
        stats["cache_misses"] = self._cache_misses
        stats["hit_rate"] = f"{(self._cache_hits / total * 100):.1f}%" if total > 0 else "N/A"
        return stats
    
    def force_refresh(self, ticker_symbol: str) -> CoreMetrics:
        """Force refresh from yfinance, bypassing cache."""
        fresh_metrics = self.yfinance.get_core_metrics(ticker_symbol)
        
        # Update cache
        self.cache.set_price(
            ticker_symbol,
            fresh_metrics.price,
            fresh_metrics.market_cap
        )
        self.cache.set_valuation(
            ticker_symbol,
            fresh_metrics.pe_ttm,
            fresh_metrics.pe_forward,
            fresh_metrics.gross_margin
        )
        if fresh_metrics.net_income_last_4_quarters:
            self.cache.set_earnings(
                ticker_symbol,
                fresh_metrics.net_income_last_4_quarters
            )
        
        return fresh_metrics
