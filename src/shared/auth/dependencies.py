from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from .exceptions import InactiveUserError, InvalidTokenError, UserNotFoundError
from .service import AuthService
from src.shared.userdb_handler import get_session, User


security = HTTPBearer()


def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Dependency to get current authenticated user from Bearer token."""
    token = credentials.credentials
    payload = auth_service.verify_access_token(token)

    if not payload:
        raise InvalidTokenError()

    user = auth_service.get_current_user(payload)
    if not user:
        raise UserNotFoundError()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure user is active."""
    if not current_user.is_active:
        raise InactiveUserError()
    return current_user
