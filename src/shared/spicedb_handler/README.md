# spicedb_handler

Shared utilities for interacting with [SpiceDB](https://authzed.com/) (Zanzibar-style authorization). This package manages the **doc–user viewer** schema and writes viewer relationships so that permission checks (e.g. “can this user view this doc?”) can be performed via SpiceDB.

## Files

| File | Purpose |
|------|--------|
| `__init__.py` | Marks this directory as a Python package. |
| `apply_schema.py` | One-off script to apply the user/doc/viewer schema to a SpiceDB instance. |
| `write_relationships.py` | Module for writing doc–user viewer relationships to SpiceDB. |

---

### `apply_schema.py`

**Purpose:** Apply the authorization schema to SpiceDB (run once per environment or after schema changes).

**Schema:**
- **`user`** — Empty definition; represents a user subject.
- **`doc`** — Resource type for documents:
  - **Relation:** `viewer` → set of `user` (who can view the doc).
  - **Permission:** `view` = `viewer` (used for “can user view doc?” checks).

**Usage:**
```bash
# Default: localhost:50051, token "test"
python -m src.shared.spicedb_handler.apply_schema

# Custom endpoint and/or token
python -m src.shared.spicedb_handler.apply_schema <endpoint> [token]
```

After running, it writes the schema, reads it back, and prints the current schema to confirm.

---

### `write_relationships.py`

**Purpose:** Write **doc → viewer → user** relationships to SpiceDB so that `doc:…#viewer@user:…` is stored and the `view` permission can be evaluated.

**Exports:**
- **`RELATION_VIEWER`** — Relation name (`"viewer"`); must match the schema in `apply_schema.SCHEMA`.
- **`RESOURCE_TYPE`** — Object type for documents (`"doc"`).
- **`SUBJECT_TYPE`** — Object type for users (`"user"`).
- **`RelationshipWriter`** — Class that writes batches of viewer relationships.

**`RelationshipWriter.write_relationships(relationships, client)`**
- **`relationships`:** List of dicts with `doc_id` and `user_id` (strings). Entries missing either key are skipped.
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) that supports `WriteRelationships`.
- Uses **OPERATION_TOUCH**, so sending the same relationships again is idempotent.
- Returns the `WriteRelationshipsResponse` (with `written_at` ZedToken), or `None` if there were no valid updates (empty input or all items skipped).

**Example:**
```python
from authzed.api.v1 import InsecureClient
from src.shared.spicedb_handler.write_relationships import RelationshipWriter

client = InsecureClient("localhost:50051", "test")
writer = RelationshipWriter()
writer.write_relationships(
    [
        {"doc_id": "doc-1", "user_id": "user-a"},
        {"doc_id": "doc-1", "user_id": "user-b"},
    ],
    client,
)
```

---

## Related docs

For broader design and operations, see **SPEC.md** and **SPICEDB_OPERATIONS.md** (if present in the repo).
