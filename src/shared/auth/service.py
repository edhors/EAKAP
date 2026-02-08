from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
from sqlmodel import Session, select

from .config import settings
from .exceptions import (
    InvalidCredentialsError,
    InvalidGrantError,
    MissingGrantFieldsError,
    UnsupportedGrantTypeError,
    UserConflictError,
)
from .schemas import UserRegister, TokenPayload, TokenRequest
from .utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_code_challenge,
)
from src.shared.userdb_handler import (
    User,
    RefreshToken,
    AuthorizationCode,
    UserService,
    TokenService,
)


class AuthService:
    """Authentication service handling OAuth 2.1 with PKCE flow."""

    def __init__(self, session: Session):
        self._session = session
        self._user_service = UserService(session)
        self._token_service = TokenService(session)

    # User Management
    def register_user(self, data: UserRegister) -> User:
        """Register a new user."""
        existing = self._user_service.get_user_by_email(data.email)
        if existing:
            raise UserConflictError()

        hashed_password = get_password_hash(data.password)
        return self._user_service.create_user(
            email=data.email,
            hashed_password=hashed_password,
            tenant_id=data.tenant_id,
            dept=data.dept,
            project=data.project,
            clearance=data.clearance,
        )

    def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials."""
        user = self._user_service.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InvalidCredentialsError()
        return user

    # OAuth 2.1 Authorization Code Flow
    def create_authorization_code(
        self,
        user_id: str,
        client_id: str,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str = "S256",
    ) -> str:
        """Create authorization code for OAuth flow."""
        code = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.authorization_code_expire_minutes
        )

        auth_code = AuthorizationCode(
            code=code,
            user_id=user_id,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            expires_at=expires_at,
        )
        self._session.add(auth_code)
        self._session.commit()
        return code

    def verify_authorization_code(
        self,
        code: str,
        code_verifier: str,
        client_id: str,
    ) -> User:
        """Verify authorization code and PKCE challenge."""
        statement = select(AuthorizationCode).where(
            AuthorizationCode.code == code,
            AuthorizationCode.client_id == client_id,
            AuthorizationCode.used == False,
        )
        auth_code = self._session.exec(statement).first()

        if not auth_code:
            raise InvalidGrantError("Invalid or expired authorization code")

        # Check expiration
        if datetime.utcnow() > auth_code.expires_at:
            raise InvalidGrantError("Invalid or expired authorization code")

        # Verify PKCE challenge
        computed_challenge = get_code_challenge(code_verifier)
        if computed_challenge != auth_code.code_challenge:
            raise InvalidGrantError("Invalid or expired authorization code")

        # Mark as used
        auth_code.used = True
        self._session.add(auth_code)
        self._session.commit()

        # Return user
        user = self._user_service.get_user_by_id(auth_code.user_id)
        if not user:
            raise InvalidGrantError("User associated with code no longer exists")
        return user

    # JWT Token Operations
    def create_tokens(self, user: User) -> Tuple[str, str]:
        """Create access and refresh token pair."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
        }

        access_token = create_access_token(token_data)
        refresh_token_str = create_refresh_token(token_data)

        # Store refresh token in DB
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        self._token_service.create_token(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at,
        )

        return access_token, refresh_token_str

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Generate new access token from refresh token."""
        # Verify token exists and not revoked in DB
        db_token = self._token_service.get_token(refresh_token)
        if not db_token:
            raise InvalidGrantError("Invalid or expired refresh token")

        # Check expiration
        if datetime.utcnow() > db_token.expires_at:
            raise InvalidGrantError("Invalid or expired refresh token")

        # Decode and verify JWT
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise InvalidGrantError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise InvalidGrantError("Invalid or expired refresh token")

        # Get user
        user = self._user_service.get_user_by_id(payload["sub"])
        if not user or not user.is_active:
            raise InvalidGrantError("Invalid or expired refresh token")

        # Revoke old token and create new pair
        self._token_service.revoke_token(refresh_token)
        return self.create_tokens(user)

    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke refresh token."""
        return self._token_service.revoke_token(token)

    # Grant-type strategy dispatch
    def exchange_token(self, data: TokenRequest) -> Tuple[str, str]:
        """Dispatch token exchange to the appropriate grant-type handler."""
        grant_handlers = {
            "authorization_code": self._handle_authorization_code_grant,
            "refresh_token": self._handle_refresh_token_grant,
        }

        handler = grant_handlers.get(data.grant_type)
        if handler is None:
            raise UnsupportedGrantTypeError()

        return handler(data)

    def _handle_authorization_code_grant(self, data: TokenRequest) -> Tuple[str, str]:
        """Handle the authorization_code grant type."""
        if not data.code or not data.code_verifier:
            raise MissingGrantFieldsError(
                "code and code_verifier required for authorization_code grant",
            )

        user = self.verify_authorization_code(
            code=data.code,
            code_verifier=data.code_verifier,
            client_id=data.client_id,
        )
        return self.create_tokens(user)

    def _handle_refresh_token_grant(self, data: TokenRequest) -> Tuple[str, str]:
        """Handle the refresh_token grant type."""
        if not data.refresh_token:
            raise MissingGrantFieldsError(
                "refresh_token required for refresh_token grant",
            )

        return self.refresh_access_token(data.refresh_token)

    def verify_access_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode access token."""
        try:
            payload = decode_token(token)
        except ValueError:
            return None

        if payload.get("type") != "access":
            return None

        return TokenPayload(
            sub=payload["sub"],
            email=payload["email"],
            tenant_id=payload["tenant_id"],
            exp=payload["exp"],
            iat=payload["iat"],
            type=payload["type"],
        )

    def get_current_user(self, token_payload: TokenPayload) -> Optional[User]:
        """Get user from token payload."""
        return self._user_service.get_user_by_id(token_payload.sub)
