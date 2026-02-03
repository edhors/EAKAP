from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
from sqlmodel import Session, select

from .config import settings
from .schemas import UserRegister, TokenPayload
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
            raise ValueError("User with this email already exists")

        hashed_password = get_password_hash(data.password)
        return self._user_service.create_user(
            email=data.email,
            hashed_password=hashed_password,
            tenant_id=data.tenant_id,
        )

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = self._user_service.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
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
    ) -> Optional[User]:
        """Verify authorization code and PKCE challenge."""
        statement = select(AuthorizationCode).where(
            AuthorizationCode.code == code,
            AuthorizationCode.client_id == client_id,
            AuthorizationCode.used == False,
        )
        auth_code = self._session.exec(statement).first()

        if not auth_code:
            return None

        # Check expiration
        if datetime.utcnow() > auth_code.expires_at:
            return None

        # Verify PKCE challenge
        computed_challenge = get_code_challenge(code_verifier)
        if computed_challenge != auth_code.code_challenge:
            return None

        # Mark as used
        auth_code.used = True
        self._session.add(auth_code)
        self._session.commit()

        # Return user
        return self._user_service.get_user_by_id(auth_code.user_id)

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

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Generate new access token from refresh token."""
        # Verify token exists and not revoked in DB
        db_token = self._token_service.get_token(refresh_token)
        if not db_token:
            return None

        # Check expiration
        if datetime.utcnow() > db_token.expires_at:
            return None

        # Decode and verify JWT
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            return None

        if payload.get("type") != "refresh":
            return None

        # Get user
        user = self._user_service.get_user_by_id(payload["sub"])
        if not user or not user.is_active:
            return None

        # Revoke old token and create new pair
        self._token_service.revoke_token(refresh_token)
        return self.create_tokens(user)

    def revoke_refresh_token(self, token: str) -> bool:
        """Revoke refresh token."""
        return self._token_service.revoke_token(token)

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
