"""
Unit tests for the Embeddings class.
"""

import pytest
from unittest.mock import MagicMock
from src.shared.indexing.embeddings import Embeddings


class TestEmbeddingsInit:
    """Tests for Embeddings.__init__"""

    def test_init_accepts_valid_langchain_embeddings(self, mock_langchain_embeddings):
        """Should successfully initialize with a valid LangChain embeddings provider."""
        embeddings = Embeddings(mock_langchain_embeddings)
        assert embeddings._provider == mock_langchain_embeddings

    def test_init_raises_type_error_for_non_embeddings_provider(self):
        """Should raise TypeError if provider is not a LangChain Embeddings instance."""
        with pytest.raises(TypeError, match="Provider must be a LangChain Embeddings instance"):
            Embeddings("not_an_embeddings_provider")


class TestEmbedQuery:
    """Tests for Embeddings.embed_query"""

    def test_embed_query_returns_list_of_floats(self, mock_langchain_embeddings):
        """Should return a list of floats when embedding a valid query."""
        embeddings = Embeddings(mock_langchain_embeddings)
        result = embeddings.embed_query("What is machine learning?")
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(x, float) for x in result)
        mock_langchain_embeddings.embed_query.assert_called_once_with("What is machine learning?")

    def test_embed_query_raises_value_error_for_empty_text(self, mock_langchain_embeddings):
        """Should raise ValueError for empty string."""
        embeddings = Embeddings(mock_langchain_embeddings)
        with pytest.raises(ValueError, match="text must be a non-empty string"):
            embeddings.embed_query("")

    def test_embed_query_raises_value_error_for_none_text(self, mock_langchain_embeddings):
        """Should raise ValueError for None."""
        embeddings = Embeddings(mock_langchain_embeddings)
        with pytest.raises(ValueError, match="text must be a non-empty string"):
            embeddings.embed_query(None)

    def test_embed_query_raises_value_error_for_non_string(self, mock_langchain_embeddings):
        """Should raise ValueError for non-string input."""
        embeddings = Embeddings(mock_langchain_embeddings)
        with pytest.raises(ValueError, match="text must be a non-empty string"):
            embeddings.embed_query(123)

    def test_embed_query_raises_runtime_error_when_provider_fails(self, mock_langchain_embeddings):
        """Should raise RuntimeError if the provider's embed_query fails."""
        mock_langchain_embeddings.embed_query.side_effect = Exception("API error")
        embeddings = Embeddings(mock_langchain_embeddings)
        
        with pytest.raises(RuntimeError, match="Failed to embed query"):
            embeddings.embed_query("test query")


class TestEmbedChunks:
    """Tests for Embeddings.embed_chunks"""

    def test_embed_chunks_returns_list_of_embeddings(self, mock_langchain_embeddings):
        """Should return a list of embedding vectors for valid chunks."""
        embeddings = Embeddings(mock_langchain_embeddings)
        texts = ["Chunk 1", "Chunk 2"]
        result = embeddings.embed_chunks(texts)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(emb, list) for emb in result)
        mock_langchain_embeddings.embed_documents.assert_called_once_with(texts)

    def test_embed_chunks_raises_value_error_for_empty_list(self, mock_langchain_embeddings):
        """Should raise ValueError for empty list."""
        embeddings = Embeddings(mock_langchain_embeddings)
        with pytest.raises(ValueError, match="texts must be a non-empty list"):
            embeddings.embed_chunks([])

    def test_embed_chunks_raises_value_error_for_non_list(self, mock_langchain_embeddings):
        """Should raise ValueError for non-list input."""
        embeddings = Embeddings(mock_langchain_embeddings)
        with pytest.raises(ValueError, match="texts must be a list of strings"):
            embeddings.embed_chunks("not a list")

    def test_embed_chunks_raises_value_error_when_items_not_non_empty_strings(self, mock_langchain_embeddings):
        """Should raise ValueError if any item is not a non-empty string."""
        embeddings = Embeddings(mock_langchain_embeddings)
        
        # Test with empty string
        with pytest.raises(ValueError, match="All items in texts must be non-empty strings"):
            embeddings.embed_chunks(["valid", ""])
        
        # Test with None
        with pytest.raises(ValueError, match="All items in texts must be non-empty strings"):
            embeddings.embed_chunks(["valid", None])
        
        # Test with non-string
        with pytest.raises(ValueError, match="All items in texts must be non-empty strings"):
            embeddings.embed_chunks(["valid", 123])

    def test_embed_chunks_raises_runtime_error_when_provider_fails(self, mock_langchain_embeddings):
        """Should raise RuntimeError if the provider's embed_documents fails."""
        mock_langchain_embeddings.embed_documents.side_effect = Exception("API error")
        embeddings = Embeddings(mock_langchain_embeddings)
        
        with pytest.raises(RuntimeError, match="Failed to embed chunks"):
            embeddings.embed_chunks(["chunk1", "chunk2"])
