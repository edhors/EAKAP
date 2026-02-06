"""
Unit tests for the Indexer class.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from src.shared.indexing.indexer import Indexer
from src.shared.indexing.embeddings import Embeddings
from src.shared.indexing.text_processor import TextProcessor


class TestIndexerInit:
    """Tests for Indexer.__init__"""

    def test_init_accepts_valid_embeddings_text_processor_vector_store(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should successfully initialize with valid components."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        assert indexer._embeddings == embeddings
        assert indexer._text_processor == text_processor
        assert indexer._vector_store == mock_vector_store

    def test_init_raises_type_error_for_invalid_embeddings(self, mock_vector_store):
        """Should raise TypeError if embeddings is not an Embeddings instance."""
        text_processor = TextProcessor()
        
        with pytest.raises(TypeError, match="embeddings must be an Embeddings instance"):
            Indexer("not_embeddings", text_processor, mock_vector_store)

    def test_init_raises_type_error_for_invalid_text_processor(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should raise TypeError if text_processor is not a TextProcessor instance."""
        embeddings = Embeddings(mock_langchain_embeddings)
        
        with pytest.raises(TypeError, match="text_processor must be a TextProcessor instance"):
            Indexer(embeddings, "not_text_processor", mock_vector_store)

    def test_init_raises_type_error_for_invalid_vector_store(
        self, mock_langchain_embeddings
    ):
        """Should raise TypeError if vector_store is not a VectorStore instance."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        
        with pytest.raises(TypeError, match="vector_store must be a VectorStore instance"):
            Indexer(embeddings, text_processor, "not_vector_store")

    def test_init_raises_value_error_when_vector_store_lacks_add_documents(
        self, mock_langchain_embeddings
    ):
        """Should raise ValueError if vector_store doesn't have add_documents method."""
        from langchain_core.vectorstores import VectorStore
        
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        
        # Create a mock that passes isinstance check but lacks add_documents
        invalid_store = MagicMock(spec=[])  # Empty spec, no methods
        invalid_store.__class__ = type('InvalidVectorStore', (VectorStore,), {})
        
        # Make sure hasattr check for add_documents fails
        del invalid_store.add_documents
        
        with pytest.raises(ValueError, match="vector_store must have an 'add_documents' method"):
            Indexer(embeddings, text_processor, invalid_store)


class TestIndexerIndex:
    """Tests for Indexer.index"""

    def test_index_calls_text_processor_split_then_vector_store_add_documents(
        self, mock_langchain_embeddings, mock_vector_store, sample_documents_with_doc_id
    ):
        """Should call text_processor.split_documents then vector_store.add_documents."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        with patch.object(text_processor, 'split_documents') as mock_split:
            # Mock split to return some chunks
            mock_split.return_value = [
                Document(page_content="chunk1", metadata={"doc_id": "doc_1"}),
                Document(page_content="chunk2", metadata={"doc_id": "doc_1"}),
            ]
            
            indexer.index(sample_documents_with_doc_id)
            
            # Verify split_documents was called
            mock_split.assert_called_once_with(sample_documents_with_doc_id)
            
            # Verify add_documents was called
            mock_vector_store.add_documents.assert_called_once()
            added_docs = mock_vector_store.add_documents.call_args[0][0]
            assert len(added_docs) == 2

    def test_index_assigns_chunk_id_per_doc_format_doc_id_chunk_index(
        self, mock_langchain_embeddings, mock_vector_store, sample_documents_with_doc_id
    ):
        """Should assign chunk_id in format: {doc_id}_chunk_{index}."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        indexer.index(sample_documents_with_doc_id)
        
        # Get the documents that were added
        added_docs = mock_vector_store.add_documents.call_args[0][0]
        
        # Check chunk_id format
        for doc in added_docs:
            assert "chunk_id" in doc.metadata
            chunk_id = doc.metadata["chunk_id"]
            # Should be in format: doc_X_chunk_Y
            assert "_chunk_" in chunk_id
            assert chunk_id.startswith("doc_")

    def test_index_uses_document_id_fallback_when_doc_id_missing(
        self, mock_langchain_embeddings, mock_vector_store, sample_documents_with_document_id
    ):
        """Should use 'document_id' metadata field if 'doc_id' is not present."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        indexer.index(sample_documents_with_document_id)
        
        # Get the documents that were added
        added_docs = mock_vector_store.add_documents.call_args[0][0]
        
        # Check that chunk_ids use document_id
        for doc in added_docs:
            chunk_id = doc.metadata["chunk_id"]
            # Should use doc_a or doc_b from document_id
            assert "doc_a" in chunk_id or "doc_b" in chunk_id

    def test_index_uses_default_doc_id_when_no_id_in_metadata(
        self, mock_langchain_embeddings, mock_vector_store, sample_documents_no_id
    ):
        """Should use 'default' as doc_id when neither doc_id nor document_id is present."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        indexer.index(sample_documents_no_id)
        
        # Get the documents that were added
        added_docs = mock_vector_store.add_documents.call_args[0][0]
        
        # Check that chunk_ids use 'default'
        for doc in added_docs:
            chunk_id = doc.metadata["chunk_id"]
            assert chunk_id.startswith("default_chunk_")

    def test_index_raises_value_error_for_empty_documents_list(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should raise ValueError for empty documents list."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        with pytest.raises(ValueError, match="documents list cannot be empty or None"):
            indexer.index([])

    def test_index_raises_value_error_for_none_documents(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should raise ValueError for None documents."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        with pytest.raises(ValueError, match="documents list cannot be empty or None"):
            indexer.index(None)

    def test_index_raises_type_error_for_non_list_documents(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should raise TypeError for non-list documents."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        with pytest.raises(TypeError, match="documents must be a list"):
            indexer.index("not a list")

    def test_index_raises_type_error_when_items_not_documents(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should raise TypeError if items in list are not Document instances."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        with pytest.raises(TypeError, match="All items in documents must be Document instances"):
            indexer.index(["not", "documents"])

    def test_index_does_not_share_metadata_reference_across_chunks(
        self, mock_langchain_embeddings, mock_vector_store
    ):
        """Should not share metadata references across chunks (each should be independent)."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        # Create a document that will be split into multiple chunks
        doc = Document(
            page_content="This is a long text. " * 10,
            metadata={"doc_id": "test_doc", "shared_key": "original"}
        )
        
        indexer.index([doc])
        
        # Get the added documents
        added_docs = mock_vector_store.add_documents.call_args[0][0]
        
        # Verify multiple chunks were created
        assert len(added_docs) > 1
        
        # Mutate the first chunk's metadata
        added_docs[0].metadata["shared_key"] = "modified"
        
        # Verify other chunks are not affected
        for doc in added_docs[1:]:
            assert doc.metadata["shared_key"] == "original"

    def test_index_raises_runtime_error_when_split_documents_fails(
        self, mock_langchain_embeddings, mock_vector_store, sample_documents_with_doc_id
    ):
        """Should raise RuntimeError if split_documents fails."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        with patch.object(text_processor, 'split_documents') as mock_split:
            mock_split.side_effect = Exception("Split error")
            
            with pytest.raises(RuntimeError, match="Failed to index documents"):
                indexer.index(sample_documents_with_doc_id)

    def test_index_raises_runtime_error_when_add_documents_fails(
        self, mock_langchain_embeddings, mock_vector_store, sample_documents_with_doc_id
    ):
        """Should raise RuntimeError if vector_store.add_documents fails."""
        embeddings = Embeddings(mock_langchain_embeddings)
        text_processor = TextProcessor()
        indexer = Indexer(embeddings, text_processor, mock_vector_store)
        
        mock_vector_store.add_documents.side_effect = Exception("VectorStore error")
        
        with pytest.raises(RuntimeError, match="Failed to index documents"):
            indexer.index(sample_documents_with_doc_id)
