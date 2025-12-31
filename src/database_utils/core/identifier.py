"""Identifier resolution for securities."""

import re
from datetime import date

from ..exceptions import IdentifierNotFoundError
from ..types import IdentifierType, SecurityId
from ..utils.logging_config import get_logger
from .connection import DatabaseConnection
from .repositories.security import SecurityRepository

logger = get_logger(__name__)

# Identifier patterns for auto-detection
# FIGI pattern: starts with BBG (Bloomberg) or similar provider codes
# ISIN pattern: country code (2 letters) + 9 alphanumeric + check digit
IDENTIFIER_PATTERNS: dict[IdentifierType, re.Pattern[str]] = {
    "FIGI": re.compile(r"^BBG[A-Z0-9]{9}$"),  # Bloomberg FIGI starts with BBG
    "ISIN": re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"),
    "CUSIP": re.compile(r"^[A-Z0-9]{9}$"),
    "SEDOL": re.compile(r"^[A-Z0-9]{7}$"),
    "JP_CODE": re.compile(r"^[0-9]{4}$"),
}

# Order of pattern detection (more specific patterns first)
DETECTION_ORDER: list[IdentifierType] = [
    "FIGI",  # 12 chars, starts with BBG (most specific)
    "ISIN",  # 12 chars, starts with country code
    "CUSIP",  # 9 chars
    "SEDOL",  # 7 chars
    "JP_CODE",  # 4 digits
]

# Ticker types to try when pattern detection fails
TICKER_TYPES: list[IdentifierType] = [
    "TICKER_YAHOO",
    "TICKER_BBG",
]


class IdentifierResolver:
    """Resolves external identifiers to internal security IDs.

    Parameters
    ----------
    db : DatabaseConnection
        Database connection to use.

    Examples
    --------
    >>> resolver = IdentifierResolver(db)
    >>> security_id = resolver.resolve("7203", "JP_CODE")
    >>> security_id = resolver.resolve_auto("US0378331005")  # Auto-detect ISIN
    """

    def __init__(self, db: DatabaseConnection) -> None:
        """Initialize the resolver."""
        self._db = db
        self._repo = SecurityRepository(db)
        logger.debug("IdentifierResolver initialized")

    def detect_identifier_type(
        self,
        identifier_value: str,
    ) -> IdentifierType | None:
        """Detect the identifier type from its value.

        Parameters
        ----------
        identifier_value : str
            Identifier value to analyze.

        Returns
        -------
        IdentifierType or None
            Detected identifier type, or None if unknown.
        """
        if not identifier_value:
            return None

        for id_type in DETECTION_ORDER:
            pattern = IDENTIFIER_PATTERNS.get(id_type)
            if pattern and pattern.match(identifier_value):
                logger.debug(
                    "Identifier type detected",
                    identifier_type=id_type,
                    identifier_value=identifier_value,
                )
                return id_type

        return None

    def resolve(
        self,
        identifier_value: str,
        identifier_type: IdentifierType | str,
        as_of: date | None = None,
    ) -> SecurityId | None:
        """Resolve an identifier to a security ID.

        Parameters
        ----------
        identifier_value : str
            Value of the identifier.
        identifier_type : IdentifierType or str
            Type of the identifier (e.g., "ISIN", "JP_CODE").
        as_of : date, optional
            Point-in-time date for validity check. Defaults to current date.

        Returns
        -------
        SecurityId or None
            Security ID if found, None otherwise.
        """
        if as_of is None:
            as_of = date.today()

        row = self._db.fetchone(
            """
            SELECT security_id
            FROM security_identifiers
            WHERE identifier_type = ?
              AND identifier_value = ?
              AND (valid_from IS NULL OR valid_from <= ?)
              AND (valid_to IS NULL OR valid_to > ?)
            ORDER BY valid_from DESC NULLS LAST
            LIMIT 1
            """,
            (identifier_type, identifier_value, as_of, as_of),
        )

        if row is None:
            logger.debug(
                "Identifier not found",
                identifier_type=identifier_type,
                identifier_value=identifier_value,
            )
            return None

        security_id: SecurityId = row["security_id"]
        logger.debug(
            "Identifier resolved",
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            security_id=security_id,
        )
        return security_id

    def resolve_auto(
        self,
        identifier_value: str,
        as_of: date | None = None,
    ) -> SecurityId | None:
        """Resolve an identifier by auto-detecting its type.

        Parameters
        ----------
        identifier_value : str
            Value of the identifier.
        as_of : date, optional
            Point-in-time date for validity check. Defaults to current date.

        Returns
        -------
        SecurityId or None
            Security ID if found, None otherwise.
        """
        # Try to detect the identifier type
        detected_type = self.detect_identifier_type(identifier_value)

        if detected_type is not None:
            result = self.resolve(identifier_value, detected_type, as_of)
            if result is not None:
                return result

        # If not found or no pattern match, try ticker types as fallback
        for ticker_type in TICKER_TYPES:
            result = self.resolve(identifier_value, ticker_type, as_of)
            if result is not None:
                return result

        return None

    def resolve_or_create(
        self,
        identifier_value: str,
        identifier_type: IdentifierType | str,
        security_name: str,
        description: str | None = None,
        asset_class: str | None = None,
        currency: str | None = None,
    ) -> SecurityId:
        """Resolve an identifier, creating a new security if not found.

        Parameters
        ----------
        identifier_value : str
            Value of the identifier.
        identifier_type : IdentifierType or str
            Type of the identifier.
        security_name : str
            Name for the new security (required for creation).
        description : str, optional
            Description for the new security.
        asset_class : str, optional
            Asset class for the new security.
        currency : str, optional
            Currency for the new security.

        Returns
        -------
        SecurityId
            Security ID (existing or newly created).

        Raises
        ------
        ValueError
            If security_name is empty and identifier doesn't exist.
        """
        # Try to resolve first
        existing_id = self.resolve(identifier_value, identifier_type)
        if existing_id is not None:
            return existing_id

        # Validate security_name for new creation
        if not security_name:
            raise ValueError(
                f"security_name is required when creating new security "
                f"for {identifier_type}={identifier_value}"
            )

        # Create new security
        security_id = self._repo.create(
            name=security_name,
            description=description,
            asset_class=asset_class,
            currency=currency,
        )

        # Add identifier
        self._repo.add_identifier(
            security_id=security_id,
            identifier_type=identifier_type,  # type: ignore[arg-type]
            identifier_value=identifier_value,
        )

        logger.info(
            "Created new security for identifier",
            security_id=security_id,
            identifier_type=identifier_type,
            identifier_value=identifier_value,
        )

        return security_id

    def resolve_or_raise(
        self,
        identifier_value: str,
        identifier_type: IdentifierType | str,
        as_of: date | None = None,
    ) -> SecurityId:
        """Resolve an identifier, raising an error if not found.

        Parameters
        ----------
        identifier_value : str
            Value of the identifier.
        identifier_type : IdentifierType or str
            Type of the identifier.
        as_of : date, optional
            Point-in-time date for validity check.

        Returns
        -------
        SecurityId
            Security ID.

        Raises
        ------
        IdentifierNotFoundError
            If identifier is not found.
        """
        result = self.resolve(identifier_value, identifier_type, as_of)

        if result is None:
            raise IdentifierNotFoundError(str(identifier_type), identifier_value)

        return result
