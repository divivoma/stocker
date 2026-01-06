# Data Architecture Proposal: Local Caching Strategy

## Problem Statement

Currently, every page load/refresh in Stock Tracker calls yfinance API for each selected ticker. This creates:
1. **Unnecessary API calls** - Quarterly earnings don't change between earnings dates
2. **Slow UI** - Each ticker fetch takes 1-3 seconds
3. **Rate limiting risk** - yfinance may throttle excessive requests
4. **Poor UX** - Users wait for data that hasn't changed

## Data Classification by Volatility

| Data Type | Update Frequency | Staleness Tolerance | Caching Strategy |
|-----------|------------------|---------------------|------------------|
| **Price** | Real-time | 15 min (delayed anyway) | Short TTL cache |
| **Market Cap** | Daily | 1 day | Daily refresh |
| **P/E Ratios** | Daily | 1 day | Daily refresh |
| **Gross Margin** | Quarterly | 90 days | Event-driven |
| **Net Income (quarterly)** | Quarterly | 90 days | Event-driven |
| **Earnings Date** | Quarterly | 90 days | Event-driven |

## Proposed Refresh Strategy

### Tier 1: Hot Data (Price-sensitive)
- **Data**: Current price, market cap
- **Refresh**: Every 15 minutes during market hours, or on-demand
- **Cache TTL**: 15 minutes

### Tier 2: Warm Data (Daily metrics)
- **Data**: P/E ratios (TTM, Forward)
- **Refresh**: Once daily after market close
- **Cache TTL**: 24 hours

### Tier 3: Cold Data (Quarterly fundamentals)
- **Data**: Net income, gross margin, earnings results
- **Refresh**: Only when new earnings are released (check earnings calendar)
- **Cache TTL**: Until next earnings date

## Database Recommendation: SQLite

### Why SQLite for MVP/Demo?

| Criteria | SQLite | PostgreSQL | MongoDB |
|----------|--------|------------|---------|
| Zero config | ✅ | ❌ | ❌ |
| No server needed | ✅ | ❌ | ❌ |
| Single file | ✅ | ❌ | ❌ |
| Python built-in | ✅ | ❌ | ❌ |
| Portable | ✅ | ❌ | ❌ |
| Good for demo | ✅ | Overkill | Overkill |
| Production-ready | ⚠️ Limited | ✅ | ✅ |

**Verdict**: SQLite is perfect for local-first MVP. Single `stock_tracker.db` file, no setup, works offline.

### Alternative Considered: DuckDB
- Better for analytical queries
- Also single-file, zero-config
- Overkill for current data volume

## Proposed Schema

```sql
-- Core ticker metadata (rarely changes)
CREATE TABLE tickers (
    symbol TEXT PRIMARY KEY,
    company_name TEXT,
    sector TEXT,
    last_updated TIMESTAMP
);

-- Price data (Tier 1 - hot)
CREATE TABLE prices (
    symbol TEXT,
    price REAL,
    market_cap INTEGER,
    fetched_at TIMESTAMP,
    PRIMARY KEY (symbol)
);

-- Valuation metrics (Tier 2 - warm)
CREATE TABLE valuations (
    symbol TEXT,
    pe_ttm REAL,
    pe_forward REAL,
    gross_margin REAL,
    fetched_at TIMESTAMP,
    PRIMARY KEY (symbol)
);

-- Quarterly earnings (Tier 3 - cold)
CREATE TABLE quarterly_earnings (
    symbol TEXT,
    quarter_end DATE,
    net_income REAL,
    revenue REAL,
    eps REAL,
    earnings_result TEXT,  -- Beat/Meet/Miss
    fetched_at TIMESTAMP,
    PRIMARY KEY (symbol, quarter_end)
);

-- Cache metadata
CREATE TABLE cache_metadata (
    symbol TEXT,
    data_type TEXT,  -- 'price', 'valuation', 'earnings'
    last_fetch TIMESTAMP,
    next_refresh TIMESTAMP,
    PRIMARY KEY (symbol, data_type)
);

-- User positions (persisted across sessions)
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    entry_price REAL,
    quantity REAL,
    take_profit_pct REAL,
    stop_loss_pct REAL,
    created_at TIMESTAMP,
    closed_at TIMESTAMP
);
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                             │
│  (app_live.py)                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CachedDataProvider                          │
│  - Checks cache first                                           │
│  - Respects TTL per data tier                                   │
│  - Falls back to yfinance if stale/missing                      │
└─────────────────────────────────────────────────────────────────┘
                    │                       │
                    ▼                       ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│      SQLite Cache         │   │     YFinanceProvider          │
│   (stock_tracker.db)      │   │   (existing, unchanged)       │
│                           │   │                               │
│  - prices                 │   │  - get_core_metrics()         │
│  - valuations             │   │  - (future) get_earnings()    │
│  - quarterly_earnings     │   │                               │
│  - positions              │   │                               │
└───────────────────────────┘   └───────────────────────────────┘
```

## Refresh Logic (Pseudocode)

```python
class CachedDataProvider:
    def get_price(self, symbol: str) -> float:
        cached = self.cache.get_price(symbol)
        if cached and cached.age < 15_minutes:
            return cached.price
        
        # Fetch fresh
        fresh = self.yfinance.get_price(symbol)
        self.cache.set_price(symbol, fresh)
        return fresh
    
    def get_quarterly_earnings(self, symbol: str) -> List[QuarterlyEarnings]:
        cached = self.cache.get_earnings(symbol)
        next_earnings_date = self.get_next_earnings_date(symbol)
        
        if cached and datetime.now() < next_earnings_date:
            return cached  # Still valid until next earnings
        
        # New earnings released, fetch fresh
        fresh = self.yfinance.get_quarterly_financials(symbol)
        self.cache.set_earnings(symbol, fresh)
        return fresh
```

## Migration Path

### Phase 1: Add SQLite Cache (Non-breaking)
1. Create `src/data_providers/cache.py` with SQLite operations
2. Create `src/data_providers/cached_provider.py` wrapping YFinanceProvider
3. Keep YFinanceProvider unchanged as fallback
4. DB file: `data/stock_tracker.db`

### Phase 2: Position Persistence
1. Migrate session_state positions to SQLite
2. Positions survive browser refresh
3. Add position history tracking

### Phase 3: Background Refresh (Optional)
1. Scheduled job to refresh Tier 2/3 data
2. Run on app startup or via cron
3. Pre-warm cache for watched tickers

## Benefits

| Metric | Before | After |
|--------|--------|-------|
| Page load (10 tickers) | 15-30 sec | < 1 sec (cached) |
| API calls per session | 10+ per view | 1-2 per day |
| Offline capability | None | Full (cached data) |
| Position persistence | Session only | Permanent |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Stale price data | Clear visual indicator "as of 15m ago" |
| Missed earnings update | Check earnings calendar on each view |
| DB corruption | Single file, easy to backup/restore |
| SQLite concurrency | Fine for single-user MVP |

## Open Questions for PRD

1. Should price refresh be user-triggered ("Refresh" button) or automatic? Marco answer: no, we can update the price every hour, this is not a tracker for quantum trading, remember the persona.
2. Should positions auto-close when triggers hit, or just alert?  Marco answer: no, user need to decide and take action not this tracker.
3. Do we need position history/audit trail? Marco answer: Marco answer: good proposal, capture it as a potential feature to be implemented later and put it in the PRD, do not implement now (backlog).
4. Should cache be clearable by user? Marco answer: no.

---

## Recommendation

**Start with Phase 1**: Add SQLite caching layer without changing existing YFinanceProvider. This gives:
- 10x faster UI for cached data
- Foundation for position persistence
- Zero-risk (fallback to live API)
- Demo-ready with single DB file
