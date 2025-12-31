"""Tests for IdentifierResolver."""

from datetime import date

import pytest

from database_utils import DatabaseConnection
from database_utils.core.identifier import IdentifierResolver
from database_utils.core.repositories.security import SecurityRepository
from database_utils.exceptions import IdentifierNotFoundError


class TestIdentifierResolverDetectType:
    """Tests for IdentifierResolver.detect_identifier_type()."""

    def test_detect_isin(self, memory_db: DatabaseConnection) -> None:
        """Should detect ISIN format (12 chars, country code + 9 + check)."""
        resolver = IdentifierResolver(memory_db)

        assert resolver.detect_identifier_type("US0378331005") == "ISIN"
        assert resolver.detect_identifier_type("JP3633400001") == "ISIN"
        assert resolver.detect_identifier_type("GB00B03MLX29") == "ISIN"

    def test_detect_cusip(self, memory_db: DatabaseConnection) -> None:
        """Should detect CUSIP format (9 alphanumeric chars)."""
        resolver = IdentifierResolver(memory_db)

        assert resolver.detect_identifier_type("037833100") == "CUSIP"
        assert resolver.detect_identifier_type("594918104") == "CUSIP"

    def test_detect_sedol(self, memory_db: DatabaseConnection) -> None:
        """Should detect SEDOL format (7 alphanumeric chars)."""
        resolver = IdentifierResolver(memory_db)

        assert resolver.detect_identifier_type("2046251") == "SEDOL"
        assert resolver.detect_identifier_type("B03MLX2") == "SEDOL"

    def test_detect_jp_code(self, memory_db: DatabaseConnection) -> None:
        """Should detect JP_CODE format (4 digits)."""
        resolver = IdentifierResolver(memory_db)

        assert resolver.detect_identifier_type("7203") == "JP_CODE"
        assert resolver.detect_identifier_type("6758") == "JP_CODE"
        assert resolver.detect_identifier_type("9984") == "JP_CODE"

    def test_detect_figi(self, memory_db: DatabaseConnection) -> None:
        """Should detect FIGI format (12 chars, 3 letters + 9 alphanumeric)."""
        resolver = IdentifierResolver(memory_db)

        assert resolver.detect_identifier_type("BBG000B9XRY4") == "FIGI"
        assert resolver.detect_identifier_type("BBG000BPH459") == "FIGI"

    def test_detect_unknown_returns_none(self, memory_db: DatabaseConnection) -> None:
        """Unknown patterns should return None."""
        resolver = IdentifierResolver(memory_db)

        assert resolver.detect_identifier_type("AAPL") is None
        assert resolver.detect_identifier_type("7203.T") is None
        assert resolver.detect_identifier_type("") is None
        assert resolver.detect_identifier_type("12345") is None  # 5 digits, not 4


class TestIdentifierResolverResolve:
    """Tests for IdentifierResolver.resolve()."""

    def test_resolve_existing_identifier(self, memory_db: DatabaseConnection) -> None:
        """Should resolve an existing identifier to security_id."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Toyota Motor Corp")
        repo.add_identifier(security_id, "JP_CODE", "7203")

        result = resolver.resolve("7203", "JP_CODE")

        assert result == security_id

    def test_resolve_nonexistent_returns_none(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Should return None for non-existent identifier."""
        resolver = IdentifierResolver(memory_db)

        result = resolver.resolve("9999", "JP_CODE")

        assert result is None

    def test_resolve_with_point_in_time(self, memory_db: DatabaseConnection) -> None:
        """Should respect validity period when resolving."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Test Security")
        repo.add_identifier(
            security_id,
            "TICKER_YAHOO",
            "OLD.T",
            valid_from=date(2020, 1, 1),
            valid_to=date(2023, 12, 31),
        )

        # Within validity period
        result_valid = resolver.resolve("OLD.T", "TICKER_YAHOO", as_of=date(2022, 6, 1))
        assert result_valid == security_id

        # After validity period
        result_expired = resolver.resolve(
            "OLD.T", "TICKER_YAHOO", as_of=date(2024, 1, 1)
        )
        assert result_expired is None


class TestIdentifierResolverResolveAuto:
    """Tests for IdentifierResolver.resolve_auto()."""

    def test_resolve_auto_detects_isin(self, memory_db: DatabaseConnection) -> None:
        """Should auto-detect ISIN and resolve."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Apple Inc")
        repo.add_identifier(security_id, "ISIN", "US0378331005")

        result = resolver.resolve_auto("US0378331005")

        assert result == security_id

    def test_resolve_auto_detects_jp_code(self, memory_db: DatabaseConnection) -> None:
        """Should auto-detect JP_CODE and resolve."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Toyota Motor Corp")
        repo.add_identifier(security_id, "JP_CODE", "7203")

        result = resolver.resolve_auto("7203")

        assert result == security_id

    def test_resolve_auto_tries_ticker_as_fallback(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Should try ticker types when pattern detection fails."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Apple Inc")
        repo.add_identifier(security_id, "TICKER_YAHOO", "AAPL")

        result = resolver.resolve_auto("AAPL")

        assert result == security_id

    def test_resolve_auto_returns_none_when_not_found(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Should return None when identifier not found."""
        resolver = IdentifierResolver(memory_db)

        result = resolver.resolve_auto("UNKNOWN_TICKER")

        assert result is None


class TestIdentifierResolverResolveOrCreate:
    """Tests for IdentifierResolver.resolve_or_create()."""

    def test_resolve_or_create_returns_existing(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Should return existing security if identifier exists."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        existing_id = repo.create(name="Toyota")
        repo.add_identifier(existing_id, "JP_CODE", "7203")

        result = resolver.resolve_or_create(
            "7203", "JP_CODE", security_name="Toyota Motor Corp"
        )

        assert result == existing_id

    def test_resolve_or_create_creates_new(self, memory_db: DatabaseConnection) -> None:
        """Should create new security if identifier doesn't exist."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        result = resolver.resolve_or_create(
            "7203",
            "JP_CODE",
            security_name="Toyota Motor Corp",
            currency="JPY",
        )

        assert result > 0

        # Verify security was created
        security = repo.get(result)
        assert security is not None
        assert security["name"] == "Toyota Motor Corp"
        assert security["currency"] == "JPY"

        # Verify identifier was added
        identifiers = repo.get_identifiers(result)
        assert len(identifiers) == 1
        assert identifiers[0]["identifier_value"] == "7203"

    def test_resolve_or_create_without_name_raises(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Should raise ValueError if security_name is not provided for new."""
        resolver = IdentifierResolver(memory_db)

        with pytest.raises(ValueError, match="security_name is required"):
            resolver.resolve_or_create("7203", "JP_CODE", security_name="")


class TestIdentifierResolverResolveOrRaise:
    """Tests for IdentifierResolver.resolve_or_raise()."""

    def test_resolve_or_raise_returns_id(self, memory_db: DatabaseConnection) -> None:
        """Should return security_id when found."""
        repo = SecurityRepository(memory_db)
        resolver = IdentifierResolver(memory_db)

        security_id = repo.create(name="Toyota")
        repo.add_identifier(security_id, "JP_CODE", "7203")

        result = resolver.resolve_or_raise("7203", "JP_CODE")

        assert result == security_id

    def test_resolve_or_raise_raises_when_not_found(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Should raise IdentifierNotFoundError when not found."""
        resolver = IdentifierResolver(memory_db)

        with pytest.raises(IdentifierNotFoundError) as exc_info:
            resolver.resolve_or_raise("9999", "JP_CODE")

        assert exc_info.value.identifier_type == "JP_CODE"
        assert exc_info.value.identifier_value == "9999"
