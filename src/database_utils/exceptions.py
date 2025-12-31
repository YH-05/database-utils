"""Custom exceptions for database-utils."""


class DatabaseUtilsError(Exception):
    """Base exception for database-utils."""


class IdentifierNotFoundError(DatabaseUtilsError):
    """Identifier could not be resolved to a security.

    Parameters
    ----------
    identifier_type : str
        Type of the identifier (e.g., "ISIN", "JP_CODE").
    identifier_value : str
        Value of the identifier.
    """

    def __init__(self, identifier_type: str, identifier_value: str) -> None:
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value
        super().__init__(f"Security not found: {identifier_type}={identifier_value}")


class DuplicateSecurityError(DatabaseUtilsError):
    """Security already exists.

    Parameters
    ----------
    identifier_type : str
        Type of the identifier.
    identifier_value : str
        Value of the identifier.
    """

    def __init__(self, identifier_type: str, identifier_value: str) -> None:
        self.identifier_type = identifier_type
        self.identifier_value = identifier_value
        super().__init__(
            f"Security already exists: {identifier_type}={identifier_value}"
        )


class ValidationError(DatabaseUtilsError):
    """Input validation failed.

    Parameters
    ----------
    field : str
        Name of the field that failed validation.
    reason : str
        Reason for the validation failure.
    """

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason}")
