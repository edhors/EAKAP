# User database: Turso setup and usage

This guide explains how to set up **Turso** (hosted SQLite) and use it with the project’s **userdb_handler** module for users, refresh tokens, and authorization codes.

---

## What is Turso?

**Turso** is a distributed SQLite database (libSQL) hosted by Turso. You get a remote database URL and an auth token; the app connects over HTTPS and uses it like SQLite. The project uses **SQLModel** (SQLAlchemy + Pydantic) with the **sqlalchemy-libsql** driver to talk to Turso.

---

## Prerequisites

- A **Turso account** (free tier available at [turso.tech](https://turso.tech))
- **Turso CLI** installed on your machine

---

## 1. Install the Turso CLI

Install the Turso CLI using one of the following.

**Linux (install script):**

```bash
curl -sSfL https://get.tur.so/install.sh | bash
```

**macOS (Homebrew):**

```bash
brew install tursodatabase/tap/turso
```

**Windows:** Use WSL, then run the same script as Linux:

```powershell
wsl
# then inside WSL:
curl -sSfL https://get.tur.so/install.sh | bash
```

Confirm installation:

```bash
turso --version
```

---

## 2. Log in to Turso

Link the CLI to your Turso account (GitHub or email):

```bash
turso auth login
```

For headless environments (e.g. WSL, CI):

```bash
turso auth login --headless
```

---

## 3. Create a database

Create a new database (replace `your-db-name` with a name you prefer):

```bash
turso db create your-db-name
```

Optional: wait until the database is ready:

```bash
turso db create your-db-name --wait
```

List databases:

```bash
turso db list
```

---

## 4. Get the database URL

The app needs the **libSQL URL** of your database.

Show database details and URL:

```bash
turso db show your-db-name --url
```

Example output:

```
libsql://your-db-name-your-org.turso.io
```

Use this value for `turso_database_url` (see below). Do **not** add `?secure=true` here; the app adds it when building the connection string.

---

## 5. Create an auth token

The app connects with a **database token**, not your Turso account.

Create a token (no expiration by default):

```bash
turso db tokens create your-db-name
```

Example output:

```
Created token: eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

Optional: create a read-only or short-lived token:

```bash
# Read-only
turso db tokens create your-db-name --read-only

# Expires in 7 days
turso db tokens create your-db-name --expiration 7d
```

Use this value for `turso_auth_token`. **Keep it secret** (e.g. in `.env`, never in git).

---

## 6. Configure the project

The **userdb_handler** reads two environment variables (with prefix `turso_`).

### Option A: `.env` file (recommended)

In the project root, create or edit `.env`:

```env
turso_database_url=libsql://your-db-name-your-org.turso.io
turso_auth_token=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

Replace with your actual URL and token from steps 4 and 5.

### Option B: Export in the shell

```bash
export turso_database_url="libsql://your-db-name-your-org.turso.io"
export turso_auth_token="eyJ..."
```

### Ensure `.env` is ignored by Git

Add to `.gitignore` if not already there:

```
.env
.env.local
```

---

## 7. Python dependencies

The project already depends on:

- **sqlmodel** – ORM and models
- **sqlalchemy-libsql** – Turso/libSQL driver for SQLAlchemy
- **pydantic-settings** – load settings from env
- **python-dotenv** – load `.env` into the environment

Install from the repo root:

```bash
pip install -r requirements.txt
```

---

## 8. Initialize the database (create tables)

Tables are created in Turso the first time you call `init_db()`.

In your app startup (e.g. FastAPI lifespan or a script):

```python
from src.shared.userdb_handler import init_db

init_db()
```

This creates the **User**, **RefreshToken**, and **AuthorizationCode** tables if they do not exist.

---

## 9. Using the database (read and write)

All access goes through a **session** and the **UserService** / **TokenService**.

1. Get a session with `get_session()`.
2. Build `UserService(session)` and/or `TokenService(session)`.
3. Call the service methods to read or write.

Example:

```python
from datetime import datetime, timedelta
from src.shared.userdb_handler import get_session, UserService, TokenService, init_db

init_db()
session_gen = get_session()
session = next(session_gen)

user_svc = UserService(session)
token_svc = TokenService(session)

# Write: create user
user = user_svc.create_user(
    email="user@example.com",
    hashed_password="hashed-secret",
    tenant_id="tenant-1",
    dept="engineering",
    project="proj-a",
    clearance=2,
)

# Read: by id, email, tenant, project
user = user_svc.get_user_by_id(user.id)
user = user_svc.get_user_by_email("user@example.com")
users = user_svc.get_users_by_tenant("tenant-1")
users = user_svc.get_users_by_project("proj-a")

# Write: update and delete
user_svc.update_user(user.id, dept="product", clearance=3)
# user_svc.delete_user(user.id)

# Write: create refresh token
refresh = token_svc.create_token(
    user_id=user.id,
    token="random-token-string",
    expires_at=datetime.utcnow() + timedelta(days=7),
)

# Read: get token(s)
token = token_svc.get_token(refresh.token)
tokens = token_svc.get_tokens_by_user(user.id)

# Write: revoke
token_svc.revoke_token(refresh.token)
# token_svc.revoke_all_user_tokens(user.id)
```

For the full list of read/write methods and usage details, see **[src/shared/userdb_handler/README.md](../../src/shared/userdb_handler/README.md)**.

---

## 10. Connection details (reference)

The **userdb_handler** builds the engine as follows:

- **URL:** `sqlite+libsql://<your-database-url>?secure=true`  
  (Your env value is `turso_database_url`, e.g. `libsql://your-db-name-your-org.turso.io`.)
- **Auth:** `connect_args={"auth_token": settings.auth_token}`  
  (From `turso_auth_token`.)

So the app always uses the **libSQL** driver with **HTTPS** (`secure=true`) and token auth. No credentials go in the URL.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| **Connection / auth errors** | Correct `turso_database_url` (with `libsql://`), valid `turso_auth_token`, and that the token was created for that database. |
| **Tables missing** | Call `init_db()` once at startup so SQLModel can create the tables. |
| **Env vars not loaded** | Ensure `.env` is in the working directory (or set `DOTENV_PATH`) and that the app loads dotenv before using `userdb_handler`. |
| **Token expired** | Turso tokens can have an expiration. Create a new token with `turso db tokens create your-db-name` and update `turso_auth_token`. |

### Turso CLI useful commands

```bash
turso db list                    # List databases
turso db show your-db-name       # Database info
turso db show your-db-name --url # Connection URL
turso db tokens create your-db-name   # New auth token
turso db shell your-db-name      # Interactive SQL shell
turso db destroy your-db-name    # Delete database (irreversible)
```

---

## Summary

1. Install **Turso CLI** and run **`turso auth login`**.
2. **Create a database:** `turso db create your-db-name`.
3. **Get URL:** `turso db show your-db-name --url` → set **`turso_database_url`**.
4. **Create token:** `turso db tokens create your-db-name` → set **`turso_auth_token`**.
5. Put both in **`.env`** (or export them).
6. In the app, call **`init_db()`** once, then use **`get_session()`**, **UserService**, and **TokenService** for all read/write.

For the full API of the module, see **[src/shared/userdb_handler/README.md](../../src/shared/userdb_handler/README.md)**.
