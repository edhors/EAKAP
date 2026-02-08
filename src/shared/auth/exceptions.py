from fastapi import status


class AuthError(Exception):
    """Base exception for all auth-related errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An authentication error occurred"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class InvalidClientError(AuthError):
    """Raised when client_id is invalid."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid client_id"


class InvalidCredentialsError(AuthError):
    """Raised when email/password authentication fails."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password"


class InvalidGrantError(AuthError):
    """Raised when an authorization code or refresh token is invalid/expired."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Invalid or expired grant"


class UnsupportedGrantTypeError(AuthError):
    """Raised when grant_type is not recognized."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Unsupported grant_type"


class MissingGrantFieldsError(AuthError):
    """Raised when required fields for a grant type are missing."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Missing required fields for this grant type"


class UserConflictError(AuthError):
    """Raised when registering a user that already exists."""

    status_code = status.HTTP_409_CONFLICT
    detail = "User with this email already exists"


class InactiveUserError(AuthError):
    """Raised when an inactive user tries to authenticate."""

    status_code = status.HTTP_403_FORBIDDEN
    detail = "User account is inactive"


class InvalidTokenError(AuthError):
    """Raised when a bearer token is invalid or expired."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid or expired token"


class UserNotFoundError(AuthError):
    """Raised when the user associated with a token no longer exists."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "User not found"
