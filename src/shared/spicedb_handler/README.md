# spicedb_handler

Shared utilities for interacting with [SpiceDB](https://authzed.com/) (Zanzibar-style authorization). This package manages an **RBAC schema** with users, roles, clearances, and documents. Documents grant view permission when the user is in the required department role, project role, and meets (or exceeds) the required clearance level.

## Files

| File | Purpose |
|------|--------|
| `__init__.py` | Marks this directory as a Python package. |
| `apply_schema.py` | One-off script to apply the RBAC schema (user/role/clearance/document) to a SpiceDB instance. |
| `write_relationships.py` | Module for writing RBAC relationships (role members, clearance members, clearance hierarchy, document access) to SpiceDB. |
| `read_relationships.py` | Module for checking which doc_ids (document IDs) a user has view permission for. |

---

### `apply_schema.py`

**Purpose:** Apply the authorization schema to SpiceDB (run once per environment or after schema changes).

**Schema:**
- **`user`** — Empty definition; represents a user subject.
- **`role`** — Represents roles (e.g. department, project):
  - **Relation:** `member` → set of `user` (users assigned to this role).
- **`clearance`** — Represents clearance levels with inheritance:
  - **Relation:** `member` → set of `user` (users assigned to this clearance level).
  - **Relation:** `higher_clearance` → set of `clearance` (higher clearances inherit lower ones).
- **`document`** — Resource type for documents:
  - **Relation:** `viewer_dept` → `role` (department role required to view).
  - **Relation:** `viewer_project` → `role` (project role required to view).
  - **Relation:** `required_clearance` → `clearance` (clearance level required to view).
  - **Permission:** `view` = user must be member of viewer_dept role AND viewer_project role AND (member of required_clearance OR member of a higher clearance).

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

**Purpose:** Write RBAC relationships to SpiceDB. The new schema requires four types of relationships: role memberships, clearance memberships, clearance hierarchy, and document access control.

**Exports:**
- **`RESOURCE_TYPE`** — Document resource type (`"document"`); used by read module.
- **`RESOURCE_TYPE_DOCUMENT`** — Document resource type (`"document"`).
- **`RESOURCE_TYPE_ROLE`** — Role resource type (`"role"`).
- **`RESOURCE_TYPE_CLEARANCE`** — Clearance resource type (`"clearance"`).
- **`SUBJECT_TYPE`** — User subject type (`"user"`).
- **`RELATION_MEMBER`** — Member relation (`"member"`).
- **`RELATION_HIGHER_CLEARANCE`** — Higher clearance relation (`"higher_clearance"`).
- **`RELATION_VIEWER_DEPT`** — Department viewer relation (`"viewer_dept"`).
- **`RELATION_VIEWER_PROJECT`** — Project viewer relation (`"viewer_project"`).
- **`RELATION_REQUIRED_CLEARANCE`** — Required clearance relation (`"required_clearance"`).
- **`RelationshipWriter`** — Class that writes batches of RBAC relationships.

#### `RelationshipWriter.write_role_members(relationships, client)`

Write role membership relationships.

- **`relationships`:** List of dicts with `role_id` and `user_id` (strings). Entries missing either key are skipped.
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) that supports `WriteRelationships`.
- Uses **OPERATION_TOUCH**, so sending the same relationships again is idempotent.
- Returns the `WriteRelationshipsResponse` (with `written_at` ZedToken), or `None` if there were no valid updates.

**Example:**
```python
from authzed.api.v1 import InsecureClient
from src.shared.spicedb_handler.write_relationships import RelationshipWriter

client = InsecureClient("localhost:50051", "test")
writer = RelationshipWriter()
writer.write_role_members(
    [
        {"role_id": "engineering", "user_id": "user-123"},
        {"role_id": "project-alpha", "user_id": "user-123"},
    ],
    client,
)
```

#### `RelationshipWriter.write_clearance_members(relationships, client)`

Write clearance membership relationships.

- **`relationships`:** List of dicts with `clearance_id` and `user_id` (strings). Entries missing either key are skipped.
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) that supports `WriteRelationships`.
- Uses **OPERATION_TOUCH**, so sending the same relationships again is idempotent.
- Returns the `WriteRelationshipsResponse` (with `written_at` ZedToken), or `None` if there were no valid updates.

**Example:**
```python
writer.write_clearance_members(
    [
        {"clearance_id": "secret", "user_id": "user-123"},
    ],
    client,
)
```

#### `RelationshipWriter.write_clearance_hierarchy(relationships, client)`

Write clearance hierarchy relationships (higher clearances inherit lower ones).

- **`relationships`:** List of dicts with `higher_clearance_id` and `lower_clearance_id` (strings). Entries missing either key are skipped.
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) that supports `WriteRelationships`.
- Uses **OPERATION_TOUCH**, so sending the same relationships again is idempotent.
- Returns the `WriteRelationshipsResponse` (with `written_at` ZedToken), or `None` if there were no valid updates.

**Example:**
```python
writer.write_clearance_hierarchy(
    [
        {"higher_clearance_id": "top_secret", "lower_clearance_id": "secret"},
        {"higher_clearance_id": "secret", "lower_clearance_id": "confidential"},
    ],
    client,
)
```

#### `RelationshipWriter.write_document_access(relationships, client)`

Write document access control relationships. Each document requires three relationships: viewer_dept (department role), viewer_project (project role), and required_clearance (clearance level).

- **`relationships`:** List of dicts with `document_id`, `viewer_dept_role_id`, `viewer_project_role_id`, and `required_clearance_id` (all strings). Entries missing any required key are skipped.
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) that supports `WriteRelationships`.
- Uses **OPERATION_TOUCH**, so sending the same relationships again is idempotent.
- Returns the `WriteRelationshipsResponse` (with `written_at` ZedToken), or `None` if there were no valid updates.

**Example:**
```python
writer.write_document_access(
    [
        {
            "document_id": "doc-1",
            "viewer_dept_role_id": "engineering",
            "viewer_project_role_id": "project-alpha",
            "required_clearance_id": "secret",
        },
    ],
    client,
)
```

---

### `read_relationships.py`

**Purpose:** Check which doc_ids (document IDs) from a candidate list the user has `view` permission for in SpiceDB. Used in RAG pipelines to filter retrieval results by user permissions.

The `view` permission is computed by SpiceDB based on the user's role memberships (viewer_dept, viewer_project) and clearance level (required_clearance or higher). The read module only needs to check the final permission; SpiceDB handles the complex logic.

**Exports:**
- **`PERMISSION_VIEW`** — Permission name (`"view"`); must match the schema in `apply_schema.SCHEMA`.
- **`RelationshipReader`** — Class that checks viewer permissions for batches of doc_ids.

**`RelationshipReader.get_allowed_doc_ids(user_id, candidates, client)`**
- **`user_id`:** The user to check permissions for (string).
- **`candidates`:** List of dicts from Full Retrieval with at least `doc_id` (document ID). Example: `[{"doc_id": "doc_1", "chunk_id": "...", "score": 0.85}, ...]`
- **`client`:** SpiceDB client (e.g. `authzed.api.v1.InsecureClient`) with `CheckBulkPermissions`.
- Extracts unique doc_ids (document IDs), then uses **CheckBulkPermissions** (one batch call) to check `view` permission on `document` resource type for each doc.
- Returns list of doc_ids (document IDs) that the user is allowed to view (subset of unique doc_ids from candidates).
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
