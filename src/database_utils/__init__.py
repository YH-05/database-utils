"""database-utils: SQLite utilities for financial data management."""

from .core.connection import (
    ConnectionError,
    DatabaseConnection,
    DatabaseError,
    TransactionError,
)
from .core.identifier import IdentifierResolver
from .core.repositories.security import SecurityRepository
from .exceptions import (
    DatabaseUtilsError,
    DuplicateSecurityError,
    IdentifierNotFoundError,
    ValidationError,
)
from .utils.logging_config import get_logger, set_log_level, setup_logging

__all__ = [
    # Core
    "DatabaseConnection",
    "DatabaseError",
    "ConnectionError",
    "TransactionError",
    # Identifier Resolution
    "IdentifierResolver",
    "SecurityRepository",
    # Exceptions
    "DatabaseUtilsError",
    "IdentifierNotFoundError",
    "DuplicateSecurityError",
    "ValidationError",
    # Logging
    "get_logger",
    "set_log_level",
    "setup_logging",
]

__version__ = "0.1.0"
