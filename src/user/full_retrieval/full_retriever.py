"""
FullRetrieval module for performing distance-based search using pre-computed query embeddings
against a ChromaDB vectorstore.
"""

import math
from typing import List, Dict, Optional, Any
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings as LangChainEmbeddings


class FullRetrieval:
    """
    Performs distance-based search using pre-computed query embeddings against a ChromaDB vectorstore.
    
    Returns ChromaDB distances directly (lower values = more similar).
    
    Supports initialization with either:
    - Path-based: persist_directory, collection_name, and embedding_function
    - Dependency injection: existing vector_store instance
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_function: Optional[LangChainEmbeddings] = None,
        vector_store: Optional[Chroma] = None
    ):
        """
        Initialize FullRetrieval with either path-based or dependency injection approach.
        
        Args:
            persist_directory: Path to ChromaDB persistence directory (required if vector_store not provided)
            collection_name: Name of the ChromaDB collection (required if vector_store not provided)
            embedding_function: LangChain embeddings instance (required if vector_store not provided)
            vector_store: Existing Chroma vectorstore instance (alternative to path-based init)
        
        Raises:
            ValueError: If neither vector_store nor required path parameters are provided
            TypeError: If types are incorrect
        """
        if vector_store is not None:
            # Dependency injection: use provided vectorstore
            if not isinstance(vector_store, Chroma):
                raise TypeError(
                    f"vector_store must be a Chroma instance, "
                    f"got {type(vector_store).__name__}"
                )
            self._vector_store = vector_store
        else:
            # Path-based initialization
            if not persist_directory or not isinstance(persist_directory, str):
                raise ValueError("persist_directory is required and must be a non-empty string when vector_store is not provided")
            
            if not collection_name or not isinstance(collection_name, str):
                raise ValueError("collection_name is required and must be a non-empty string when vector_store is not provided")
            
            if not embedding_function:
                raise ValueError("embedding_function is required when vector_store is not provided")
            if not isinstance(embedding_function, LangChainEmbeddings):
                raise TypeError(
                    f"embedding_function must be a LangChain Embeddings instance, "
                    f"got {type(embedding_function).__name__}"
                )
            
            # Initialize ChromaDB
            self._vector_store = Chroma(
                persist_directory=persist_directory,
                collection_name=collection_name,
                embedding_function=embedding_function
            )
    
    def search(
        self,
        query_embeddings: List[float],
        threshold: float = 1.5,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform distance-based search using pre-computed query embeddings.
        
        Args:
            query_embeddings: List of float values representing the query embedding vector
            threshold: Maximum distance to include in results (lower = more similar). Default is 1.0.
            k: Optional maximum number of results to return before threshold filtering
        
        Returns:
            List of dictionaries with keys: doc_id, chunk_id, score
            The 'score' field contains the distance (lower values = more similar).
            Format: [{"doc_id": str, "chunk_id": str, "score": float}, ...]
        """
        if not query_embeddings:
            return []
        
        # Access underlying ChromaDB collection
        collection = self._vector_store._collection
        
        # Get collection count
        collection_count = collection.count()
        if collection_count == 0:
            return []
        
        # Determine n_results: use k if provided, otherwise get all results
        # ChromaDB will return results sorted by distance (ascending)
        n_results = k if k is not None else max(collection_count, 10000)
        
        # Perform query with embeddings directly
        results = collection.query(
            query_embeddings=[query_embeddings],
            n_results=n_results
        )
        
        # Process results
        # ChromaDB returns: {'ids', 'distances', 'metadatas', 'documents'}
        if not results.get('ids') or not results['ids'][0]:
            return []
        
        ids = results['ids'][0]
        distances = results['distances'][0]
        metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
        
        processed_results = []
        
        for i, (doc_id, distance) in enumerate(zip(ids, distances)):
            distance = float(distance)
            
            # Skip invalid distance values
            if math.isnan(distance) or math.isinf(distance):
                continue
            
            # Filter by threshold (keep if distance <= threshold)
            if distance > threshold:
                continue
            
            # Extract metadata
            metadata = metadatas[i] if i < len(metadatas) and isinstance(metadatas[i], dict) else {}
            
            # Extract doc_id and chunk_id from metadata, with fallback to id
            doc_id_meta = metadata.get('doc_id') if metadata else None
            chunk_id = metadata.get('chunk_id') if metadata else None
            
            # Fallback: if metadata is missing, use the id itself
            if doc_id_meta is None:
                doc_id_meta = str(doc_id) if doc_id is not None else f"unknown_{i}"
            if chunk_id is None:
                chunk_id = str(doc_id) if doc_id is not None else f"unknown_{i}"
            
            processed_results.append({
                "doc_id": str(doc_id_meta),
                "chunk_id": str(chunk_id),
                "score": distance
            })
        
        return processed_results
