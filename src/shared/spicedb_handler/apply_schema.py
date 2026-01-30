"""One-off script to apply the user/doc/viewer schema to SpiceDB."""

import sys

from authzed.api.v1 import InsecureClient, ReadSchemaRequest, WriteSchemaRequest

# Schema: one relation (viewer), one permission (view).
# See SPEC.md and SPICEDB_OPERATIONS.md.
SCHEMA = """
definition user {}

definition doc {
    relation viewer: user
    permission view = viewer
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
