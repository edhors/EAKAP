"""
Indexer class that orchestrates the indexing pipeline: document splitting,
embedding creation, and storage in a vector store.
"""

from typing import List
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from .embeddings import Embeddings
from .text_processor import TextProcessor


class Indexer:
    """
    Orchestrates the indexing pipeline: document splitting, embedding creation,
    and storage in a vector store.
    
    The Indexer coordinates the workflow by:
    1. Splitting documents into chunks using TextProcessor
    2. Assigning unique chunk IDs to each chunk
    3. Adding split documents to the vector store (which automatically creates embeddings)
    """
    
    def __init__(
        self,
        embeddings: Embeddings,
        text_processor: TextProcessor,
        vector_store: VectorStore
    ):
        """
        Initialize the Indexer with required components.
        
        Args:
            embeddings: Embeddings instance (wrapper around LangChain embeddings)
            text_processor: TextProcessor instance for splitting documents
            vector_store: VectorStore instance that must be initialized with the
                        LangChain embeddings function (embeddings._provider)
        
        Raises:
            TypeError: If any parameter is not of the expected type
            ValueError: If vector_store is not properly initialized
        """
        if not isinstance(embeddings, Embeddings):
            raise TypeError(
                f"embeddings must be an Embeddings instance, "
                f"got {type(embeddings).__name__}"
            )
        
        if not isinstance(text_processor, TextProcessor):
            raise TypeError(
                f"text_processor must be a TextProcessor instance, "
                f"got {type(text_processor).__name__}"
            )
        
        if not isinstance(vector_store, VectorStore):
            raise TypeError(
                f"vector_store must be a VectorStore instance, "
                f"got {type(vector_store).__name__}"
            )
        
        # Check that vector_store has the required method
        if not hasattr(vector_store, 'add_documents'):
            raise ValueError(
                "vector_store must have an 'add_documents' method. "
                "Ensure the vector store is properly initialized with the embeddings function."
            )
        
        self._embeddings = embeddings
        self._text_processor = text_processor
        self._vector_store = vector_store
    
    def index(self, documents: List[Document]) -> None:
        """
        Process documents through the indexing pipeline and store them.
        
        The pipeline:
        1. Splits documents into chunks using TextProcessor
        2. Assigns unique chunk IDs to each chunk
        3. Adds split documents to the vector store (embeddings are created automatically)
        
        Args:
            documents: List of LangChain Document objects to index. Each document's
                      metadata should contain a 'doc_id' field (or 'document_id' for
                      backward compatibility) to uniquely identify the document. If not
                      provided, 'default' will be used.
        
        Returns:
            None
        
        Raises:
            ValueError: If documents list is empty or None
            TypeError: If documents is not a list or contains invalid items
            RuntimeError: If indexing fails at any step
        
        Note:
            Chunk IDs are assigned in the format: {doc_id}_chunk_{incremental_index}
            where doc_id comes from metadata (preferring 'doc_id', falling back to
            'document_id' for backward compatibility).
        """
        if not documents:
            raise ValueError("documents list cannot be empty or None")
        
        if not isinstance(documents, list):
            raise TypeError("documents must be a list")
        
        if not all(isinstance(doc, Document) for doc in documents):
            raise TypeError("All items in documents must be Document instances")
        
        try:
            # Step 1: Split documents into chunks
            split_documents = self._text_processor.split_documents(documents)
            
            # Step 2: Add unique chunk IDs to split documents
            # Track chunk indices per doc_id to ensure uniqueness across all chunks
            chunk_counter = {}  # {doc_id: counter}
            
            for chunk in split_documents:
                # Ensure we have a fresh metadata dict (not shared reference)
                # This is critical because split_documents may share metadata references
                if chunk.metadata is None:
                    chunk.metadata = {}
                else:
                    # Create a deep copy to avoid shared references
                    chunk.metadata = dict(chunk.metadata)
                
                # Get or create doc_id for this chunk (with backward compatibility for document_id)
                doc_id = chunk.metadata.get("doc_id") or chunk.metadata.get("document_id", "default")
                
                # Initialize counter for this doc_id if not exists
                if doc_id not in chunk_counter:
                    chunk_counter[doc_id] = 0
                
                # Always overwrite chunk_id to ensure uniqueness and proper incrementing
                # Format: {doc_id}_chunk_{incremental_index}
                chunk.metadata["chunk_id"] = f"{doc_id}_chunk_{chunk_counter[doc_id]}"
                chunk_counter[doc_id] += 1
            
            # Step 3: Add split documents to vector store
            # The vector store automatically creates embeddings using the embeddings function
            # it was initialized with
            self._vector_store.add_documents(split_documents)
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to index documents: {str(e)}"
            ) from e
