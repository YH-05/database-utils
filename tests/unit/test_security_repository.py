"""Tests for SecurityRepository."""

from datetime import date

import pytest

from database_utils import DatabaseConnection
from database_utils.core.repositories.security import SecurityRepository
from database_utils.exceptions import DuplicateSecurityError


class TestSecurityRepositoryCreate:
    """Tests for SecurityRepository.create()."""

    def test_create_security_returns_id(self, memory_db: DatabaseConnection) -> None:
        """Creating a security should return a positive security_id."""
        repo = SecurityRepository(memory_db)

        security_id = repo.create(name="Toyota Motor Corp")

        assert security_id > 0

    def test_create_security_with_all_fields(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Creating a security with all fields should store them."""
        repo = SecurityRepository(memory_db)

        security_id = repo.create(
            name="Apple Inc",
            description="Technology company",
            asset_class="equity",
            currency="USD",
        )

        security = repo.get(security_id)
        assert security is not None
        assert security["name"] == "Apple Inc"
        assert security["description"] == "Technology company"
        assert security["asset_class"] == "equity"
        assert security["currency"] == "USD"

    def test_create_multiple_securities(self, memory_db: DatabaseConnection) -> None:
        """Creating multiple securities should return unique IDs."""
        repo = SecurityRepository(memory_db)

        id1 = repo.create(name="Security A")
        id2 = repo.create(name="Security B")
        id3 = repo.create(name="Security C")

        assert len({id1, id2, id3}) == 3


class TestSecurityRepositoryGet:
    """Tests for SecurityRepository.get()."""

    def test_get_existing_security(self, memory_db: DatabaseConnection) -> None:
        """Getting an existing security should return its data."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Test Security", currency="JPY")

        security = repo.get(security_id)

        assert security is not None
        assert security["security_id"] == security_id
        assert security["name"] == "Test Security"
        assert security["currency"] == "JPY"

    def test_get_nonexistent_security(self, memory_db: DatabaseConnection) -> None:
        """Getting a non-existent security should return None."""
        repo = SecurityRepository(memory_db)

        security = repo.get(9999)

        assert security is None


class TestSecurityRepositoryIdentifiers:
    """Tests for identifier management."""

    def test_add_identifier(self, memory_db: DatabaseConnection) -> None:
        """Adding an identifier should associate it with the security."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Toyota")

        repo.add_identifier(
            security_id=security_id,
            identifier_type="JP_CODE",
            identifier_value="7203",
        )

        identifiers = repo.get_identifiers(security_id)
        assert len(identifiers) == 1
        assert identifiers[0]["identifier_type"] == "JP_CODE"
        assert identifiers[0]["identifier_value"] == "7203"

    def test_add_multiple_identifiers(self, memory_db: DatabaseConnection) -> None:
        """Adding multiple identifiers should store all of them."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Apple Inc")

        repo.add_identifier(security_id, "ISIN", "US0378331005")
        repo.add_identifier(security_id, "CUSIP", "037833100")
        repo.add_identifier(security_id, "TICKER_YAHOO", "AAPL")

        identifiers = repo.get_identifiers(security_id)
        assert len(identifiers) == 3
        types = {i["identifier_type"] for i in identifiers}
        assert types == {"ISIN", "CUSIP", "TICKER_YAHOO"}

    def test_add_identifier_with_validity_period(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Adding an identifier with validity period should store dates."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Test Security")

        repo.add_identifier(
            security_id=security_id,
            identifier_type="TICKER_YAHOO",
            identifier_value="OLD.T",
            valid_from=date(2020, 1, 1),
            valid_to=date(2023, 12, 31),
        )

        identifiers = repo.get_identifiers(security_id)
        assert len(identifiers) == 1
        assert identifiers[0]["valid_from"] == date(2020, 1, 1)
        assert identifiers[0]["valid_to"] == date(2023, 12, 31)

    def test_add_primary_identifier(self, memory_db: DatabaseConnection) -> None:
        """Adding a primary identifier should mark it as primary."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Test Security")

        repo.add_identifier(
            security_id=security_id,
            identifier_type="ISIN",
            identifier_value="JP1234567890",
            is_primary=True,
        )

        identifiers = repo.get_identifiers(security_id)
        assert identifiers[0]["is_primary"] is True

    def test_add_duplicate_identifier_raises(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Adding a duplicate identifier should raise DuplicateSecurityError."""
        repo = SecurityRepository(memory_db)
        id1 = repo.create(name="Security 1")
        id2 = repo.create(name="Security 2")

        repo.add_identifier(id1, "ISIN", "US0378331005")

        with pytest.raises(DuplicateSecurityError):
            repo.add_identifier(id2, "ISIN", "US0378331005")


class TestSecurityRepositoryGetByIdentifier:
    """Tests for SecurityRepository.get_by_identifier()."""

    def test_get_by_identifier_exact_match(self, memory_db: DatabaseConnection) -> None:
        """Getting by identifier should return the correct security."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Toyota Motor Corp")
        repo.add_identifier(security_id, "JP_CODE", "7203")

        result = repo.get_by_identifier("JP_CODE", "7203")

        assert result is not None
        assert result["security_id"] == security_id
        assert result["name"] == "Toyota Motor Corp"

    def test_get_by_identifier_not_found(self, memory_db: DatabaseConnection) -> None:
        """Getting by non-existent identifier should return None."""
        repo = SecurityRepository(memory_db)

        result = repo.get_by_identifier("JP_CODE", "9999")

        assert result is None

    def test_get_by_identifier_point_in_time(
        self, memory_db: DatabaseConnection
    ) -> None:
        """Getting by identifier with as_of date should respect validity."""
        repo = SecurityRepository(memory_db)
        security_id = repo.create(name="Test Security")

        # Old identifier valid until 2023-12-31
        repo.add_identifier(
            security_id,
            "TICKER_YAHOO",
            "OLD.T",
            valid_from=date(2020, 1, 1),
            valid_to=date(2023, 12, 31),
        )
        # New identifier valid from 2024-01-01
        repo.add_identifier(
            security_id,
            "TICKER_YAHOO",
            "NEW.T",
            valid_from=date(2024, 1, 1),
        )

        # Query in old period
        result_old = repo.get_by_identifier(
            "TICKER_YAHOO",
            "OLD.T",
            as_of=date(2023, 6, 15),
        )
        assert result_old is not None

        # Query in new period
        result_new = repo.get_by_identifier(
            "TICKER_YAHOO",
            "NEW.T",
            as_of=date(2024, 6, 15),
        )
        assert result_new is not None

        # Old identifier not valid in new period
        result_expired = repo.get_by_identifier(
            "TICKER_YAHOO",
            "OLD.T",
            as_of=date(2024, 6, 15),
        )
        assert result_expired is None


class TestSecurityRepositorySearch:
    """Tests for SecurityRepository.search()."""

    def test_search_by_name_pattern(self, memory_db: DatabaseConnection) -> None:
        """Searching by name pattern should return matching securities."""
        repo = SecurityRepository(memory_db)
        repo.create(name="Toyota Motor Corp")
        repo.create(name="Sony Group Corp")
        repo.create(name="Honda Motor Co")

        results = repo.search(name_pattern="%Motor%")

        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"Toyota Motor Corp", "Honda Motor Co"}

    def test_search_by_identifier(self, memory_db: DatabaseConnection) -> None:
        """Searching by identifier value should return matching securities."""
        repo = SecurityRepository(memory_db)
        id1 = repo.create(name="Toyota")
        id2 = repo.create(name="Sony")
        repo.add_identifier(id1, "JP_CODE", "7203")
        repo.add_identifier(id2, "JP_CODE", "6758")

        results = repo.search(identifier_value="7203")

        assert len(results) == 1
        assert results[0]["name"] == "Toyota"

    def test_search_empty_result(self, memory_db: DatabaseConnection) -> None:
        """Searching with no matches should return empty list."""
        repo = SecurityRepository(memory_db)
        repo.create(name="Toyota")

        results = repo.search(name_pattern="%Apple%")

        assert results == []
