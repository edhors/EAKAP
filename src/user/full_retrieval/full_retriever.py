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
            # Validate that the vectorstore has a collection
            try:
                if not hasattr(vector_store, '_collection') or vector_store._collection is None:
                    raise RuntimeError(
                        "Provided vector_store does not have a valid ChromaDB collection. "
                        "Ensure the vectorstore is properly initialized."
                    )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to validate vector_store: {str(e)}"
                ) from e
            self._vector_store = vector_store
        else:
            # Path-based initialization
            if not persist_directory:
                raise ValueError("persist_directory is required when vector_store is not provided")
            if not isinstance(persist_directory, str) or not persist_directory.strip():
                raise ValueError("persist_directory must be a non-empty string")
            
            if not collection_name:
                raise ValueError("collection_name is required when vector_store is not provided")
            if not isinstance(collection_name, str) or not collection_name.strip():
                raise ValueError("collection_name must be a non-empty string")
            
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
                # Validate that collection was created/loaded successfully
                if not hasattr(self._vector_store, '_collection') or self._vector_store._collection is None:
                    raise RuntimeError(
                        f"Failed to initialize ChromaDB collection '{collection_name}' "
                        f"at '{persist_directory}'. The collection may not exist or the path may be invalid."
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
        
        # Check for NaN or Infinity values
        for i, val in enumerate(query_embeddings):
            if math.isnan(val):
                raise ValueError(
                    f"query_embeddings contains NaN (Not a Number) at index {i}. "
                    "All values must be finite numbers."
                )
            if math.isinf(val):
                raise ValueError(
                    f"query_embeddings contains Infinity at index {i}. "
                    "All values must be finite numbers."
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
            if not hasattr(self._vector_store, '_collection'):
                raise RuntimeError(
                    "Vector store does not have a _collection attribute. "
                    "Ensure the vector_store is properly initialized."
                )
            
            collection = self._vector_store._collection
            if collection is None:
                raise RuntimeError(
                    "ChromaDB collection is None. "
                    "The collection may not have been initialized properly."
                )
            
            # Get collection count with error handling
            try:
                collection_count = collection.count()
                if collection_count == 0:
                    return []  # Empty collection, return empty results
            except Exception as e:
                raise RuntimeError(
                    f"Failed to access ChromaDB collection count: {str(e)}. "
                    "The collection may be corrupted or inaccessible."
                ) from e
            
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
            
            # Validate query results structure
            if not isinstance(results, dict):
                raise RuntimeError(
                    f"ChromaDB query returned unexpected result type: {type(results).__name__}. "
                    "Expected a dictionary with 'ids', 'distances', and 'metadatas' keys."
                )
            
            if 'ids' not in results:
                raise RuntimeError(
                    "ChromaDB query result missing 'ids' key. "
                    "The query result structure is invalid."
                )
            
            if 'distances' not in results:
                raise RuntimeError(
                    "ChromaDB query result missing 'distances' key. "
                    "The query result structure is invalid."
                )
            
            # Process results
            # ChromaDB returns: {'ids', 'distances', 'metadatas', 'documents'}
            # distances is a list of lists (one list per query embedding)
            # For a single query, we get distances[0]
            if not results['ids'] or not results['ids'][0]:
                return []
            
            ids = results['ids'][0]
            distances = results['distances'][0]
            
            # Validate that ids and distances have the same length
            if len(ids) != len(distances):
                raise RuntimeError(
                    f"Mismatch between ids ({len(ids)}) and distances ({len(distances)}) lengths. "
                    "ChromaDB query result is corrupted."
                )
            
            # Safely extract metadatas
            metadatas = []
            if 'metadatas' in results and results['metadatas']:
                if isinstance(results['metadatas'], list) and len(results['metadatas']) > 0:
                    metadatas = results['metadatas'][0]
                    if not isinstance(metadatas, list):
                        metadatas = []
                else:
                    metadatas = []
            
            # Convert distances to similarity scores
            # For cosine similarity: similarity = 1 - distance
            # (ChromaDB uses cosine distance where 0 = identical, 2 = opposite)
            processed_results = []
            
            for i, (doc_id, distance) in enumerate(zip(ids, distances)):
                try:
                    # Validate distance is numeric
                    if not isinstance(distance, (int, float)):
                        raise ValueError(f"Distance at index {i} is not numeric: {type(distance).__name__}")
                    
                    distance = float(distance)
                    
                    # Check for invalid distance values
                    if math.isnan(distance):
                        # Skip results with NaN distances
                        continue
                    if math.isinf(distance):
                        # Skip results with infinite distances
                        continue
                    
                    # Convert distance to similarity score (1 - distance for cosine)
                    # Clamp to [0, 1] range in case distance > 1
                    similarity_score = max(0.0, min(1.0, 1.0 - distance))
                    
                    # Filter by threshold
                    if similarity_score < threshold:
                        continue
                    
                    # Extract metadata with error handling
                    metadata = {}
                    try:
                        if i < len(metadatas) and metadatas[i] is not None:
                            if isinstance(metadatas[i], dict):
                                metadata = metadatas[i]
                    except (IndexError, TypeError) as e:
                        # Metadata extraction failed, use empty dict
                        metadata = {}
                    
                    # Extract doc_id and chunk_id from metadata, with fallback to id
                    # Metadata should contain both doc_id and chunk_id
                    try:
                        doc_id_meta = metadata.get('doc_id') if isinstance(metadata, dict) else None
                        chunk_id = metadata.get('chunk_id') if isinstance(metadata, dict) else None
                    except Exception as e:
                        # Metadata access failed, use fallbacks
                        doc_id_meta = None
                        chunk_id = None
                    
                    # Fallback: if metadata is missing, use the id itself
                    # This handles cases where metadata might not be properly set
                    if doc_id_meta is None:
                        doc_id_meta = str(doc_id) if doc_id is not None else f"unknown_{i}"
                    if chunk_id is None:
                        chunk_id = str(doc_id) if doc_id is not None else f"unknown_{i}"
                    
                    # Ensure doc_id and chunk_id are strings
                    try:
                        doc_id_meta = str(doc_id_meta)
                        chunk_id = str(chunk_id)
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to convert doc_id or chunk_id to string at index {i}: {str(e)}"
                        ) from e
                    
                    processed_results.append({
                        "doc_id": doc_id_meta,
                        "chunk_id": chunk_id,
                        "score": float(similarity_score)
                    })
                    
                except Exception as e:
                    # Log error but continue processing other results
                    # This prevents one bad result from breaking the entire query
                    raise RuntimeError(
                        f"Error processing result at index {i}: {str(e)}. "
                        f"doc_id={doc_id}, distance={distance}"
                    ) from e
            
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
