"""Database connection management for database-utils.

This module provides the DatabaseConnection class for managing SQLite connections.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..utils.logging_config import get_logger
from .schema import initialize_schema

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Base exception for database errors."""


class ConnectionError(DatabaseError):
    """Error connecting to the database."""


class TransactionError(DatabaseError):
    """Error during a transaction."""


class DatabaseConnection:
    """Manages SQLite database connections.

    Provides connection management, transaction handling, and schema initialization.

    Parameters
    ----------
    db_path : str | Path
        Path to the SQLite database file. Use `:memory:` for in-memory database.
    auto_initialize : bool, optional
        Whether to automatically initialize schema on first connection.
        Default is True.

    Examples
    --------
    Basic usage:

    >>> db = DatabaseConnection("portfolio.db")
    >>> with db.transaction():
    ...     db.execute("INSERT INTO securities (name) VALUES (?)", ("AAPL",))

    In-memory database for testing:

    >>> db = DatabaseConnection(":memory:")
    """

    def __init__(self, db_path: str | Path, *, auto_initialize: bool = True) -> None:
        """Initialize the database connection."""
        self._db_path = Path(db_path) if db_path != ":memory:" else db_path
        self._conn: sqlite3.Connection | None = None
        self._auto_initialize = auto_initialize
        self._initialized = False

        logger.debug("DatabaseConnection created", db_path=str(db_path))

    @property
    def db_path(self) -> str | Path:
        """Get the database path."""
        return self._db_path

    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._conn is not None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the raw SQLite connection.

        Returns
        -------
        sqlite3.Connection
            The underlying SQLite connection.

        Raises
        ------
        ConnectionError
            If not connected to the database.
        """
        if self._conn is None:
            raise ConnectionError("Not connected to database. Call connect() first.")
        return self._conn

    def connect(self) -> None:
        """Establish connection to the database.

        Raises
        ------
        ConnectionError
            If connection fails.
        """
        if self._conn is not None:
            return

        try:
            db_path_str = (
                str(self._db_path) if isinstance(self._db_path, Path) else self._db_path
            )

            self._conn = sqlite3.connect(db_path_str)
            self._conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrent access
            self._conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key constraints
            self._conn.execute("PRAGMA foreign_keys=ON")

            logger.info("Connected to database", db_path=db_path_str)

            if self._auto_initialize and not self._initialized:
                self.initialize()

        except sqlite3.Error as e:
            msg = f"Failed to connect to database at {self._db_path}: {e}"
            logger.error(msg)
            raise ConnectionError(msg) from e

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.debug("Database connection closed")

    def initialize(self) -> None:
        """Initialize the database schema.

        Creates all tables, indexes, views, and inserts default data.

        Raises
        ------
        DatabaseError
            If initialization fails.
        """
        if self._conn is None:
            self.connect()
            return  # connect() will call initialize()

        try:
            initialize_schema(self._conn)
            self._initialized = True
        except sqlite3.Error as e:
            msg = f"Failed to initialize database schema: {e}"
            logger.error(msg, exc_info=True)
            raise DatabaseError(msg) from e

    def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | dict[str, Any] = (),
    ) -> sqlite3.Cursor:
        """Execute a SQL statement.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        params : tuple or dict, optional
            Parameters for the SQL statement.

        Returns
        -------
        sqlite3.Cursor
            Cursor with query results.

        Raises
        ------
        DatabaseError
            If execution fails.
        """
        if self._conn is None:
            self.connect()

        assert self._conn is not None  # for type checker

        try:
            cursor = self._conn.execute(sql, params)
            return cursor
        except sqlite3.Error as e:
            logger.error("SQL execution failed", sql=sql[:100], error=str(e))
            raise DatabaseError(f"SQL execution failed: {e}") from e

    def executemany(
        self,
        sql: str,
        params_seq: list[tuple[Any, ...]] | list[dict[str, Any]],
    ) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        params_seq : list
            Sequence of parameter tuples or dicts.

        Returns
        -------
        sqlite3.Cursor
            Cursor with results.

        Raises
        ------
        DatabaseError
            If execution fails.
        """
        if self._conn is None:
            self.connect()

        assert self._conn is not None

        try:
            cursor = self._conn.executemany(sql, params_seq)
            return cursor
        except sqlite3.Error as e:
            logger.error("SQL executemany failed", sql=sql[:100], error=str(e))
            raise DatabaseError(f"SQL executemany failed: {e}") from e

    def fetchone(
        self,
        sql: str,
        params: tuple[Any, ...] | dict[str, Any] = (),
    ) -> sqlite3.Row | None:
        """Execute SQL and fetch one row.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        params : tuple or dict, optional
            Parameters for the SQL statement.

        Returns
        -------
        sqlite3.Row or None
            Single row result or None if no rows.
        """
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def fetchall(
        self,
        sql: str,
        params: tuple[Any, ...] | dict[str, Any] = (),
    ) -> list[sqlite3.Row]:
        """Execute SQL and fetch all rows.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        params : tuple or dict, optional
            Parameters for the SQL statement.

        Returns
        -------
        list[sqlite3.Row]
            List of row results.
        """
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._conn is not None:
            self._conn.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._conn is not None:
            self._conn.rollback()

    @contextmanager
    def transaction(self):
        """Context manager for transactions.

        Automatically commits on success, rolls back on exception.

        Yields
        ------
        DatabaseConnection
            Self for chaining.

        Raises
        ------
        TransactionError
            If transaction fails.

        Examples
        --------
        >>> with db.transaction():
        ...     db.execute("INSERT INTO securities (name) VALUES (?)", ("AAPL",))
        ...     db.execute("INSERT INTO securities (name) VALUES (?)", ("GOOGL",))
        """
        if self._conn is None:
            self.connect()

        assert self._conn is not None

        try:
            yield self
            self._conn.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            self._conn.rollback()
            logger.warning("Transaction rolled back", error=str(e))
            raise TransactionError(f"Transaction failed: {e}") from e

    def __enter__(self) -> "DatabaseConnection":
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.close()

    def __repr__(self) -> str:
        """Return string representation."""
        status = "connected" if self.is_connected else "disconnected"
        return f"DatabaseConnection(db_path='{self._db_path}', status={status})"
