import sys
from pathlib import Path
import dotenv

# Add project root so "src" is importable when running pytest from any directory
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# tests/test_full_retrieval.py

import math
import pytest
from unittest.mock import MagicMock

from src.user.full_retrieval.full_retriever import FullRetrieval
from langchain_core.embeddings import Embeddings as LangChainEmbeddings
from langchain_chroma import Chroma


class DummyEmbeddings(LangChainEmbeddings):
    """Dummy embeddings class for testing."""
    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Return same dummy vector for each document
        return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.fixture
def dummy_vector_store():
    """Mocked Chroma vector store."""
    mock_collection = MagicMock()
    # Mock collection.count()
    mock_collection.count.return_value = 5
    # Mock collection.query()
    mock_collection.query.return_value = {
        'ids': [['doc1', 'doc2']],
        'distances': [[0.5, 2.0]],
        'metadatas': [[{'doc_id': 'doc1', 'chunk_id': 'chunk1'}, {}]],
        'documents': [['doc1 content', 'doc2 content']]
    }
    mock_store = MagicMock(spec=Chroma)
    mock_store._collection = mock_collection
    return mock_store


def test_init_with_vector_store(dummy_vector_store):
    retriever = FullRetrieval(vector_store=dummy_vector_store)
    assert retriever._vector_store == dummy_vector_store


def test_init_with_path_based(monkeypatch):
    dummy_embeddings = DummyEmbeddings()
    # Mock Chroma constructor
    mock_chroma = MagicMock(spec=Chroma)
    
    # Use the actual module path where FullRetrieval is defined
    monkeypatch.setattr(
        "src.user.full_retrieval.full_retriever.Chroma",
        lambda **kwargs: mock_chroma
    )

    retriever = FullRetrieval(
        persist_directory="test_dir",
        collection_name="test_collection",
        embedding_function=dummy_embeddings
    )
    assert retriever._vector_store == mock_chroma


def test_init_errors():
    # Missing vector_store and path parameters
    with pytest.raises(ValueError):
        FullRetrieval()
    
    # Invalid types
    with pytest.raises(TypeError):
        FullRetrieval(vector_store="not_a_store")
    
    with pytest.raises(TypeError):
        FullRetrieval(
            persist_directory="dir",
            collection_name="col",
            embedding_function="not_embeddings"
        )


def test_search_basic(dummy_vector_store):
    retriever = FullRetrieval(vector_store=dummy_vector_store)
    results = retriever.search([0.1, 0.2, 0.3], threshold=1.0)
    
    assert isinstance(results, list)
    assert len(results) == 1  # Only doc1 is below threshold
    assert results[0]['doc_id'] == 'doc1'
    assert results[0]['chunk_id'] == 'chunk1'
    assert results[0]['score'] == 0.5


def test_search_no_results(dummy_vector_store):
    retriever = FullRetrieval(vector_store=dummy_vector_store)
    # Threshold too low, no results
    results = retriever.search([0.1, 0.2, 0.3], threshold=0.1)
    assert results == []


def test_search_empty_query(dummy_vector_store):
    retriever = FullRetrieval(vector_store=dummy_vector_store)
    results = retriever.search([])
    assert results == []


def test_search_invalid_distance(monkeypatch, dummy_vector_store):
    retriever = FullRetrieval(vector_store=dummy_vector_store)
    # Inject NaN and Inf distances
    dummy_vector_store._collection.query.return_value = {
        'ids': [['doc1', 'doc2']],
        'distances': [[float('nan'), float('inf')]],
        'metadatas': [[{'doc_id': 'doc1'}, {'doc_id': 'doc2'}]],
        'documents': [['doc1', 'doc2']]
    }
    results = retriever.search([0.1, 0.2, 0.3])
    assert results == []


def test_search_missing_metadata(monkeypatch, dummy_vector_store):
    retriever = FullRetrieval(vector_store=dummy_vector_store)
    # Metadata missing
    dummy_vector_store._collection.query.return_value = {
        'ids': [['doc1']],
        'distances': [[0.3]],
        'metadatas': [[]],
        'documents': [['doc1 content']]
    }
    results = retriever.search([0.1, 0.2, 0.3], threshold=1.0)
    assert results[0]['doc_id'] == 'doc1'
    assert results[0]['chunk_id'] == 'doc1'
    assert results[0]['score'] == 0.3
