# documentdb_handler

Shared module for document metadata persistence. Uses **SQLModel** with a **Turso**-backed database via a **local embedded replica** that syncs with Turso.

## Overview

- **Document** model: `dept`, `project`, `clearance`, `url`, and `id`
- Session-based **DocumentService** for create, get by id, and delete
- Same Turso env vars as `userdb_handler`; this module uses an **embedded** libSQL DB that syncs with the remote Turso URL

## Structure

| File | Purpose |
|------|---------|
| `config.py` | Settings from env (`turso_database_url`, `turso_auth_token`) |
| `database.py` | Engine (embedded replica), `init_db()`, `get_session()` |
| `models.py` | `Document` (SQLModel table) |
| `service.py` | `DocumentService` |
| `__init__.py` | Public exports |

## Connection mode

The engine uses a **local SQLite file** (`embedded.db`) that syncs with Turso:

```python
# database.py
engine = create_engine(
    "sqlite+libsql:///embedded.db",
    connect_args={
        "auth_token": settings.auth_token,
        "sync_url": settings.database_url,
    },
)
```

So you need the same Turso URL and token as for the user DB; data is written/read locally and synced with Turso. For full Turso setup (CLI, create DB, tokens), see [docs/userdb/setup-and-usage.md](../../../docs/userdb/setup-and-usage.md).

## Setup

1. **Environment**

   Set in `.env` or environment (same as userdb):

   - `turso_database_url` – Turso DB URL (e.g. `libsql://...`)
   - `turso_auth_token` – Turso auth token

2. **Initialize DB**

   Call once (e.g. at app startup):

   ```python
   from src.shared.documentdb_handler import init_db
   init_db()
   ```

   This creates the `document` table in the embedded DB (and syncs with Turso).

## Usage

All database read and write goes through a **session** and **DocumentService**.

### Session and service

```python
from src.shared.documentdb_handler import get_session, DocumentService, init_db

init_db()
session_gen = get_session()
session = next(session_gen)

doc_svc = DocumentService(session)

# Create
doc = doc_svc.create_doc(dept="engineering", project="proj-a", clearance=2, url="https://example.com/doc")

# Read
doc = doc_svc.get_doc_by_id(doc.id)

# Delete
doc_svc.delete_doc(doc.id)
```

### Read and write operations

| Service | Read | Write |
|---------|------|--------|
| **DocumentService** | `get_doc_by_id(document_id)` → `Document \| None` | `create_doc(dept, project, clearance, url)` → `Document`, `delete_doc(document_id)` → `bool` |

- **Read:** returns the `Document` or `None` if not found.
- **Write:** create returns the new `Document`; delete returns `True` if deleted, `False` if not found.

### Public API (from `documentdb_handler`)

- **Model:** `Document`
- **Config:** `settings`
- **DB:** `engine`, `get_session`, `init_db`
- **Service:** `DocumentService`

## Model

- **Document:** `id` (UUID), `dept`, `project`, `clearance`, `url`

No Pydantic request/response schemas in this module; the service builds `Document` directly.
