"""One-off script to apply the RBAC schema (user/role/clearance/document) to SpiceDB."""

import sys

from authzed.api.v1 import InsecureClient, ReadSchemaRequest, WriteSchemaRequest

# Schema: User-based access control via roles and clearances.
# Documents grant view permission when user is in required department role,
# project role, and meets (or exceeds) the required clearance level.
# See SPEC.md and SPICEDB_OPERATIONS.md.
SCHEMA = """
definition user {}

definition role {
  relation member: user
}

definition clearance {
  relation member: user
  relation higher_clearance: clearance
  permission effective_member = member + higher_clearance->effective_member
}

definition document {
  relation viewer_dept: role
  relation viewer_project: role
  relation required_clearance: clearance
  permission view = viewer_dept->member & viewer_project->member & required_clearance->effective_member
}
"""


def main() -> None:
    endpoint = "localhost:50051"
    token = "test"
    if len(sys.argv) >= 2:
        endpoint = sys.argv[1]
    if len(sys.argv) >= 3:
        token = sys.argv[2]

    client = InsecureClient(endpoint, token)
    client.WriteSchema(WriteSchemaRequest(schema=SCHEMA.strip()))
    resp = client.ReadSchema(ReadSchemaRequest())
    print("Schema applied successfully. Current schema:")
    print(resp.schema_text)


if __name__ == "__main__":
    main()
