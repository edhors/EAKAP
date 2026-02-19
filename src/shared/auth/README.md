# auth

Shared authentication module for FastAPI apps. Implements **OAuth 2.1 Authorization Code with PKCE**, JWT access/refresh tokens, user registration, and protected-route dependencies.

## Overview

- **User registration** with email, password, tenant, department, project, and clearance
- **Login** returns an authorization code (PKCE) instead of tokens directly
- **Token endpoint** exchanges authorization code or refresh token for access + refresh tokens
- **JWT** access tokens (short-lived) and refresh tokens (stored in DB, revocable)
- **Dependencies** for protecting routes: `get_current_user`, `get_current_active_user`

Depends on **userdb_handler** for `User`, `RefreshToken`, `AuthorizationCode`, `UserService`, `TokenService`, and `get_session`.

## Structure

| File | Purpose |
|------|---------|
| `config.py` | Settings from env (`auth_*` prefix): JWT, OAuth client, code/token expiry |
| `router.py` | FastAPI routes: `/auth/register`, `/auth/login`, `/auth/token`, `/auth/token/revoke`, `/auth/me`; `register_exception_handlers()` |
| `service.py` | `AuthService`: register, login, authorization code + PKCE, token exchange, refresh, revoke |
| `utils.py` | Password hashing (pwdlib), JWT create/decode, PKCE code verifier/challenge |
| `schemas.py` | Pydantic: `UserRegister`, `UserResponse`, `UserLogin`, `TokenRequest`, `TokenResponse`, `TokenPayload`, etc. |
| `dependencies.py` | `get_auth_service`, `get_current_user`, `get_current_active_user` (Bearer token) |
| `exceptions.py` | `AuthError` and subclasses: `InvalidCredentialsError`, `InvalidGrantError`, `UserConflictError`, etc. |
| `models.py` | (Reserved; user/token models live in userdb_handler) |

## Setup

### 1. Environment

Set in `.env` or environment (with `auth_` prefix):

| Variable | Required | Description |
|----------|----------|-------------|
| `auth_secret_key` | Yes | Secret for signing JWTs |
| `auth_oauth_client_id` | Yes | Allowed OAuth client_id (e.g. frontend app id) |
| `auth_oauth_redirect_uri` | Yes | Allowed redirect URI |
| `auth_algorithm` | No | JWT algorithm (default: `HS256`) |
| `auth_access_token_expire_minutes` | No | Access token TTL (default: 15) |
| `auth_refresh_token_expire_days` | No | Refresh token TTL (default: 30) |
| `auth_authorization_code_expire_minutes` | No | Authorization code TTL (default: 10) |

### 2. Mount router and exception handlers

```python
from fastapi import FastAPI
from src.shared.auth.router import router, register_exception_handlers

app = FastAPI()
app.include_router(router)
register_exception_handlers(app)
```

Ensure the app uses the same **session/database** source as `userdb_handler` (e.g. `get_session` from userdb_handler is used by `get_auth_service`).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register user (body: `UserRegister`). Returns `UserResponse`. |
| `POST` | `/auth/login` | Login with email/password; query: `client_id`, `redirect_uri`, `code_challenge`, `code_challenge_method`, `state`. Returns `AuthorizeResponse` (authorization code + optional state). |
| `POST` | `/auth/token` | Exchange code+code_verifier or refresh_token for tokens. Body: `TokenRequest` (grant_type, client_id, and code/code_verifier or refresh_token). Returns `TokenResponse`. |
| `POST` | `/auth/token/revoke` | Revoke a refresh token (body: token). Returns 204. |
| `GET` | `/auth/me` | Current user (requires Bearer access token). Returns `UserResponse`. |

All auth errors are mapped via `register_exception_handlers` to JSON with appropriate status codes and optional `WWW-Authenticate: Bearer` for 401.

## Protecting routes

Use `get_current_active_user` for routes that require an authenticated, active user:

```python
from fastapi import APIRouter, Depends
from src.shared.auth.dependencies import get_current_active_user
from src.shared.userdb_handler import User

router = APIRouter()

@router.get("/protected")
def protected(current_user: User = Depends(get_current_active_user)):
    return {"user_id": current_user.id, "email": current_user.email}
```

Use `get_current_user` if you only need a valid token and user (e.g. to allow inactive users with a different message).

## OAuth 2.1 PKCE flow (high level)

1. **Client** generates PKCE pair: `code_verifier`, `code_challenge` (e.g. S256 of verifier).
2. **Client** sends user to `POST /auth/login` with email/password and query params: `client_id`, `redirect_uri`, `code_challenge`, `code_challenge_method`, optional `state`.
3. **Server** authenticates user, creates short-lived authorization code bound to `code_challenge`, returns code (and state) to client (e.g. in redirect).
4. **Client** calls `POST /auth/token` with `grant_type=authorization_code`, `client_id`, `code`, `code_verifier`.
5. **Server** verifies code, checks PKCE (challenge from verifier), then issues access_token and refresh_token.
6. **Client** uses access_token as Bearer for API calls; uses refresh_token with `grant_type=refresh_token` to get a new pair when needed.
7. **Logout**: `POST /auth/token/revoke` with the refresh token.

## Exceptions

All derive from `AuthError` (status + detail). Handled by `register_exception_handlers`:

- `InvalidClientError` (400)
- `InvalidCredentialsError` (401)
- `InvalidGrantError` (400) – bad/expired code or refresh token
- `UnsupportedGrantTypeError` (400)
- `MissingGrantFieldsError` (400)
- `UserConflictError` (409)
- `InactiveUserError` (403)
- `InvalidTokenError` (401)
- `UserNotFoundError` (401)
