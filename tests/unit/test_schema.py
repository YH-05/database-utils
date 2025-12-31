"""Tests for database schema initialization."""

import pytest

from database_utils import DatabaseConnection, DatabaseError
from database_utils.core.schema import (
    DEFAULT_DATA_SOURCES,
    DEFAULT_IDENTIFIER_TYPES,
    get_schema_version,
    initialize_schema,
    set_schema_version,
)


class TestSchemaInitialization:
    """Tests for schema initialization."""

    def test_initialize_schema_creates_tables(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema initialization should create all required tables."""
        initialize_schema(empty_db.connection)

        expected_tables = [
            "securities",
            "identifier_types",
            "security_identifiers",
            "data_sources",
            "price_data",
            "factor_definitions",
            "factor_data",
            "trades",
            "portfolio_holdings",
        ]

        cursor = empty_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        actual_tables = [row["name"] for row in cursor.fetchall()]

        for table in expected_tables:
            assert table in actual_tables, f"Table {table} should exist"

    def test_initialize_schema_creates_views(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema initialization should create views."""
        initialize_schema(empty_db.connection)

        cursor = empty_db.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        )
        views = [row["name"] for row in cursor.fetchall()]

        assert "best_prices" in views
        assert "latest_factors" in views

    def test_initialize_schema_creates_indexes(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema initialization should create indexes."""
        initialize_schema(empty_db.connection)

        cursor = empty_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = [row["name"] for row in cursor.fetchall()]

        assert len(indexes) >= 5, "Should create at least 5 custom indexes"
        assert "idx_security_identifiers_value" in indexes

    def test_initialize_schema_inserts_identifier_types(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema initialization should insert default identifier types."""
        initialize_schema(empty_db.connection)

        cursor = empty_db.execute("SELECT COUNT(*) as count FROM identifier_types")
        count = cursor.fetchone()["count"]

        assert count == len(DEFAULT_IDENTIFIER_TYPES)

        cursor = empty_db.execute(
            "SELECT type_code FROM identifier_types ORDER BY type_code"
        )
        types = [row["type_code"] for row in cursor.fetchall()]

        assert "ISIN" in types
        assert "JP_CODE" in types
        assert "TICKER_YAHOO" in types

    def test_initialize_schema_inserts_data_sources(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema initialization should insert default data sources."""
        initialize_schema(empty_db.connection)

        cursor = empty_db.execute("SELECT COUNT(*) as count FROM data_sources")
        count = cursor.fetchone()["count"]

        assert count == len(DEFAULT_DATA_SOURCES)

        cursor = empty_db.execute(
            "SELECT source_code FROM data_sources ORDER BY priority"
        )
        sources = [row["source_code"] for row in cursor.fetchall()]

        assert "YFINANCE" in sources
        assert "MANUAL_ENTRY" in sources

    def test_initialize_schema_is_idempotent(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema initialization should be idempotent."""
        initialize_schema(empty_db.connection)
        initialize_schema(empty_db.connection)  # Should not raise

        cursor = empty_db.execute("SELECT COUNT(*) as count FROM identifier_types")
        count = cursor.fetchone()["count"]

        assert count == len(DEFAULT_IDENTIFIER_TYPES)

    def test_foreign_key_constraints_enabled(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Foreign key constraints should be enabled."""
        cursor = memory_db.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()[0]

        assert result == 1, "Foreign keys should be enabled"


class TestSchemaVersion:
    """Tests for schema version management."""

    def test_get_schema_version_returns_zero_initially(
        self, empty_db: DatabaseConnection
    ) -> None:
        """Schema version should be 0 initially."""
        version = get_schema_version(empty_db.connection)
        assert version == 0

    def test_set_and_get_schema_version(self, empty_db: DatabaseConnection) -> None:
        """Should be able to set and get schema version."""
        set_schema_version(empty_db.connection, 1)
        assert get_schema_version(empty_db.connection) == 1

        set_schema_version(empty_db.connection, 5)
        assert get_schema_version(empty_db.connection) == 5


class TestTableConstraints:
    """Tests for table constraints."""

    def test_securities_allows_insert(self, memory_db: DatabaseConnection) -> None:
        """Should be able to insert a security."""
        memory_db.execute(
            "INSERT INTO securities (name, currency) VALUES (?, ?)",
            ("Toyota Motor Corp", "JPY"),
        )
        memory_db.commit()

        cursor = memory_db.execute(
            "SELECT * FROM securities WHERE name = ?", ("Toyota Motor Corp",)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row["name"] == "Toyota Motor Corp"
        assert row["currency"] == "JPY"

    def test_security_identifiers_foreign_key(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Security identifiers should enforce foreign key to securities."""
        with pytest.raises(DatabaseError, match="FOREIGN KEY constraint failed"):
            memory_db.execute(
                """
                INSERT INTO security_identifiers
                (security_id, identifier_type, identifier_value)
                VALUES (?, ?, ?)
                """,
                (9999, "ISIN", "JP1234567890"),
            )

    def test_price_data_unique_constraint(self, memory_db: DatabaseConnection) -> None:
        """Price data should enforce unique constraint on security+source+date."""
        # Insert a security first
        memory_db.execute(
            "INSERT INTO securities (name) VALUES (?)",
            ("Test Security",),
        )
        security_id = memory_db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Get a data source
        cursor = memory_db.execute(
            "SELECT source_id FROM data_sources WHERE source_code = ?",
            ("YFINANCE",),
        )
        source_id = cursor.fetchone()["source_id"]

        # Insert price data
        memory_db.execute(
            """
            INSERT INTO price_data (security_id, source_id, price_date, close)
            VALUES (?, ?, ?, ?)
            """,
            (security_id, source_id, "2025-01-01", 100.0),
        )
        memory_db.commit()

        # Attempt duplicate insert should fail
        with pytest.raises(DatabaseError, match="UNIQUE constraint failed"):
            memory_db.execute(
                """
                INSERT INTO price_data (security_id, source_id, price_date, close)
                VALUES (?, ?, ?, ?)
                """,
                (security_id, source_id, "2025-01-01", 101.0),
            )

    def test_data_sources_type_constraint(self, memory_db: DatabaseConnection) -> None:
        """Data sources should enforce source_type check constraint."""
        with pytest.raises(DatabaseError, match="CHECK constraint failed"):
            memory_db.execute(
                """
                INSERT INTO data_sources (source_code, source_type, priority)
                VALUES (?, ?, ?)
                """,
                ("INVALID", "INVALID_TYPE", 100),
            )

    def test_trades_type_constraint(self, memory_db: DatabaseConnection) -> None:
        """Trades should enforce trade_type check constraint."""
        # Insert a security first
        memory_db.execute(
            "INSERT INTO securities (name) VALUES (?)",
            ("Test Security",),
        )
        security_id = memory_db.execute("SELECT last_insert_rowid()").fetchone()[0]

        with pytest.raises(DatabaseError, match="CHECK constraint failed"):
            memory_db.execute(
                """
                INSERT INTO trades (security_id, trade_type, trade_date, quantity, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (security_id, "INVALID_TYPE", "2025-01-01", 100, 1000),
            )
