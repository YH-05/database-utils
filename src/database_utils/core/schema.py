"""Database schema definitions for database-utils.

This module contains SQL statements for creating tables, indexes, and views.
"""

import sqlite3

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Table Definitions
# ============================================================================

SECURITIES_TABLE = """
CREATE TABLE IF NOT EXISTS securities (
    security_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    asset_class TEXT,
    currency TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

IDENTIFIER_TYPES_TABLE = """
CREATE TABLE IF NOT EXISTS identifier_types (
    type_code TEXT PRIMARY KEY,
    type_name TEXT NOT NULL,
    description TEXT,
    pattern TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SECURITY_IDENTIFIERS_TABLE = """
CREATE TABLE IF NOT EXISTS security_identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id INTEGER NOT NULL,
    identifier_type TEXT NOT NULL,
    identifier_value TEXT NOT NULL,
    valid_from DATE,
    valid_to DATE,
    is_primary INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE,
    FOREIGN KEY (identifier_type) REFERENCES identifier_types(type_code),
    UNIQUE (identifier_type, identifier_value, valid_from)
)
"""

DATA_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS data_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_code TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK (source_type IN ('API', 'FILE', 'MANUAL', 'DERIVED')),
    description TEXT,
    priority INTEGER DEFAULT 100,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

PRICE_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    price_date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL NOT NULL,
    volume INTEGER,
    adjusted_close REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES data_sources(source_id),
    UNIQUE (security_id, source_id, price_date)
)
"""

FACTOR_DEFINITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS factor_definitions (
    factor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_code TEXT NOT NULL UNIQUE,
    factor_name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    data_type TEXT DEFAULT 'numeric' CHECK (data_type IN ('numeric', 'text', 'boolean')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

FACTOR_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS factor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id INTEGER NOT NULL,
    factor_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    as_of_date DATE NOT NULL,
    value_numeric REAL,
    value_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE,
    FOREIGN KEY (factor_id) REFERENCES factor_definitions(factor_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES data_sources(source_id),
    UNIQUE (security_id, factor_id, source_id, as_of_date)
)
"""

TRADES_TABLE = """
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id INTEGER NOT NULL,
    trade_type TEXT NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    trade_date DATE NOT NULL,
    settlement_date DATE,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'JPY',
    fees REAL DEFAULT 0,
    status TEXT DEFAULT 'EXECUTED' CHECK (status IN ('EXECUTED', 'PENDING', 'CANCELLED')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE
)
"""

PORTFOLIO_HOLDINGS_TABLE = """
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id INTEGER NOT NULL,
    as_of_date DATE NOT NULL,
    quantity REAL NOT NULL,
    cost_basis REAL,
    market_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id) ON DELETE CASCADE,
    UNIQUE (security_id, as_of_date)
)
"""

# ============================================================================
# Index Definitions
# ============================================================================

INDEXES = [
    # Security identifiers indexes for fast lookup
    "CREATE INDEX IF NOT EXISTS idx_security_identifiers_value ON security_identifiers(identifier_value)",
    "CREATE INDEX IF NOT EXISTS idx_security_identifiers_type_value ON security_identifiers(identifier_type, identifier_value)",
    "CREATE INDEX IF NOT EXISTS idx_security_identifiers_security ON security_identifiers(security_id)",
    # Price data indexes
    "CREATE INDEX IF NOT EXISTS idx_price_data_security_date ON price_data(security_id, price_date)",
    "CREATE INDEX IF NOT EXISTS idx_price_data_date ON price_data(price_date)",
    # Factor data indexes
    "CREATE INDEX IF NOT EXISTS idx_factor_data_security_date ON factor_data(security_id, as_of_date)",
    "CREATE INDEX IF NOT EXISTS idx_factor_data_factor ON factor_data(factor_id)",
    # Trade indexes
    "CREATE INDEX IF NOT EXISTS idx_trades_security ON trades(security_id)",
    "CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date)",
    # Portfolio indexes
    "CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_date ON portfolio_holdings(as_of_date)",
]

# ============================================================================
# View Definitions
# ============================================================================

BEST_PRICES_VIEW = """
CREATE VIEW IF NOT EXISTS best_prices AS
SELECT
    p.security_id,
    p.price_date,
    p.open,
    p.high,
    p.low,
    p.close,
    p.volume,
    p.adjusted_close,
    ds.source_code,
    ds.priority as source_priority
FROM price_data p
JOIN data_sources ds ON p.source_id = ds.source_id
WHERE ds.is_active = 1
AND p.id = (
    SELECT p2.id
    FROM price_data p2
    JOIN data_sources ds2 ON p2.source_id = ds2.source_id
    WHERE p2.security_id = p.security_id
    AND p2.price_date = p.price_date
    AND ds2.is_active = 1
    ORDER BY ds2.priority ASC
    LIMIT 1
)
"""

LATEST_FACTORS_VIEW = """
CREATE VIEW IF NOT EXISTS latest_factors AS
SELECT
    fd.security_id,
    fdef.factor_code,
    fdef.factor_name,
    fd.as_of_date,
    fd.value_numeric,
    fd.value_text,
    ds.source_code,
    ds.priority as source_priority
FROM factor_data fd
JOIN factor_definitions fdef ON fd.factor_id = fdef.factor_id
JOIN data_sources ds ON fd.source_id = ds.source_id
WHERE ds.is_active = 1
AND fd.id = (
    SELECT fd2.id
    FROM factor_data fd2
    JOIN data_sources ds2 ON fd2.source_id = ds2.source_id
    WHERE fd2.security_id = fd.security_id
    AND fd2.factor_id = fd.factor_id
    AND fd2.as_of_date = fd.as_of_date
    AND ds2.is_active = 1
    ORDER BY ds2.priority ASC
    LIMIT 1
)
"""

# ============================================================================
# Default Data
# ============================================================================

DEFAULT_IDENTIFIER_TYPES = [
    (
        "ISIN",
        "International Securities Identification Number",
        "12-character alphanumeric code",
        r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",
    ),
    (
        "CUSIP",
        "Committee on Uniform Securities Identification Procedures",
        "9-character alphanumeric code",
        r"^[A-Z0-9]{9}$",
    ),
    (
        "SEDOL",
        "Stock Exchange Daily Official List",
        "7-character alphanumeric code",
        r"^[A-Z0-9]{7}$",
    ),
    ("TICKER_BBG", "Bloomberg Ticker", "Bloomberg ticker symbol", None),
    ("TICKER_YAHOO", "Yahoo Finance Ticker", "Yahoo Finance ticker symbol", None),
    (
        "JP_CODE",
        "Japanese Security Code",
        "4-digit Japanese security code",
        r"^[0-9]{4}$",
    ),
    (
        "FIGI",
        "Financial Instrument Global Identifier",
        "12-character identifier",
        r"^[A-Z]{3}[A-Z0-9]{9}$",
    ),
]

DEFAULT_DATA_SOURCES = [
    ("YFINANCE", "API", "Yahoo Finance API", 10),
    ("EXCEL_IMPORT", "FILE", "Excel file import", 50),
    ("MANUAL_ENTRY", "MANUAL", "Manual data entry", 100),
    ("DERIVED_CALC", "DERIVED", "Calculated/derived values", 200),
]


# ============================================================================
# Schema Initialization
# ============================================================================


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Initialize the database schema.

    Creates all tables, indexes, views, and inserts default data.

    Parameters
    ----------
    conn : sqlite3.Connection
        SQLite database connection.

    Raises
    ------
    sqlite3.Error
        If schema initialization fails.
    """
    logger.info("Initializing database schema")

    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create tables
    tables = [
        ("securities", SECURITIES_TABLE),
        ("identifier_types", IDENTIFIER_TYPES_TABLE),
        ("security_identifiers", SECURITY_IDENTIFIERS_TABLE),
        ("data_sources", DATA_SOURCES_TABLE),
        ("price_data", PRICE_DATA_TABLE),
        ("factor_definitions", FACTOR_DEFINITIONS_TABLE),
        ("factor_data", FACTOR_DATA_TABLE),
        ("trades", TRADES_TABLE),
        ("portfolio_holdings", PORTFOLIO_HOLDINGS_TABLE),
    ]

    for table_name, table_sql in tables:
        logger.debug("Creating table", table_name=table_name)
        cursor.execute(table_sql)

    # Create indexes
    for index_sql in INDEXES:
        cursor.execute(index_sql)
    logger.debug("Created indexes", count=len(INDEXES))

    # Create views
    cursor.execute(BEST_PRICES_VIEW)
    cursor.execute(LATEST_FACTORS_VIEW)
    logger.debug("Created views")

    # Insert default identifier types
    cursor.executemany(
        """
        INSERT OR IGNORE INTO identifier_types (type_code, type_name, description, pattern)
        VALUES (?, ?, ?, ?)
        """,
        DEFAULT_IDENTIFIER_TYPES,
    )
    logger.debug(
        "Inserted default identifier types", count=len(DEFAULT_IDENTIFIER_TYPES)
    )

    # Insert default data sources
    cursor.executemany(
        """
        INSERT OR IGNORE INTO data_sources (source_code, source_type, description, priority)
        VALUES (?, ?, ?, ?)
        """,
        DEFAULT_DATA_SOURCES,
    )
    logger.debug("Inserted default data sources", count=len(DEFAULT_DATA_SOURCES))

    conn.commit()
    logger.info("Database schema initialized successfully")


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get the current schema version.

    Parameters
    ----------
    conn : sqlite3.Connection
        SQLite database connection.

    Returns
    -------
    int
        Current schema version, or 0 if not set.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    return cursor.fetchone()[0]


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Set the schema version.

    Parameters
    ----------
    conn : sqlite3.Connection
        SQLite database connection.
    version : int
        Schema version to set.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA user_version = {version}")
    conn.commit()
    logger.debug("Set schema version", version=version)
