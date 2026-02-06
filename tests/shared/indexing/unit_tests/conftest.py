"""
Shared pytest fixtures for indexing unit tests.
"""

import sys
from pathlib import Path

# Add project root so "src" is importable when running pytest from any directory
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest
from typing import List
from unittest.mock import MagicMock
from langchain_core.documents import Document


@pytest.fixture
def mock_langchain_embeddings():
    """
    Mock LangChain embeddings provider with embed_query and embed_documents methods.
    Must be a subclass of LangChainEmbeddings to pass isinstance checks.
    """
    from langchain_core.embeddings import Embeddings as LangChainEmbeddings
    
    mock = MagicMock(spec=LangChainEmbeddings)
    # Make isinstance check pass
    mock.__class__ = type('MockEmbeddings', (LangChainEmbeddings,), {})
    mock.embed_query.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    mock.embed_documents.return_value = [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.6, 0.7, 0.8, 0.9, 1.0],
    ]
    return mock


@pytest.fixture
def mock_vector_store():
    """
    Mock VectorStore with add_documents method.
    Must be a subclass of VectorStore to pass isinstance checks.
    """
    from langchain_core.vectorstores import VectorStore
    
    mock = MagicMock(spec=VectorStore)
    # Make isinstance check pass
    mock.__class__ = type('MockVectorStore', (VectorStore,), {})
    mock.add_documents.return_value = None
    return mock


@pytest.fixture
def sample_documents_with_doc_id() -> List[Document]:
    """
    Sample documents with 'doc_id' in metadata.
    """
    return [
        Document(page_content="This is the first document.", metadata={"doc_id": "doc_1"}),
        Document(page_content="This is the second document.", metadata={"doc_id": "doc_2"}),
    ]


@pytest.fixture
def sample_documents_with_document_id() -> List[Document]:
    """
    Sample documents with 'document_id' in metadata (backward compatibility).
    """
    return [
        Document(page_content="First doc content.", metadata={"document_id": "doc_a"}),
        Document(page_content="Second doc content.", metadata={"document_id": "doc_b"}),
    ]


@pytest.fixture
def sample_documents_no_id() -> List[Document]:
    """
    Sample documents without doc_id or document_id in metadata.
    """
    return [
        Document(page_content="Document without ID.", metadata={}),
        Document(page_content="Another document without ID.", metadata={}),
    ]
