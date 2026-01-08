"""
Cached data provider that wraps YFinanceProvider with SQLite caching.
Implements tiered caching strategy for optimal performance.
Handles rate limits gracefully by returning stale cached data.
"""

from typing import Optional, Tuple
from datetime import datetime
from src.data_providers.yfinance_provider import YFinanceProvider, PriceHistory, RateLimitError
from src.data_providers.cache import StockCache
from src.domain.core_metrics import CoreMetrics
import logging

logger = logging.getLogger(__name__)


class CachedDataProvider:
    """
    Data provider with SQLite caching layer.
    
    Caching strategy:
    - Tier 1 (Price, Market Cap): 1 hour TTL
    - Tier 2 (P/E ratios, Gross Margin): 24 hour TTL
    - Tier 3 (Quarterly earnings): 90 day TTL
    
    Rate limit handling:
    - On rate limit error, returns stale cached data
    - Sets rate_limited flag for UI to show warning
    """
    
    def __init__(self, db_path: str = None):
        self.cache = StockCache(db_path)
        self.yfinance = YFinanceProvider()
        self._cache_hits = 0
        self._cache_misses = 0
        self._rate_limited = False
        self._last_rate_limit_time: Optional[datetime] = None
    
    @property
    def is_rate_limited(self) -> bool:
        """Check if we're currently rate limited."""
        return self._rate_limited
    
    def get_core_metrics(self, ticker_symbol: str) -> CoreMetrics:
        """
        Get core metrics with caching.
        Checks cache first, falls back to yfinance if stale/missing.
        On rate limit, returns stale cached data if available.
        """
        # Try to get fresh data from cache
        cached_price = self.cache.get_price(ticker_symbol)
        cached_valuation = self.cache.get_valuation(ticker_symbol)
        cached_earnings = self.cache.get_earnings(ticker_symbol)
        
        # If all cache hits (not stale), return cached data
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
                # Currency fields - defaults for cached data (USD assumed)
                price_currency="USD",
                financial_currency="USD",
                net_income_last_quarter_usd=cached_earnings[0] if cached_earnings else None,
                net_income_last_4_quarters_usd=cached_earnings or [],
            )
        
        # Cache miss - try to fetch from yfinance
        self._cache_misses += 1
        try:
            fresh_metrics = self.yfinance.get_core_metrics(ticker_symbol)
            self._rate_limited = False  # Reset rate limit flag on success
            
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
            
        except RateLimitError:
            logger.warning(f"Rate limited - falling back to stale cache for {ticker_symbol}")
            self._rate_limited = True
            self._last_rate_limit_time = datetime.now()
            
            # Try to get stale cached data
            return self._get_stale_cached_metrics(ticker_symbol)
        
        except Exception as e:
            logger.error(f"Error fetching {ticker_symbol}: {e}")
            # Try stale cache on any error
            return self._get_stale_cached_metrics(ticker_symbol)
    
    def _get_stale_cached_metrics(self, ticker_symbol: str) -> CoreMetrics:
        """Get stale cached data when fresh data unavailable."""
        cached_price = self.cache.get_price(ticker_symbol, allow_stale=True)
        cached_valuation = self.cache.get_valuation(ticker_symbol, allow_stale=True)
        cached_earnings = self.cache.get_earnings(ticker_symbol, allow_stale=True)
        
        earnings_list = cached_earnings or []
        
        if cached_price or cached_valuation or cached_earnings:
            return CoreMetrics(
                ticker=ticker_symbol,
                price=cached_price.price if cached_price else None,
                market_cap=cached_price.market_cap if cached_price else None,
                pe_ttm=cached_valuation.pe_ttm if cached_valuation else None,
                pe_forward=cached_valuation.pe_forward if cached_valuation else None,
                gross_margin=cached_valuation.gross_margin if cached_valuation else None,
                net_income_last_quarter=earnings_list[0] if earnings_list else None,
                net_income_last_4_quarters=earnings_list,
                # Currency fields - defaults for cached data
                price_currency="USD",
                financial_currency="USD",
                net_income_last_quarter_usd=earnings_list[0] if earnings_list else None,
                net_income_last_4_quarters_usd=earnings_list,
            )
        
        # No cached data at all - return empty metrics
        return CoreMetrics(
            ticker=ticker_symbol,
            price=None,
            market_cap=None,
            pe_ttm=None,
            pe_forward=None,
            gross_margin=None,
            net_income_last_quarter=None,
            net_income_last_4_quarters=[],
            price_currency="USD",
            financial_currency="USD",
            net_income_last_quarter_usd=None,
            net_income_last_4_quarters_usd=[],
        )
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics including hit rate and rate limit status."""
        stats = self.cache.get_cache_stats()
        total = self._cache_hits + self._cache_misses
        stats["cache_hits"] = self._cache_hits
        stats["cache_misses"] = self._cache_misses
        stats["hit_rate"] = f"{(self._cache_hits / total * 100):.1f}%" if total > 0 else "N/A"
        stats["rate_limited"] = self._rate_limited
        stats["last_update"] = self.cache.get_latest_update_time()
        return stats
    
    def get_latest_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the most recent data update."""
        return self.cache.get_latest_update_time()
    
    def force_refresh(self, ticker_symbol: str) -> CoreMetrics:
        """Force refresh from yfinance, bypassing cache."""
        try:
            fresh_metrics = self.yfinance.get_core_metrics(ticker_symbol)
            self._rate_limited = False
            
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
        except RateLimitError:
            self._rate_limited = True
            self._last_rate_limit_time = datetime.now()
            return self._get_stale_cached_metrics(ticker_symbol)
    
    def get_price_history(self, ticker_symbol: str, days: int = 10) -> Optional[PriceHistory]:
        """Get price history - fetches from yfinance, handles rate limits."""
        if self._rate_limited:
            # Don't even try if we know we're rate limited
            return None
        try:
            return self.yfinance.get_price_history(ticker_symbol, days)
        except Exception:
            return None
