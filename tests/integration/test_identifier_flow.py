"""Integration tests for identifier resolution flow."""

from datetime import date

import pytest

from database_utils import (
    DatabaseConnection,
    IdentifierNotFoundError,
    IdentifierResolver,
    SecurityRepository,
)


class TestIdentifierResolutionFlow:
    """End-to-end tests for identifier resolution."""

    def test_create_security_add_identifiers_resolve(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Full flow: create security, add identifiers, resolve by various types."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        # Create a security
        security_id = repo.create(
            name="Toyota Motor Corp",
            description="Japanese automobile manufacturer",
            asset_class="equity",
            currency="JPY",
        )

        # Add multiple identifiers
        repo.add_identifier(security_id, "JP_CODE", "7203", is_primary=True)
        repo.add_identifier(security_id, "ISIN", "JP3633400001")
        repo.add_identifier(security_id, "TICKER_YAHOO", "7203.T")

        # Resolve by each identifier type
        assert resolver.resolve("7203", "JP_CODE") == security_id
        assert resolver.resolve("JP3633400001", "ISIN") == security_id
        assert resolver.resolve("7203.T", "TICKER_YAHOO") == security_id

        # Auto-resolve
        assert resolver.resolve_auto("7203") == security_id
        assert resolver.resolve_auto("JP3633400001") == security_id

    def test_resolve_or_create_new_security(
        self, memory_db: DatabaseConnection
    ) -> None:
        """resolve_or_create should create new security when not found."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        # Security doesn't exist yet
        security_id = resolver.resolve_or_create(
            identifier_value="AAPL",
            identifier_type="TICKER_YAHOO",
            security_name="Apple Inc",
            currency="USD",
        )

        # Verify security was created
        security = repo.get(security_id)
        assert security is not None
        assert security["name"] == "Apple Inc"
        assert security["currency"] == "USD"

        # Verify identifier was added
        identifiers = repo.get_identifiers(security_id)
        assert len(identifiers) == 1
        assert identifiers[0]["identifier_value"] == "AAPL"

        # Subsequent calls should return same ID
        same_id = resolver.resolve_or_create(
            identifier_value="AAPL",
            identifier_type="TICKER_YAHOO",
            security_name="Should not change",
        )
        assert same_id == security_id

    def test_point_in_time_resolution(self, memory_db: DatabaseConnection) -> None:
        """Identifier resolution should respect validity periods."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Test Corp")

        # Add old ticker (expired)
        repo.add_identifier(
            security_id,
            "TICKER_YAHOO",
            "OLD.T",
            valid_from=date(2020, 1, 1),
            valid_to=date(2023, 12, 31),
        )

        # Add new ticker (current)
        repo.add_identifier(
            security_id,
            "TICKER_YAHOO",
            "NEW.T",
            valid_from=date(2024, 1, 1),
        )

        # Resolve at different points in time
        assert (
            resolver.resolve("OLD.T", "TICKER_YAHOO", as_of=date(2022, 6, 1))
            == security_id
        )
        assert (
            resolver.resolve("NEW.T", "TICKER_YAHOO", as_of=date(2024, 6, 1))
            == security_id
        )

        # Old ticker not valid in 2024
        assert resolver.resolve("OLD.T", "TICKER_YAHOO", as_of=date(2024, 6, 1)) is None

        # New ticker not valid in 2022
        assert resolver.resolve("NEW.T", "TICKER_YAHOO", as_of=date(2022, 6, 1)) is None

    def test_multiple_securities_with_different_identifiers(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Different securities should have different identifiers."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        # Create multiple securities
        toyota_id = repo.create(name="Toyota Motor Corp", currency="JPY")
        honda_id = repo.create(name="Honda Motor Co", currency="JPY")
        apple_id = repo.create(name="Apple Inc", currency="USD")

        # Add identifiers
        repo.add_identifier(toyota_id, "JP_CODE", "7203")
        repo.add_identifier(honda_id, "JP_CODE", "7267")
        repo.add_identifier(apple_id, "TICKER_YAHOO", "AAPL")
        repo.add_identifier(apple_id, "ISIN", "US0378331005")

        # Resolve each
        assert resolver.resolve("7203", "JP_CODE") == toyota_id
        assert resolver.resolve("7267", "JP_CODE") == honda_id
        assert resolver.resolve("AAPL", "TICKER_YAHOO") == apple_id
        assert resolver.resolve_auto("US0378331005") == apple_id

    def test_resolve_or_raise_raises_when_not_found(
        self, memory_db: DatabaseConnection
    ) -> None:
        """resolve_or_raise should raise IdentifierNotFoundError."""
        resolver = IdentifierResolver(memory_db)

        with pytest.raises(IdentifierNotFoundError) as exc_info:
            resolver.resolve_or_raise("NONEXISTENT", "TICKER_YAHOO")

        assert exc_info.value.identifier_type == "TICKER_YAHOO"
        assert exc_info.value.identifier_value == "NONEXISTENT"

    def test_search_securities(self, memory_db: DatabaseConnection) -> None:
        """Search should find securities by name pattern or identifier."""
        repo = SecurityRepository(memory_db)

        # Create securities
        toyota_id = repo.create(name="Toyota Motor Corp")
        honda_id = repo.create(name="Honda Motor Co")
        sony_id = repo.create(name="Sony Group Corp")

        repo.add_identifier(toyota_id, "JP_CODE", "7203")
        repo.add_identifier(honda_id, "JP_CODE", "7267")

        # Search by name pattern
        motor_results = repo.search(name_pattern="%Motor%")
        assert len(motor_results) == 2

        # Search by identifier
        code_results = repo.search(identifier_value="7203")
        assert len(code_results) == 1
        assert code_results[0]["name"] == "Toyota Motor Corp"


class TestTransactionBehavior:
    """Tests for transaction behavior in identifier operations."""

    def test_create_security_with_identifier_atomic(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Creating security with identifier should be atomic."""
        resolver = IdentifierResolver(memory_db)
        repo = SecurityRepository(memory_db)

        # Use resolve_or_create which creates both security and identifier
        security_id = resolver.resolve_or_create(
            identifier_value="7203",
            identifier_type="JP_CODE",
            security_name="Toyota Motor Corp",
        )

        # Both should exist
        security = repo.get(security_id)
        assert security is not None

        identifiers = repo.get_identifiers(security_id)
        assert len(identifiers) == 1

        # Should be resolvable
        assert resolver.resolve("7203", "JP_CODE") == security_id
