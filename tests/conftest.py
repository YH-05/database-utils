"""Pytest configuration and fixtures for database-utils tests."""

import pytest

from database_utils import DatabaseConnection


@pytest.fixture
def memory_db() -> DatabaseConnection:
    """Create an in-memory database connection.

    Returns
    -------
    DatabaseConnection
        Connected and initialized in-memory database.
    """
    db = DatabaseConnection(":memory:")
    db.connect()
    return db


@pytest.fixture
def empty_db() -> DatabaseConnection:
    """Create an uninitialized in-memory database.

    Returns
    -------
    DatabaseConnection
        Connected but not initialized database.
    """
    db = DatabaseConnection(":memory:", auto_initialize=False)
    db.connect()
    return db
