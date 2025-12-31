"""Type definitions for database-utils."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypedDict

# ============================================================================
# Logging Types
# ============================================================================

type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# ============================================================================
# ID Types
# ============================================================================

type SecurityId = int
type SourceId = int
type FactorId = int
type TradeId = int

# ============================================================================
# Identifier Types
# ============================================================================

type IdentifierType = Literal[
    "ISIN",  # International Securities Identification Number (12 chars)
    "CUSIP",  # Committee on Uniform Securities Identification Procedures (9 chars)
    "SEDOL",  # Stock Exchange Daily Official List (7 chars)
    "TICKER_BBG",  # Bloomberg ticker
    "TICKER_YAHOO",  # Yahoo Finance ticker
    "JP_CODE",  # Japanese security code (4 digits)
    "FIGI",  # Financial Instrument Global Identifier (12 chars)
]

# ============================================================================
# Data Source Types
# ============================================================================

type SourceType = Literal[
    "API",  # External API (yfinance, Bloomberg, etc.)
    "FILE",  # File import (Excel, CSV)
    "MANUAL",  # Manual entry
    "DERIVED",  # Calculated/derived data
]

# ============================================================================
# Trade Types
# ============================================================================

type TradeType = Literal["BUY", "SELL"]
type TradeStatus = Literal["EXECUTED", "PENDING", "CANCELLED"]

# ============================================================================
# Security TypedDicts
# ============================================================================


class SecurityDict(TypedDict):
    """Security master record."""

    security_id: SecurityId
    name: str
    description: str | None
    asset_class: str | None
    currency: str | None
    created_at: datetime
    updated_at: datetime


class SecurityIdentifierDict(TypedDict):
    """External identifier mapping for a security."""

    id: int
    security_id: SecurityId
    identifier_type: IdentifierType
    identifier_value: str
    valid_from: date | None
    valid_to: date | None
    is_primary: bool
    created_at: datetime


class SecurityCreateDict(TypedDict, total=False):
    """Input for creating a security."""

    name: str
    description: str | None
    asset_class: str | None
    currency: str | None


# ============================================================================
# Data Source TypedDicts
# ============================================================================


class DataSourceDict(TypedDict):
    """Data source definition."""

    source_id: SourceId
    source_code: str
    source_type: SourceType
    description: str | None
    priority: int
    is_active: bool
    created_at: datetime


class DataSourceCreateDict(TypedDict, total=False):
    """Input for creating a data source."""

    source_code: str
    source_type: SourceType
    description: str | None
    priority: int


# ============================================================================
# Price Data TypedDicts
# ============================================================================


class PriceDataDict(TypedDict):
    """OHLCV price data record."""

    id: int
    security_id: SecurityId
    source_id: SourceId
    price_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: int | None
    adjusted_close: Decimal | None
    created_at: datetime


class PriceDataCreateDict(TypedDict, total=False):
    """Input for creating price data."""

    security_id: SecurityId
    source_id: SourceId
    price_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: int | None
    adjusted_close: Decimal | None


# ============================================================================
# Factor TypedDicts
# ============================================================================


class FactorDefinitionDict(TypedDict):
    """Factor/feature definition."""

    factor_id: FactorId
    factor_code: str
    factor_name: str
    description: str | None
    category: str | None
    data_type: str
    created_at: datetime


class FactorDefinitionCreateDict(TypedDict, total=False):
    """Input for creating a factor definition."""

    factor_code: str
    factor_name: str
    description: str | None
    category: str | None
    data_type: str


class FactorDataDict(TypedDict):
    """Factor data value."""

    id: int
    security_id: SecurityId
    factor_id: FactorId
    source_id: SourceId
    as_of_date: date
    value_numeric: Decimal | None
    value_text: str | None
    created_at: datetime


class FactorDataCreateDict(TypedDict, total=False):
    """Input for creating factor data."""

    security_id: SecurityId
    factor_id: FactorId
    source_id: SourceId
    as_of_date: date
    value_numeric: Decimal | None
    value_text: str | None


# ============================================================================
# Trade TypedDicts
# ============================================================================


class TradeDict(TypedDict):
    """Trade record."""

    trade_id: TradeId
    security_id: SecurityId
    trade_type: TradeType
    trade_date: date
    settlement_date: date | None
    quantity: Decimal
    price: Decimal
    currency: str
    fees: Decimal | None
    status: TradeStatus
    notes: str | None
    created_at: datetime


class TradeCreateDict(TypedDict, total=False):
    """Input for creating a trade."""

    security_id: SecurityId
    trade_type: TradeType
    trade_date: date
    settlement_date: date | None
    quantity: Decimal
    price: Decimal
    currency: str
    fees: Decimal | None
    notes: str | None


# ============================================================================
# Portfolio TypedDicts
# ============================================================================


class PortfolioHoldingDict(TypedDict):
    """Portfolio holding record."""

    id: int
    security_id: SecurityId
    as_of_date: date
    quantity: Decimal
    cost_basis: Decimal | None
    market_value: Decimal | None
    created_at: datetime


# ============================================================================
# Query Result Types
# ============================================================================


class IdentifierMatchDict(TypedDict):
    """Result of identifier resolution."""

    security_id: SecurityId
    identifier_type: IdentifierType
    identifier_value: str
    is_primary: bool


class BestPriceDict(TypedDict):
    """Best available price from prioritized sources."""

    security_id: SecurityId
    price_date: date
    close: Decimal
    source_code: str
    source_priority: int


class LatestFactorDict(TypedDict):
    """Latest factor value from prioritized sources."""

    security_id: SecurityId
    factor_code: str
    as_of_date: date
    value_numeric: Decimal | None
    value_text: str | None
    source_code: str
