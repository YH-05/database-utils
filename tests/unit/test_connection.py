"""Tests for database connection management."""

import tempfile
from pathlib import Path

import pytest

from database_utils import (
    DatabaseConnection,
    DatabaseError,
    TransactionError,
)


class TestDatabaseConnectionBasic:
    """Tests for basic DatabaseConnection functionality."""

    def test_create_in_memory_connection(self) -> None:
        """Should create an in-memory database connection."""
        db = DatabaseConnection(":memory:")

        assert db.db_path == ":memory:"
        assert not db.is_connected

    def test_create_file_connection(self) -> None:
        """Should create a file-based database connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DatabaseConnection(db_path)

            assert db.db_path == db_path
            assert not db.is_connected

    def test_connect_creates_connection(self) -> None:
        """Connect should establish database connection."""
        db = DatabaseConnection(":memory:")
        db.connect()

        assert db.is_connected

    def test_close_disconnects(self) -> None:
        """Close should disconnect from database."""
        db = DatabaseConnection(":memory:")
        db.connect()
        db.close()

        assert not db.is_connected

    def test_context_manager_connects_and_closes(self) -> None:
        """Context manager should connect on enter and close on exit."""
        db = DatabaseConnection(":memory:")

        with db:
            assert db.is_connected

        assert not db.is_connected

    def test_auto_initialize_on_connect(self) -> None:
        """Should auto-initialize schema on connect by default."""
        db = DatabaseConnection(":memory:")
        db.connect()

        # Check that tables exist
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='securities'"
        )
        result = cursor.fetchone()

        assert result is not None

    def test_skip_auto_initialize(self) -> None:
        """Should skip auto-initialize when disabled."""
        db = DatabaseConnection(":memory:", auto_initialize=False)
        db.connect()

        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='securities'"
        )
        result = cursor.fetchone()

        assert result is None

    def test_multiple_connects_idempotent(self) -> None:
        """Multiple connect calls should be idempotent."""
        db = DatabaseConnection(":memory:")
        db.connect()
        db.connect()  # Should not raise
        db.connect()  # Should not raise

        assert db.is_connected


class TestDatabaseConnectionExecute:
    """Tests for SQL execution."""

    def test_execute_select(self, memory_db: DatabaseConnection) -> None:
        """Should execute SELECT queries."""
        cursor = memory_db.execute("SELECT 1 + 1 as result")
        result = cursor.fetchone()

        assert result["result"] == 2

    def test_execute_insert(self, memory_db: DatabaseConnection) -> None:
        """Should execute INSERT statements."""
        memory_db.execute(
            "INSERT INTO securities (name) VALUES (?)",
            ("Test Security",),
        )
        memory_db.commit()

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 1

    def test_execute_with_params(self, memory_db: DatabaseConnection) -> None:
        """Should execute with positional parameters."""
        memory_db.execute(
            "INSERT INTO securities (name, currency) VALUES (?, ?)",
            ("Toyota", "JPY"),
        )
        memory_db.commit()

        cursor = memory_db.execute(
            "SELECT * FROM securities WHERE name = ?",
            ("Toyota",),
        )
        row = cursor.fetchone()

        assert row["name"] == "Toyota"
        assert row["currency"] == "JPY"

    def test_execute_with_dict_params(self, memory_db: DatabaseConnection) -> None:
        """Should execute with named parameters."""
        memory_db.execute(
            "INSERT INTO securities (name, currency) VALUES (:name, :currency)",
            {"name": "Apple", "currency": "USD"},
        )
        memory_db.commit()

        cursor = memory_db.execute(
            "SELECT * FROM securities WHERE name = :name",
            {"name": "Apple"},
        )
        row = cursor.fetchone()

        assert row["name"] == "Apple"
        assert row["currency"] == "USD"

    def test_executemany(self, memory_db: DatabaseConnection) -> None:
        """Should execute with multiple parameter sets."""
        data = [
            ("Security A",),
            ("Security B",),
            ("Security C",),
        ]
        memory_db.executemany(
            "INSERT INTO securities (name) VALUES (?)",
            data,
        )
        memory_db.commit()

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 3

    def test_fetchone(self, memory_db: DatabaseConnection) -> None:
        """Should fetch single row."""
        memory_db.execute(
            "INSERT INTO securities (name) VALUES (?)",
            ("Test",),
        )
        memory_db.commit()

        row = memory_db.fetchone("SELECT * FROM securities WHERE name = ?", ("Test",))
        assert row is not None
        assert row["name"] == "Test"

    def test_fetchone_returns_none(self, memory_db: DatabaseConnection) -> None:
        """Should return None when no rows match."""
        row = memory_db.fetchone(
            "SELECT * FROM securities WHERE name = ?",
            ("NonExistent",),
        )
        assert row is None

    def test_fetchall(self, memory_db: DatabaseConnection) -> None:
        """Should fetch all rows."""
        data = [("A",), ("B",), ("C",)]
        memory_db.executemany("INSERT INTO securities (name) VALUES (?)", data)
        memory_db.commit()

        rows = memory_db.fetchall("SELECT name FROM securities ORDER BY name")
        assert len(rows) == 3
        assert [r["name"] for r in rows] == ["A", "B", "C"]

    def test_execute_auto_connects(self) -> None:
        """Execute should auto-connect if not connected."""
        db = DatabaseConnection(":memory:")
        assert not db.is_connected

        db.execute("SELECT 1")
        assert db.is_connected


class TestDatabaseConnectionTransaction:
    """Tests for transaction management."""

    def test_transaction_commits_on_success(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Transaction should commit on success."""
        with memory_db.transaction():
            memory_db.execute(
                "INSERT INTO securities (name) VALUES (?)",
                ("Test",),
            )

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 1

    def test_transaction_rollbacks_on_exception(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Transaction should rollback on exception."""
        with pytest.raises(TransactionError), memory_db.transaction():
            memory_db.execute(
                "INSERT INTO securities (name) VALUES (?)",
                ("Test",),
            )
            raise ValueError("Simulated error")

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 0

    def test_nested_operations_in_transaction(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Multiple operations should be atomic in transaction."""
        with memory_db.transaction():
            memory_db.execute(
                "INSERT INTO securities (name) VALUES (?)",
                ("Security 1",),
            )
            memory_db.execute(
                "INSERT INTO securities (name) VALUES (?)",
                ("Security 2",),
            )

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 2

    def test_transaction_returns_self(self, memory_db: DatabaseConnection) -> None:
        """Transaction context should yield the connection."""
        with memory_db.transaction() as conn:
            assert conn is memory_db

    def test_manual_commit(self, memory_db: DatabaseConnection) -> None:
        """Should be able to manually commit."""
        memory_db.execute(
            "INSERT INTO securities (name) VALUES (?)",
            ("Test",),
        )
        memory_db.commit()

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 1

    def test_manual_rollback(self, memory_db: DatabaseConnection) -> None:
        """Should be able to manually rollback."""
        memory_db.execute(
            "INSERT INTO securities (name) VALUES (?)",
            ("Test",),
        )
        memory_db.rollback()

        cursor = memory_db.execute("SELECT COUNT(*) as count FROM securities")
        assert cursor.fetchone()["count"] == 0


class TestDatabaseConnectionErrors:
    """Tests for error handling."""

    def test_execute_invalid_sql_raises(self, memory_db: DatabaseConnection) -> None:
        """Invalid SQL should raise DatabaseError."""
        with pytest.raises(DatabaseError):
            memory_db.execute("INVALID SQL STATEMENT")

    def test_connection_repr(self) -> None:
        """Should have readable repr."""
        db = DatabaseConnection(":memory:")
        assert "disconnected" in repr(db)

        db.connect()
        assert "connected" in repr(db)


class TestDatabaseConnectionPersistence:
    """Tests for file-based database persistence."""

    def test_creates_database_file(self) -> None:
        """Should create database file on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            assert not db_path.exists()

            with DatabaseConnection(db_path):
                pass

            assert db_path.exists()

    def test_data_persists_across_connections(self) -> None:
        """Data should persist across connections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # First connection: insert data
            with DatabaseConnection(db_path) as db:
                db.execute(
                    "INSERT INTO securities (name) VALUES (?)",
                    ("Persistent",),
                )
                db.commit()

            # Second connection: verify data exists
            with DatabaseConnection(db_path) as db:
                row = db.fetchone(
                    "SELECT * FROM securities WHERE name = ?",
                    ("Persistent",),
                )
                assert row is not None
                assert row["name"] == "Persistent"

    def test_wal_mode_enabled(self) -> None:
        """WAL mode should be enabled for file databases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            with DatabaseConnection(db_path) as db:
                cursor = db.execute("PRAGMA journal_mode")
                mode = cursor.fetchone()[0]
                assert mode.lower() == "wal"
