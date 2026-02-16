# userdb_handler

Shared module for user persistence and token management. Uses **SQLModel** with a **Turso** (SQLite) database.

## Overview

- **User** CRUD with tenant, department, project, and clearance
- **Refresh token** storage and revocation
- **Authorization code** storage for OAuth 2.1 PKCE
- Session-based services suitable for dependency injection

## Structure

| File | Purpose |
|------|---------|
| `config.py` | Settings from env (`turso_database_url`, `turso_auth_token`) |
| `database.py` | Engine, `init_db()`, `get_session()` |
| `models.py` | `User`, `RefreshToken`, `AuthorizationCode` (SQLModel tables) |
| `schemas.py` | Pydantic schemas: `UserCreate`, `UserUpdate`, `RefreshTokenCreate` |
| `service.py` | `UserService`, `TokenService` |
| `__init__.py` | Public exports |

## Setup

1. **Environment**

   Set in `.env` or environment:

   - `turso_database_url` – Turso DB URL (e.g. `libsql://...`)
   - `turso_auth_token` – Turso auth token

2. **Initialize DB**

   Call once (e.g. at app startup):

   ```python
   from src.shared.userdb_handler import init_db
   init_db()
   ```

## Usage

### Session and services

```python
from src.shared.userdb_handler import get_session, UserService, TokenService

with next(get_session()) as session:
    user_svc = UserService(session)
    token_svc = TokenService(session)

    # Create user
    user = user_svc.create_user(
        email="user@example.com",
        hashed_password="...",
        tenant_id="tenant-1",
        dept="engineering",
        project="proj-a",
        clearance=2,
    )

    # Lookup
    user = user_svc.get_user_by_email("user@example.com")
    users = user_svc.get_users_by_tenant("tenant-1")

    # Refresh token
    refresh = token_svc.create_token(user_id=user.id, token="...", expires_at=...)
    token_svc.revoke_token(refresh.token)
```

### Public API (from `userdb_handler`)

- **Models:** `User`, `RefreshToken`, `AuthorizationCode`
- **Config:** `settings`
- **DB:** `engine`, `get_session`, `init_db`
- **Services:** `UserService`, `TokenService`

## Models

- **User:** `id`, `email`, `hashed_password`, `tenant_id`, `is_active`, `dept`, `project`, `clearance`
- **RefreshToken:** `id`, `user_id`, `token`, `expires_at`, `revoked`
- **AuthorizationCode:** `id`, `code`, `user_id`, `client_id`, `redirect_uri`, `code_challenge`, `code_challenge_method`, `expires_at`, `used`, `created_at`

## Tests

- `test_db_connection.py` – checks DB connection and session type after `init_db()`
- `test_service.py` – `UserService` tests (e.g. `create_user`)

Run from project root, e.g.:

```bash
pytest src/shared/userdb_handler/
```
