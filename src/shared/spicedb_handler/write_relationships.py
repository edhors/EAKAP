"""Write doc-user viewer relationships to SpiceDB."""

from typing import Any, Dict, List

from authzed.api.v1 import (
    ObjectReference,
    Relationship,
    RelationshipUpdate,
    SubjectReference,
    WriteRelationshipsRequest,
)

# Relation name: doc:{doc_id}#viewer@user:{user_id}. Must match schema (see apply_schema.SCHEMA).
RELATION_VIEWER = "viewer"

RESOURCE_TYPE = "doc"
SUBJECT_TYPE = "user"


class RelationshipWriter:
    """Writes doc-user viewer relationships to SpiceDB."""

    def write_relationships(
        self,
        relationships: List[Dict[str, Any]],
        client: Any,
    ) -> Any:
        """Write a list of doc–user viewer relationships to SpiceDB.

        Each item must have keys doc_id and user_id (str). Items missing either key are skipped.
        Uses OPERATION_TOUCH so re-sending the same list is idempotent.

        Args:
            relationships: List of dicts with doc_id and user_id.
            client: SpiceDB client (e.g. InsecureClient) with WriteRelationships.

        Returns:
            WriteRelationshipsResponse (has written_at ZedToken).
        """
        updates = []
        for item in relationships:
            doc_id = item.get("doc_id")
            user_id = item.get("user_id")
            if not doc_id or not user_id:
                continue
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(object_type=RESOURCE_TYPE, object_id=doc_id),
                        relation=RELATION_VIEWER,
                        subject=SubjectReference(
                            object=ObjectReference(object_type=SUBJECT_TYPE, object_id=user_id)
                        ),
                    ),
                )
            )
        if not updates:
            # WriteRelationships with empty updates may be invalid; caller gets empty list written.
            return None
        return client.WriteRelationships(WriteRelationshipsRequest(updates=updates))
