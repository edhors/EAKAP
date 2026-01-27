"""
Wrapper class for LangChain embeddings that provides a unified interface
for embedding queries and text chunks.
"""

from typing import List
from langchain_core.embeddings import Embeddings as LangChainEmbeddings


class Embeddings:
    """
    Wrapper class that uses a LangChain embeddings provider to create embeddings.
    
    This class delegates to the underlying LangChain embeddings instance
    to create embeddings for queries and text chunks.
    """
    
    def __init__(self, provider: LangChainEmbeddings):
        """
        Initialize with a LangChain embeddings provider instance.
        
        Args:
            provider: A LangChain Embeddings instance (created via EmbeddingsProvider.create_provider)
        
        Raises:
            TypeError: If provider is not a LangChain Embeddings instance
        """
        if not isinstance(provider, LangChainEmbeddings):
            raise TypeError(
                f"Provider must be a LangChain Embeddings instance, "
                f"got {type(provider).__name__}"
            )
        self._provider = provider
    
    def embed_query(self, text: str) -> List[float]:
        """
        Create embedding for a single text query.
        
        Args:
            text: The text string to embed
        
        Returns:
            List[float]: The embedding vector as a list of floats
        
        Raises:
            ValueError: If text is empty or None
            Exception: If embedding creation fails
        """
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")
        
        try:
            return self._provider.embed_query(text)
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {str(e)}") from e
    
    def embed_chunks(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for multiple text chunks.
        
        Args:
            texts: List of text strings (chunks) to embed
        
        Returns:
            List[List[float]]: List of embedding vectors, one per input chunk
        
        Raises:
            ValueError: If texts is empty or contains invalid entries
            RuntimeError: If embedding creation fails
        """
        if not texts:
            raise ValueError("texts must be a non-empty list")
        
        if not isinstance(texts, list):
            raise ValueError("texts must be a list of strings")
        
        if not all(isinstance(text, str) and text for text in texts):
            raise ValueError("All items in texts must be non-empty strings")
        
        try:
            return self._provider.embed_documents(texts)
        except Exception as e:
            raise RuntimeError(f"Failed to embed chunks: {str(e)}") from e

