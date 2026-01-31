# spicedb_handler

Shared utilities for interacting with [SpiceDB](https://authzed.com/) (Zanzibar-style authorization). This package manages the **doc–user viewer** schema and writes viewer relationships so that permission checks (e.g. “can this user view this doc?”) can be performed via SpiceDB.

## Files

| File | Purpose |
|------|--------|
| `__init__.py` | Marks this directory as a Python package. |
| `apply_schema.py` | One-off script to apply the user/doc/viewer schema to a SpiceDB instance. |
| `write_relationships.py` | Module for writing doc–user viewer relationships to SpiceDB. |
| `read_relationships.py` | Module for checking which doc_ids a user has view permission for. |

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

### `read_relationships.py`

**Purpose:** Check which doc_ids from a candidate list the user has `view` permission for in SpiceDB. Used in RAG pipelines to filter retrieval results by user permissions.

**Exports:**
- **`PERMISSION_VIEW`** — Permission name (`"view"`); must match the schema in `apply_schema.SCHEMA`.
- **`RelationshipReader`** — Class that checks viewer permissions for batches of doc_ids.

**`RelationshipReader.get_allowed_doc_ids(user_id, candidates, client)`**
- **`user_id`:** The user to check permissions for (string).
- **`candidates`:** List of dicts from Full Retrieval with at least `doc_id`. Example: `[{"doc_id": "doc_1", "chunk_id": "...", "score": 0.85}, ...]`
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) with `CheckBulkPermissions`.
- Extracts unique doc_ids, then uses **CheckBulkPermissions** (one batch call) to check `view` permission for each doc.
- Returns list of doc_ids that the user is allowed to view (subset of unique doc_ids from candidates).
- Returns empty list if no candidates or no permissions granted.

**Example:**
```python
from authzed.api.v1 import InsecureClient
from src.shared.spicedb_handler.read_relationships import RelationshipReader

client = InsecureClient("localhost:50051", "test")
reader = RelationshipReader()

# Candidates from Full Retrieval
candidates = [
    {"doc_id": "doc_1", "chunk_id": "doc_1_chunk_0", "score": 0.85},
    {"doc_id": "doc_2", "chunk_id": "doc_2_chunk_0", "score": 0.72},
    {"doc_id": "doc_1", "chunk_id": "doc_1_chunk_1", "score": 0.68},  # duplicate doc_id
]

# Get allowed doc_ids for user
allowed_doc_ids = reader.get_allowed_doc_ids("user-123", candidates, client)
# Returns: ['doc_1'] (if user only has permission for doc_1)

# Use with PolicyFilter
from src.user.final_retrieval.policy_filter import PolicyFilter
pf = PolicyFilter(top_k=5)
chunk_ids = pf.filter(candidates, allowed_doc_ids)
```

---

## Related docs

For broader design and operations, see **SPEC.md** and **SPICEDB_OPERATIONS.md** (if present in the repo).
