"""Write RBAC relationships (roles, clearances, document access) to SpiceDB."""

from typing import Any, Dict, List

from authzed.api.v1 import (
    ObjectReference,
    Relationship,
    RelationshipUpdate,
    SubjectReference,
    WriteRelationshipsRequest,
)

# Resource types (must match schema in apply_schema.SCHEMA)
RESOURCE_TYPE = "document"  # For read module compatibility
RESOURCE_TYPE_DOCUMENT = "document"
RESOURCE_TYPE_ROLE = "role"
RESOURCE_TYPE_CLEARANCE = "clearance"
SUBJECT_TYPE = "user"

# Relation names (must match schema in apply_schema.SCHEMA)
RELATION_MEMBER = "member"
RELATION_HIGHER_CLEARANCE = "higher_clearance"
RELATION_VIEWER_DEPT = "viewer_dept"
RELATION_VIEWER_PROJECT = "viewer_project"
RELATION_REQUIRED_CLEARANCE = "required_clearance"


class RelationshipWriter:
    """Writes RBAC relationships (roles, clearances, document access) to SpiceDB."""

    def write_role_members(
        self,
        relationships: List[Dict[str, Any]],
        client: Any,
    ) -> Any:
        """Write role membership relationships to SpiceDB.

        Each item must have keys role_id and user_id (str). Items missing either key are skipped.
        Uses OPERATION_TOUCH so re-sending the same list is idempotent.

        Args:
            relationships: List of dicts with role_id and user_id.
            client: SpiceDB client (e.g. InsecureClient) with WriteRelationships.

        Returns:
            WriteRelationshipsResponse (has written_at ZedToken), or None if no valid updates.
        
        Example:
            >>> writer = RelationshipWriter()
            >>> writer.write_role_members([
            ...     {"role_id": "engineering", "user_id": "user-123"},
            ...     {"role_id": "project-alpha", "user_id": "user-123"},
            ... ], client)
        """
        updates = []
        for item in relationships:
            role_id = item.get("role_id")
            user_id = item.get("user_id")
            if not role_id or not user_id:
                continue
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(object_type=RESOURCE_TYPE_ROLE, object_id=role_id),
                        relation=RELATION_MEMBER,
                        subject=SubjectReference(
                            object=ObjectReference(object_type=SUBJECT_TYPE, object_id=user_id)
                        ),
                    ),
                )
            )
        if not updates:
            return None
        return client.WriteRelationships(WriteRelationshipsRequest(updates=updates))

    def write_clearance_members(
        self,
        relationships: List[Dict[str, Any]],
        client: Any,
    ) -> Any:
        """Write clearance membership relationships to SpiceDB.

        Each item must have keys clearance_id and user_id (str). Items missing either key are skipped.
        Uses OPERATION_TOUCH so re-sending the same list is idempotent.

        Args:
            relationships: List of dicts with clearance_id and user_id.
            client: SpiceDB client (e.g. InsecureClient) with WriteRelationships.

        Returns:
            WriteRelationshipsResponse (has written_at ZedToken), or None if no valid updates.
        
        Example:
            >>> writer = RelationshipWriter()
            >>> writer.write_clearance_members([
            ...     {"clearance_id": "secret", "user_id": "user-123"},
            ... ], client)
        """
        updates = []
        for item in relationships:
            clearance_id = item.get("clearance_id")
            user_id = item.get("user_id")
            if not clearance_id or not user_id:
                continue
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(
                            object_type=RESOURCE_TYPE_CLEARANCE, object_id=clearance_id
                        ),
                        relation=RELATION_MEMBER,
                        subject=SubjectReference(
                            object=ObjectReference(object_type=SUBJECT_TYPE, object_id=user_id)
                        ),
                    ),
                )
            )
        if not updates:
            return None
        return client.WriteRelationships(WriteRelationshipsRequest(updates=updates))

    def write_clearance_hierarchy(
        self,
        relationships: List[Dict[str, Any]],
        client: Any,
    ) -> Any:
        """Write clearance hierarchy relationships to SpiceDB.

        Each item must have keys higher_clearance_id and lower_clearance_id (str).
        Items missing either key are skipped.
        Uses OPERATION_TOUCH so re-sending the same list is idempotent.

        Args:
            relationships: List of dicts with higher_clearance_id and lower_clearance_id.
            client: SpiceDB client (e.g. InsecureClient) with WriteRelationships.

        Returns:
            WriteRelationshipsResponse (has written_at ZedToken), or None if no valid updates.
        
        Example:
            >>> writer = RelationshipWriter()
            >>> writer.write_clearance_hierarchy([
            ...     {"higher_clearance_id": "top_secret", "lower_clearance_id": "secret"},
            ...     {"higher_clearance_id": "secret", "lower_clearance_id": "confidential"},
            ... ], client)
        """
        updates = []
        for item in relationships:
            higher_clearance_id = item.get("higher_clearance_id")
            lower_clearance_id = item.get("lower_clearance_id")
            if not higher_clearance_id or not lower_clearance_id:
                continue
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(
                            object_type=RESOURCE_TYPE_CLEARANCE, object_id=higher_clearance_id
                        ),
                        relation=RELATION_HIGHER_CLEARANCE,
                        subject=SubjectReference(
                            object=ObjectReference(
                                object_type=RESOURCE_TYPE_CLEARANCE, object_id=lower_clearance_id
                            )
                        ),
                    ),
                )
            )
        if not updates:
            return None
        return client.WriteRelationships(WriteRelationshipsRequest(updates=updates))

    def write_document_access(
        self,
        relationships: List[Dict[str, Any]],
        client: Any,
    ) -> Any:
        """Write document access control relationships to SpiceDB.

        Each item must have keys document_id, viewer_dept_role_id, viewer_project_role_id,
        and required_clearance_id (all str). Items missing any required key are skipped.
        For each valid document, writes three relationships: viewer_dept, viewer_project,
        and required_clearance.
        Uses OPERATION_TOUCH so re-sending the same list is idempotent.

        Args:
            relationships: List of dicts with document_id, viewer_dept_role_id,
                          viewer_project_role_id, required_clearance_id.
            client: SpiceDB client (e.g. InsecureClient) with WriteRelationships.

        Returns:
            WriteRelationshipsResponse (has written_at ZedToken), or None if no valid updates.
        
        Example:
            >>> writer = RelationshipWriter()
            >>> writer.write_document_access([
            ...     {
            ...         "document_id": "doc-1",
            ...         "viewer_dept_role_id": "engineering",
            ...         "viewer_project_role_id": "project-alpha",
            ...         "required_clearance_id": "secret",
            ...     },
            ... ], client)
        """
        updates = []
        for item in relationships:
            document_id = item.get("document_id")
            viewer_dept_role_id = item.get("viewer_dept_role_id")
            viewer_project_role_id = item.get("viewer_project_role_id")
            required_clearance_id = item.get("required_clearance_id")
            
            if not all([document_id, viewer_dept_role_id, viewer_project_role_id, required_clearance_id]):
                continue
            
            # Add viewer_dept relationship
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(
                            object_type=RESOURCE_TYPE_DOCUMENT, object_id=document_id
                        ),
                        relation=RELATION_VIEWER_DEPT,
                        subject=SubjectReference(
                            object=ObjectReference(
                                object_type=RESOURCE_TYPE_ROLE, object_id=viewer_dept_role_id
                            )
                        ),
                    ),
                )
            )
            
            # Add viewer_project relationship
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(
                            object_type=RESOURCE_TYPE_DOCUMENT, object_id=document_id
                        ),
                        relation=RELATION_VIEWER_PROJECT,
                        subject=SubjectReference(
                            object=ObjectReference(
                                object_type=RESOURCE_TYPE_ROLE, object_id=viewer_project_role_id
                            )
                        ),
                    ),
                )
            )
            
            # Add required_clearance relationship
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(
                            object_type=RESOURCE_TYPE_DOCUMENT, object_id=document_id
                        ),
                        relation=RELATION_REQUIRED_CLEARANCE,
                        subject=SubjectReference(
                            object=ObjectReference(
                                object_type=RESOURCE_TYPE_CLEARANCE, object_id=required_clearance_id
                            )
                        ),
                    ),
                )
            )
        
        if not updates:
            return None
        return client.WriteRelationships(WriteRelationshipsRequest(updates=updates))
