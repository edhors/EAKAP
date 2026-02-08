from typing import Optional
from fastapi import APIRouter, Depends, FastAPI, Query, status
from fastapi.responses import JSONResponse
from starlette.requests import Request

import sys
from pathlib import Path
# Add parent of src to sys.path so src can be imported as a module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src import *


router = APIRouter(prefix="/auth", tags=["Authentication"])


def register_exception_handlers(app: FastAPI) -> None:
    """Register auth exception handlers on the FastAPI app.

    Call this from your main.py after creating the app::

        from src.shared.auth.router import router, register_exception_handlers

        app = FastAPI()
        app.include_router(router)
        register_exception_handlers(app)
    """

    #FIX: Not used at the moment
    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
        headers = (
            {"WWW-Authenticate": "Bearer"}
            if exc.status_code == status.HTTP_401_UNAUTHORIZED
            else None
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    user = auth_service.register_user(data)
    return UserResponse(
        id=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
    )


@router.post("/login", response_model=AuthorizeResponse)
async def login(
    data: UserLogin,
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(default="S256"),
    state: Optional[str] = Query(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate user and return authorization code for OAuth PKCE flow."""
    _validate_client_id(client_id)

    user = auth_service.authenticate_user(data.email, data.password)

    code = auth_service.create_authorization_code(
        user_id=user.id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    return AuthorizeResponse(code=code, state=state)


@router.post("/token", response_model=TokenResponse)
async def token(
    data: TokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Exchange authorization code or refresh token for access token."""
    _validate_client_id(data.client_id)

    access_token, refresh_token = auth_service.exchange_token(data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/token/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    data: TokenRevokeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Revoke a refresh token (logout)."""
    auth_service.revoke_refresh_token(data.token)
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        tenant_id=current_user.tenant_id,
        is_active=current_user.is_active,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_client_id(client_id: str) -> None:
    """Raise InvalidClientError if client_id doesn't match config."""
    if client_id != settings.oauth_client_id:
        raise InvalidClientError()
