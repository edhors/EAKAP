from typing import Optional
from sqlmodel import Session
from .models import Document


class DocumentService:
    """Service for document CRUD operations."""

    def __init__(self, session: Session):
        self._session = session

    def create_doc(self, dept: str, project: str, clearance: int, url: str) -> Document:
        """Create a new document."""
        document = Document(dept=dept, project=project, clearance=clearance, url=url)
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        return document

    def get_doc_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self._session.get(Document, document_id)


    def delete_doc(self, document_id: str) -> bool:
        """Delete a document."""
        document = self.get_doc_by_id(document_id)
        if not document:
            return False
        self._session.delete(document)
        self._session.commit()
        return True


