"""Security repository for managing securities and identifiers."""

from datetime import date

from ...exceptions import DuplicateSecurityError
from ...types import IdentifierType, SecurityDict, SecurityId, SecurityIdentifierDict
from ...utils.logging_config import get_logger
from ..connection import DatabaseConnection

logger = get_logger(__name__)


class SecurityRepository:
    """Repository for managing securities and their identifiers.

    Parameters
    ----------
    db : DatabaseConnection
        Database connection to use.

    Examples
    --------
    >>> repo = SecurityRepository(db)
    >>> security_id = repo.create(name="Toyota Motor Corp", currency="JPY")
    >>> repo.add_identifier(security_id, "JP_CODE", "7203")
    >>> security = repo.get_by_identifier("JP_CODE", "7203")
    """

    def __init__(self, db: DatabaseConnection) -> None:
        """Initialize the repository."""
        self._db = db
        logger.debug("SecurityRepository initialized")

    def create(
        self,
        name: str,
        description: str | None = None,
        asset_class: str | None = None,
        currency: str | None = None,
    ) -> SecurityId:
        """Create a new security.

        Parameters
        ----------
        name : str
            Name of the security.
        description : str, optional
            Description of the security.
        asset_class : str, optional
            Asset class (e.g., "equity", "bond").
        currency : str, optional
            Currency code (e.g., "JPY", "USD").

        Returns
        -------
        SecurityId
            The ID of the created security.
        """
        cursor = self._db.execute(
            """
            INSERT INTO securities (name, description, asset_class, currency)
            VALUES (?, ?, ?, ?)
            """,
            (name, description, asset_class, currency),
        )
        self._db.commit()

        security_id: SecurityId = cursor.lastrowid  # type: ignore[assignment]
        logger.info("Security created", security_id=security_id, name=name)
        return security_id

    def get(self, security_id: SecurityId) -> SecurityDict | None:
        """Get a security by ID.

        Parameters
        ----------
        security_id : SecurityId
            ID of the security to retrieve.

        Returns
        -------
        SecurityDict or None
            Security data if found, None otherwise.
        """
        row = self._db.fetchone(
            """
            SELECT security_id, name, description, asset_class, currency,
                   created_at, updated_at
            FROM securities
            WHERE security_id = ?
            """,
            (security_id,),
        )

        if row is None:
            return None

        return SecurityDict(
            security_id=row["security_id"],
            name=row["name"],
            description=row["description"],
            asset_class=row["asset_class"],
            currency=row["currency"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def add_identifier(
        self,
        security_id: SecurityId,
        identifier_type: IdentifierType | str,
        identifier_value: str,
        is_primary: bool = False,
        valid_from: date | None = None,
        valid_to: date | None = None,
    ) -> None:
        """Add an identifier to a security.

        Parameters
        ----------
        security_id : SecurityId
            ID of the security.
        identifier_type : IdentifierType or str
            Type of the identifier (e.g., "ISIN", "JP_CODE").
        identifier_value : str
            Value of the identifier.
        is_primary : bool, optional
            Whether this is the primary identifier.
        valid_from : date, optional
            Start of validity period.
        valid_to : date, optional
            End of validity period.

        Raises
        ------
        DuplicateSecurityError
            If the identifier is already assigned to another security.
        """
        # Check for duplicate
        existing = self._db.fetchone(
            """
            SELECT security_id FROM security_identifiers
            WHERE identifier_type = ?
              AND identifier_value = ?
              AND (valid_from IS NULL OR valid_from = ?)
            """,
            (identifier_type, identifier_value, valid_from),
        )

        if existing is not None and existing["security_id"] != security_id:
            raise DuplicateSecurityError(str(identifier_type), identifier_value)

        self._db.execute(
            """
            INSERT INTO security_identifiers
            (security_id, identifier_type, identifier_value, is_primary, valid_from, valid_to)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                security_id,
                identifier_type,
                identifier_value,
                1 if is_primary else 0,
                valid_from,
                valid_to,
            ),
        )
        self._db.commit()

        logger.debug(
            "Identifier added",
            security_id=security_id,
            identifier_type=identifier_type,
            identifier_value=identifier_value,
        )

    def get_identifiers(
        self,
        security_id: SecurityId,
    ) -> list[SecurityIdentifierDict]:
        """Get all identifiers for a security.

        Parameters
        ----------
        security_id : SecurityId
            ID of the security.

        Returns
        -------
        list[SecurityIdentifierDict]
            List of identifiers.
        """
        rows = self._db.fetchall(
            """
            SELECT id, security_id, identifier_type, identifier_value,
                   valid_from, valid_to, is_primary, created_at
            FROM security_identifiers
            WHERE security_id = ?
            ORDER BY identifier_type, valid_from
            """,
            (security_id,),
        )

        return [
            SecurityIdentifierDict(
                id=row["id"],
                security_id=row["security_id"],
                identifier_type=row["identifier_type"],
                identifier_value=row["identifier_value"],
                valid_from=_parse_date(row["valid_from"]),
                valid_to=_parse_date(row["valid_to"]),
                is_primary=bool(row["is_primary"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_by_identifier(
        self,
        identifier_type: IdentifierType | str,
        identifier_value: str,
        as_of: date | None = None,
    ) -> SecurityDict | None:
        """Get a security by identifier.

        Parameters
        ----------
        identifier_type : IdentifierType or str
            Type of the identifier.
        identifier_value : str
            Value of the identifier.
        as_of : date, optional
            Point-in-time date for validity check. Defaults to current date.

        Returns
        -------
        SecurityDict or None
            Security data if found, None otherwise.
        """
        if as_of is None:
            as_of = date.today()

        row = self._db.fetchone(
            """
            SELECT s.security_id, s.name, s.description, s.asset_class,
                   s.currency, s.created_at, s.updated_at
            FROM securities s
            JOIN security_identifiers si ON s.security_id = si.security_id
            WHERE si.identifier_type = ?
              AND si.identifier_value = ?
              AND (si.valid_from IS NULL OR si.valid_from <= ?)
              AND (si.valid_to IS NULL OR si.valid_to > ?)
            ORDER BY si.valid_from DESC NULLS LAST
            LIMIT 1
            """,
            (identifier_type, identifier_value, as_of, as_of),
        )

        if row is None:
            return None

        return SecurityDict(
            security_id=row["security_id"],
            name=row["name"],
            description=row["description"],
            asset_class=row["asset_class"],
            currency=row["currency"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def search(
        self,
        name_pattern: str | None = None,
        identifier_value: str | None = None,
    ) -> list[SecurityDict]:
        """Search for securities.

        Parameters
        ----------
        name_pattern : str, optional
            SQL LIKE pattern for name search.
        identifier_value : str, optional
            Identifier value to search for.

        Returns
        -------
        list[SecurityDict]
            List of matching securities.
        """
        if identifier_value is not None:
            rows = self._db.fetchall(
                """
                SELECT DISTINCT s.security_id, s.name, s.description,
                       s.asset_class, s.currency, s.created_at, s.updated_at
                FROM securities s
                JOIN security_identifiers si ON s.security_id = si.security_id
                WHERE si.identifier_value = ?
                ORDER BY s.name
                """,
                (identifier_value,),
            )
        elif name_pattern is not None:
            rows = self._db.fetchall(
                """
                SELECT security_id, name, description, asset_class, currency,
                       created_at, updated_at
                FROM securities
                WHERE name LIKE ?
                ORDER BY name
                """,
                (name_pattern,),
            )
        else:
            rows = self._db.fetchall(
                """
                SELECT security_id, name, description, asset_class, currency,
                       created_at, updated_at
                FROM securities
                ORDER BY name
                """,
            )

        return [
            SecurityDict(
                security_id=row["security_id"],
                name=row["name"],
                description=row["description"],
                asset_class=row["asset_class"],
                currency=row["currency"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]


def _parse_date(value: str | date | None) -> date | None:
    """Parse a date value from SQLite.

    Parameters
    ----------
    value : str or date or None
        Value to parse.

    Returns
    -------
    date or None
        Parsed date or None.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
