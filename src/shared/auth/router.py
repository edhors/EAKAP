from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from .config import settings
from .service import AuthService
from .schemas import (
    UserRegister,
    UserResponse,
    UserLogin,
    AuthorizeRequest,
    AuthorizeResponse,
    TokenRequest,
    TokenResponse,
    TokenRevokeRequest,
)
from .dependencies import get_auth_service, get_current_active_user
from src.shared.userdb_handler import get_session, User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    try:
        user = auth_service.register_user(data)
        return UserResponse(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
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
    # Validate client_id
    if client_id != settings.oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id",
        )

    # Authenticate user
    user = auth_service.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate authorization code
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
    # Validate client_id
    if data.client_id != settings.oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id",
        )

    if data.grant_type == "authorization_code":
        # Exchange authorization code for tokens
        if not data.code or not data.code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code and code_verifier required for authorization_code grant",
            )

        user = auth_service.verify_authorization_code(
            code=data.code,
            code_verifier=data.code_verifier,
            client_id=data.client_id,
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired authorization code",
            )

        access_token, refresh_token = auth_service.create_tokens(user)

    elif data.grant_type == "refresh_token":
        # Refresh access token
        if not data.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="refresh_token required for refresh_token grant",
            )

        result = auth_service.refresh_access_token(data.refresh_token)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired refresh token",
            )

        access_token, refresh_token = result

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type",
        )

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
