"""
FullRetrieval module for performing similarity search using pre-computed query embeddings
against a ChromaDB vectorstore.
"""

import math
from typing import List, Dict, Optional, Any
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings as LangChainEmbeddings


class FullRetrieval:
    """
    Performs similarity search using pre-computed query embeddings against a ChromaDB vectorstore.
    
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
            TypeError: If embedding_function is not a LangChain Embeddings instance when using path-based init
            RuntimeError: If ChromaDB initialization fails (connection errors, invalid path, etc.)
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
            
            # Initialize ChromaDB with error handling
            try:
                self._vector_store = Chroma(
                    persist_directory=persist_directory,
                    collection_name=collection_name,
                    embedding_function=embedding_function
                )
            except FileNotFoundError as e:
                raise RuntimeError(
                    f"ChromaDB persistence directory not found: {persist_directory}. "
                    f"Ensure the directory exists and is accessible."
                ) from e
            except PermissionError as e:
                raise RuntimeError(
                    f"Permission denied accessing ChromaDB directory: {persist_directory}. "
                    f"Check file permissions."
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Failed to initialize ChromaDB vectorstore: {str(e)}. "
                    f"Check that persist_directory='{persist_directory}' and "
                    f"collection_name='{collection_name}' are valid."
                ) from e
    
    def search(
        self,
        query_embeddings: List[float],
        threshold: float = 0.5,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using pre-computed query embeddings.
        
        Args:
            query_embeddings: List of float values representing the query embedding vector
            threshold: Minimum similarity score (0-1) to include in results. Default is 0.5.
            k: Optional maximum number of results to return before threshold filtering
        
        Returns:
            List of dictionaries with keys: doc_id, chunk_id, score
            Format: [{"doc_id": str, "chunk_id": str, "score": float}, ...]
        
        Raises:
            ValueError: If query_embeddings is empty, contains invalid values, or threshold is not between 0 and 1
            RuntimeError: If ChromaDB query fails, collection is inaccessible, or metadata extraction fails
        """
        # Validate query_embeddings
        if not query_embeddings:
            raise ValueError("query_embeddings must be a non-empty list")
        if not isinstance(query_embeddings, list):
            raise TypeError(
                f"query_embeddings must be a list, got {type(query_embeddings).__name__}"
            )
        
        # Validate all items are numeric and convert to float
        try:
            query_embeddings = [float(x) for x in query_embeddings]
        except (ValueError, TypeError) as e:
            raise ValueError(
                "All items in query_embeddings must be numeric (int or float). "
                f"Found invalid value: {str(e)}"
            ) from e
        
        # Check for NaN or Infinity values (ChromaDB will reject these anyway, but fail fast)
        for i, val in enumerate(query_embeddings):
            if math.isnan(val) or math.isinf(val):
                raise ValueError(
                    f"query_embeddings contains invalid value at index {i} "
                    f"(NaN or Infinity). All values must be finite numbers."
                )
        
        # Validate threshold
        if not isinstance(threshold, (int, float)):
            raise TypeError(
                f"threshold must be a number, got {type(threshold).__name__}"
            )
        threshold = float(threshold)
        if not (0 <= threshold <= 1):
            raise ValueError(
                f"threshold must be between 0 and 1 (inclusive), got {threshold}"
            )
        
        # Validate k
        if k is not None:
            if not isinstance(k, int):
                raise TypeError(f"k must be an integer, got {type(k).__name__}")
            if k <= 0:
                raise ValueError(f"k must be a positive integer, got {k}")
        
        try:
            # Access underlying ChromaDB collection
            collection = self._vector_store._collection
            if collection is None:
                raise RuntimeError(
                    "ChromaDB collection is None. "
                    "The collection may not have been initialized properly."
                )
            
            # Get collection count
            collection_count = collection.count()
            if collection_count == 0:
                return []  # Empty collection, return empty results
            
            # Determine n_results: use k if provided, otherwise get all results
            # ChromaDB will return results sorted by distance (ascending)
            # When k is None, use a large number to get all results
            n_results = k if k is not None else max(collection_count, 10000)
            
            # Perform query with embeddings directly
            # ChromaDB's query method accepts query_embeddings as a list
            try:
                results = collection.query(
                    query_embeddings=[query_embeddings],
                    n_results=n_results
                )
            except ValueError as e:
                # Handle dimension mismatch or invalid embedding format
                raise RuntimeError(
                    f"Invalid query embeddings format or dimension mismatch: {str(e)}. "
                    "Ensure query_embeddings matches the embedding dimension of the collection."
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"ChromaDB query operation failed: {str(e)}. "
                    "Check that the collection is accessible and the embeddings are valid."
                ) from e
            
            # Process results
            # ChromaDB returns: {'ids', 'distances', 'metadatas', 'documents'}
            # distances is a list of lists (one list per query embedding)
            # For a single query, we get distances[0]
            if not results.get('ids') or not results['ids'][0]:
                return []
            
            ids = results['ids'][0]
            distances = results['distances'][0]
            
            # Extract metadatas (ChromaDB guarantees structure)
            metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
            
            # Convert distances to similarity scores
            # For cosine similarity: similarity = 1 - distance
            # (ChromaDB uses cosine distance where 0 = identical, 2 = opposite)
            processed_results = []
            
            for i, (doc_id, distance) in enumerate(zip(ids, distances)):
                # Convert distance to float (ChromaDB always returns numeric)
                distance = float(distance)
                
                # Skip invalid distance values
                if math.isnan(distance) or math.isinf(distance):
                    continue
                
                # Convert distance to similarity score (1 - distance for cosine)
                # Clamp to [0, 1] range in case distance > 1
                similarity_score = max(0.0, min(1.0, 1.0 - distance))
                
                # Filter by threshold
                if similarity_score < threshold:
                    continue
                
                # Extract metadata (safe access with fallback)
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
                    "score": similarity_score
                })
            
            return processed_results
            
        except AttributeError as e:
            raise RuntimeError(
                f"Failed to access ChromaDB collection: {str(e)}. "
                "Ensure the vector_store is properly initialized and has a _collection attribute."
            ) from e
        except RuntimeError:
            # Re-raise RuntimeErrors as-is (they already have proper context)
            raise
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error during ChromaDB query: {str(e)}. "
                "Check that the collection is accessible and properly initialized."
            ) from e
