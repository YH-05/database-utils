"""Core module for database-utils package."""

from .connection import (
    ConnectionError,
    DatabaseConnection,
    DatabaseError,
    TransactionError,
)
from .schema import (
    get_schema_version,
    initialize_schema,
    set_schema_version,
)

__all__ = [
    "ConnectionError",
    "DatabaseConnection",
    "DatabaseError",
    "TransactionError",
    "get_schema_version",
    "initialize_schema",
    "set_schema_version",
]
