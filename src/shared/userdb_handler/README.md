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

All database read and write goes through **sessions** and the **UserService** / **TokenService**. Get a session with `get_session()`, then instantiate the services with that session.

### Session and services

```python
from datetime import datetime, timedelta
from src.shared.userdb_handler import get_session, UserService, TokenService

session_gen = get_session()
session = next(session_gen)
try:
    user_svc = UserService(session)
    token_svc = TokenService(session)

    # --- Write: create user ---
    user = user_svc.create_user(
        email="user@example.com",
        hashed_password="...",
        tenant_id="tenant-1",
        dept="engineering",
        project="proj-a",
        clearance=2,
    )

    # --- Read: look up users ---
    user = user_svc.get_user_by_id(user.id)
    user = user_svc.get_user_by_email("user@example.com")
    users = user_svc.get_users_by_tenant("tenant-1")
    users = user_svc.get_users_by_project("proj-a")

    # --- Write: update and delete user ---
    user_svc.update_user(user.id, dept="product", clearance=3)
    user_svc.delete_user(user.id)

    # --- Write: create refresh token ---
    refresh = token_svc.create_token(
        user_id=user.id,
        token="random-token-string",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    # --- Read: look up tokens ---
    token = token_svc.get_token(refresh.token)
    tokens = token_svc.get_tokens_by_user(user.id)

    # --- Write: revoke tokens ---
    token_svc.revoke_token(refresh.token)
    token_svc.revoke_all_user_tokens(user.id)
finally:
    session_gen.close()  # if using generator manually
```

### Read and write operations

| Service       | Read (queries)                                                                 | Write (mutations)                                              |
|---------------|---------------------------------------------------------------------------------|----------------------------------------------------------------|
| **UserService**  | `get_user_by_id(id)`, `get_user_by_email(email)`, `get_users_by_tenant(tenant_id)`, `get_users_by_project(project)` | `create_user(...)`, `update_user(user_id, **kwargs)`, `delete_user(user_id)` |
| **TokenService** | `get_token(token)`, `get_tokens_by_user(user_id)`                               | `create_token(user_id, token, expires_at)`, `revoke_token(token)`, `revoke_all_user_tokens(user_id)` |

- **Read** methods return a single model or list; user/token lookups return `None` or empty list when not found.
- **Write** methods persist changes with `session.commit()`; create/update return the model, delete/revoke return `bool` or count.

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
