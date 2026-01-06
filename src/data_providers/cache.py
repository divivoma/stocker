"""
SQLite cache layer for stock data.
Implements tiered caching strategy:
- Tier 1 (Hot): Price, Market Cap - 1 hour TTL
- Tier 2 (Warm): P/E ratios - 24 hour TTL  
- Tier 3 (Cold): Quarterly earnings - until next earnings date
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json


# Cache TTLs based on architecture proposal
PRICE_TTL_MINUTES = 60  # 1 hour per Marco's feedback
VALUATION_TTL_HOURS = 24
EARNINGS_TTL_DAYS = 90  # Quarterly data


@dataclass
class CachedPrice:
    symbol: str
    price: Optional[float]
    market_cap: Optional[int]
    fetched_at: datetime
    
    @property
    def age_minutes(self) -> float:
        return (datetime.now() - self.fetched_at).total_seconds() / 60
    
    @property
    def is_stale(self) -> bool:
        return self.age_minutes > PRICE_TTL_MINUTES


@dataclass
class CachedValuation:
    symbol: str
    pe_ttm: Optional[float]
    pe_forward: Optional[float]
    gross_margin: Optional[float]
    fetched_at: datetime
    
    @property
    def age_hours(self) -> float:
        return (datetime.now() - self.fetched_at).total_seconds() / 3600
    
    @property
    def is_stale(self) -> bool:
        return self.age_hours > VALUATION_TTL_HOURS


@dataclass  
class CachedEarnings:
    symbol: str
    quarter_end: str
    net_income: Optional[float]
    fetched_at: datetime


class StockCache:
    """SQLite-based cache for stock data."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to data/stock_tracker.db
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "stock_tracker.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                -- Price data (Tier 1 - hot, 1 hour TTL)
                CREATE TABLE IF NOT EXISTS prices (
                    symbol TEXT PRIMARY KEY,
                    price REAL,
                    market_cap INTEGER,
                    fetched_at TIMESTAMP
                );
                
                -- Valuation metrics (Tier 2 - warm, 24 hour TTL)
                CREATE TABLE IF NOT EXISTS valuations (
                    symbol TEXT PRIMARY KEY,
                    pe_ttm REAL,
                    pe_forward REAL,
                    gross_margin REAL,
                    fetched_at TIMESTAMP
                );
                
                -- Quarterly earnings (Tier 3 - cold, quarterly refresh)
                CREATE TABLE IF NOT EXISTS quarterly_earnings (
                    symbol TEXT,
                    quarter_index INTEGER,
                    net_income REAL,
                    fetched_at TIMESTAMP,
                    PRIMARY KEY (symbol, quarter_index)
                );
                
                -- Ticker metadata
                CREATE TABLE IF NOT EXISTS tickers (
                    symbol TEXT PRIMARY KEY,
                    company_name TEXT,
                    sector TEXT,
                    last_updated TIMESTAMP
                );
                
                -- User positions (persistent across sessions)
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    take_profit_pct REAL,
                    stop_loss_pct REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                );
                
                CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
                CREATE INDEX IF NOT EXISTS idx_positions_active ON positions(is_active);
            """)
            conn.commit()
        finally:
            conn.close()
    
    # --- Price Cache (Tier 1) ---
    
    def get_price(self, symbol: str) -> Optional[CachedPrice]:
        """Get cached price if not stale."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM prices WHERE symbol = ?",
                (symbol,)
            ).fetchone()
            
            if row is None:
                return None
            
            cached = CachedPrice(
                symbol=row["symbol"],
                price=row["price"],
                market_cap=row["market_cap"],
                fetched_at=datetime.fromisoformat(row["fetched_at"])
            )
            
            if cached.is_stale:
                return None
            
            return cached
        finally:
            conn.close()
    
    def set_price(self, symbol: str, price: Optional[float], market_cap: Optional[int]):
        """Cache price data."""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO prices (symbol, price, market_cap, fetched_at)
                VALUES (?, ?, ?, ?)
            """, (symbol, price, market_cap, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    # --- Valuation Cache (Tier 2) ---
    
    def get_valuation(self, symbol: str) -> Optional[CachedValuation]:
        """Get cached valuation if not stale."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM valuations WHERE symbol = ?",
                (symbol,)
            ).fetchone()
            
            if row is None:
                return None
            
            cached = CachedValuation(
                symbol=row["symbol"],
                pe_ttm=row["pe_ttm"],
                pe_forward=row["pe_forward"],
                gross_margin=row["gross_margin"],
                fetched_at=datetime.fromisoformat(row["fetched_at"])
            )
            
            if cached.is_stale:
                return None
            
            return cached
        finally:
            conn.close()
    
    def set_valuation(self, symbol: str, pe_ttm: Optional[float], 
                      pe_forward: Optional[float], gross_margin: Optional[float]):
        """Cache valuation data."""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO valuations (symbol, pe_ttm, pe_forward, gross_margin, fetched_at)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, pe_ttm, pe_forward, gross_margin, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    # --- Earnings Cache (Tier 3) ---
    
    def get_earnings(self, symbol: str) -> Optional[List[float]]:
        """Get cached quarterly earnings (last 4 quarters)."""
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT net_income, fetched_at FROM quarterly_earnings 
                WHERE symbol = ? 
                ORDER BY quarter_index ASC
            """, (symbol,)).fetchall()
            
            if not rows:
                return None
            
            # Check if data is stale (older than 90 days)
            fetched_at = datetime.fromisoformat(rows[0]["fetched_at"])
            age_days = (datetime.now() - fetched_at).days
            if age_days > EARNINGS_TTL_DAYS:
                return None
            
            return [row["net_income"] for row in rows if row["net_income"] is not None]
        finally:
            conn.close()
    
    def set_earnings(self, symbol: str, net_income_quarters: List[float]):
        """Cache quarterly earnings data."""
        conn = self._get_connection()
        try:
            # Clear old data
            conn.execute("DELETE FROM quarterly_earnings WHERE symbol = ?", (symbol,))
            
            # Insert new data
            now = datetime.now().isoformat()
            for i, income in enumerate(net_income_quarters):
                conn.execute("""
                    INSERT INTO quarterly_earnings (symbol, quarter_index, net_income, fetched_at)
                    VALUES (?, ?, ?, ?)
                """, (symbol, i, income, now))
            
            conn.commit()
        finally:
            conn.close()
    
    # --- Cache Stats ---
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for debugging."""
        conn = self._get_connection()
        try:
            stats = {}
            stats["prices_count"] = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
            stats["valuations_count"] = conn.execute("SELECT COUNT(*) FROM valuations").fetchone()[0]
            stats["earnings_symbols"] = conn.execute(
                "SELECT COUNT(DISTINCT symbol) FROM quarterly_earnings"
            ).fetchone()[0]
            stats["db_size_kb"] = self.db_path.stat().st_size / 1024 if self.db_path.exists() else 0
            return stats
        finally:
            conn.close()
