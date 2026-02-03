from .config import settings
from .service import AuthService
from .router import router
from .dependencies import get_auth_service, get_current_user, get_current_active_user
from .schemas import (
    UserRegister,
    UserResponse,
    UserLogin,
    AuthorizeRequest,
    AuthorizeResponse,
    TokenRequest,
    TokenResponse,
    TokenRevokeRequest,
    TokenPayload,
)
from .utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_code_verifier,
    generate_pkce_pair,
    get_code_challenge,
)

__all__ = [
    # Config
    "settings",
    # Service
    "AuthService",
    # Router
    "router",
    # Dependencies
    "get_auth_service",
    "get_current_user",
    "get_current_active_user",
    # Schemas
    "UserRegister",
    "UserResponse",
    "UserLogin",
    "AuthorizeRequest",
    "AuthorizeResponse",
    "TokenRequest",
    "TokenResponse",
    "TokenRevokeRequest",
    "TokenPayload",
    # Utils
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_code_verifier",
    "generate_pkce_pair",
    "get_code_challenge",
]
