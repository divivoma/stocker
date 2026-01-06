import pytest
import tempfile
import os
from datetime import datetime, timedelta
from src.data_providers.cache import StockCache, CachedPrice, CachedValuation, PRICE_TTL_MINUTES


class TestStockCache:
    @pytest.fixture
    def cache(self):
        """Create a temporary cache for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_cache.db")
            yield StockCache(db_path)
    
    def test_set_and_get_price(self, cache):
        """Test price caching."""
        cache.set_price("NVDA", 450.0, 1100000000000)
        
        result = cache.get_price("NVDA")
        
        assert result is not None
        assert result.symbol == "NVDA"
        assert result.price == 450.0
        assert result.market_cap == 1100000000000
    
    def test_price_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get_price("UNKNOWN")
        assert result is None
    
    def test_set_and_get_valuation(self, cache):
        """Test valuation caching."""
        cache.set_valuation("AAPL", 28.5, 25.0, 0.45)
        
        result = cache.get_valuation("AAPL")
        
        assert result is not None
        assert result.pe_ttm == 28.5
        assert result.pe_forward == 25.0
        assert result.gross_margin == 0.45
    
    def test_set_and_get_earnings(self, cache):
        """Test earnings caching."""
        earnings = [15000000000.0, 14500000000.0, 14000000000.0, 13500000000.0]
        cache.set_earnings("MSFT", earnings)
        
        result = cache.get_earnings("MSFT")
        
        assert result is not None
        assert len(result) == 4
        assert result[0] == 15000000000.0
    
    def test_earnings_overwrites_old_data(self, cache):
        """Test that new earnings replace old data."""
        old_earnings = [1000.0, 2000.0]
        new_earnings = [3000.0, 4000.0, 5000.0]
        
        cache.set_earnings("TEST", old_earnings)
        cache.set_earnings("TEST", new_earnings)
        
        result = cache.get_earnings("TEST")
        assert len(result) == 3
        assert result[0] == 3000.0
    
    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set_price("NVDA", 450.0, 1100000000000)
        cache.set_price("AAPL", 180.0, 2800000000000)
        cache.set_valuation("NVDA", 60.0, 50.0, 0.75)
        
        stats = cache.get_cache_stats()
        
        assert stats["prices_count"] == 2
        assert stats["valuations_count"] == 1
    
    def test_price_update_replaces(self, cache):
        """Test that updating price replaces old value."""
        cache.set_price("NVDA", 400.0, 1000000000000)
        cache.set_price("NVDA", 450.0, 1100000000000)
        
        result = cache.get_price("NVDA")
        assert result.price == 450.0


class TestCachedPrice:
    def test_age_calculation(self):
        """Test age calculation."""
        cached = CachedPrice(
            symbol="NVDA",
            price=450.0,
            market_cap=1100000000000,
            fetched_at=datetime.now() - timedelta(minutes=30)
        )
        
        assert 29 < cached.age_minutes < 31
    
    def test_is_stale_fresh(self):
        """Test fresh data is not stale."""
        cached = CachedPrice(
            symbol="NVDA",
            price=450.0,
            market_cap=1100000000000,
            fetched_at=datetime.now()
        )
        
        assert not cached.is_stale
    
    def test_is_stale_old(self):
        """Test old data is stale."""
        cached = CachedPrice(
            symbol="NVDA",
            price=450.0,
            market_cap=1100000000000,
            fetched_at=datetime.now() - timedelta(minutes=PRICE_TTL_MINUTES + 1)
        )
        
        assert cached.is_stale
