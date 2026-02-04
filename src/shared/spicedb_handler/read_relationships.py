"""Read document-user permissions from SpiceDB."""

from typing import Any, Dict, List

from authzed.api.v1 import (
    CheckBulkPermissionsRequest,
    CheckBulkPermissionsRequestItem,
    CheckPermissionResponse,
    ObjectReference,
    SubjectReference,
)

from .write_relationships import RESOURCE_TYPE, SUBJECT_TYPE

# Permission name: must match schema (see apply_schema.SCHEMA).
PERMISSION_VIEW = "view"


class RelationshipReader:
    """Reads document permissions from SpiceDB."""

    def get_allowed_doc_ids(
        self,
        user_id: str,
        candidates: List[Dict[str, Any]],
        client: Any,
    ) -> List[str]:
        """Get list of doc_ids from candidates that user has view permission for.

        Extracts unique doc_ids (document IDs) from candidates and checks SpiceDB to see which ones
        the user is allowed to view. Uses CheckBulkPermissions for efficiency.
        
        The view permission is computed by SpiceDB based on role membership (viewer_dept, viewer_project)
        and clearance level (required_clearance or higher).

        Args:
            user_id: The user to check permissions for.
            candidates: List of dicts from Full Retrieval with at least doc_id (document ID).
                       Example: [{"doc_id": "doc_1", "chunk_id": "...", "score": 0.85}, ...]
            client: SpiceDB client (e.g. InsecureClient) with CheckBulkPermissions.

        Returns:
            List of doc_ids (document IDs) that user is allowed to view (subset of unique doc_ids from candidates).
            Returns empty list if no candidates or no permissions.

        Example:
            >>> from authzed.api.v1 import InsecureClient
            >>> from src.shared.spicedb_handler.read_relationships import RelationshipReader
            >>> client = InsecureClient("localhost:50051", "test")
            >>> reader = RelationshipReader()
            >>> candidates = [
            ...     {"doc_id": "doc_1", "chunk_id": "doc_1_chunk_0", "score": 0.85},
            ...     {"doc_id": "doc_2", "chunk_id": "doc_2_chunk_0", "score": 0.72},
            ... ]
            >>> allowed = reader.get_allowed_doc_ids("user-123", candidates, client)
            >>> print(allowed)
            ['doc_1']
        """
        # Edge case: empty candidates
        if not candidates:
            return []

        # Step 1: Extract unique doc_ids
        doc_ids = self._extract_doc_ids(candidates)

        # Edge case: no doc_ids after extraction
        if not doc_ids:
            return []

        # Step 2: Build bulk permission check request
        items = []
        for doc_id in doc_ids:
            items.append(
                CheckBulkPermissionsRequestItem(
                    resource=ObjectReference(object_type=RESOURCE_TYPE, object_id=doc_id),
                    permission=PERMISSION_VIEW,
                    subject=SubjectReference(
                        object=ObjectReference(object_type=SUBJECT_TYPE, object_id=user_id)
                    ),
                )
            )

        request = CheckBulkPermissionsRequest(items=items)

        # Step 3: Call SpiceDB
        response = client.CheckBulkPermissions(request)

        # Step 4: Filter by permission
        allowed_doc_ids = []
        for i, pair in enumerate(response.pairs):
            # Check if permission is granted
            if (
                pair.item.permissionship
                == CheckPermissionResponse.Permissionship.PERMISSIONSHIP_HAS_PERMISSION
            ):
                allowed_doc_ids.append(doc_ids[i])

        return allowed_doc_ids

    def _extract_doc_ids(self, candidates: List[Dict[str, Any]]) -> List[str]:
        """Extract unique doc_ids (document IDs) from candidates in order of first occurrence.

        Args:
            candidates: List of dicts from Full Retrieval with at least doc_id (document ID).
                       Example: [{"doc_id": "doc_1", "chunk_id": "...", "score": 0.85}, ...]

        Returns:
            List of unique doc_ids (document IDs) (preserves order of first occurrence).
            Items without doc_id are skipped.
        """
        seen = set()
        doc_ids = []
        for item in candidates:
            doc_id = item.get("doc_id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                doc_ids.append(str(doc_id))
        return doc_ids
