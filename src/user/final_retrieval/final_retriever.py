from langchain_chroma import Chroma
import logging

logger = logging.getLogger(__name__)

class FinalRetriever:
    """
    A class to handle fetching chunk texts from a Chroma vector store 
    and building formatted context strings for LLM prompts.
    """

    def __init__(self, vector_store: Chroma):
        """
        Initialize the retriever with a Chroma vector store.
        
        Args:
            vector_store: Vector store object with a _collection attribute.
                Must have _collection.get(where={...}) method available.
        """
        self.vector_store = vector_store

    def retrieve_chunks(self, chunks: list[str]) -> str:
        """
        Fetch chunk texts from Chroma vector store and build a formatted context string.
        
        This method queries the Chroma collection for each chunk ID and constructs
        a string containing the source metadata and content for each retrieved chunk.
        
        Args:
            chunks: List of chunk IDs to retrieve from the vector store.
                Example: ['doc_1_chunk_1', 'doc_1_chunk_2']
        
        Returns:
            str: Formatted context string with source and content for each chunk.
                Returns empty string if chunks list is empty, vector_store is None,
                or no chunks are found.
        """
        # Edge case: empty chunks list
        if not chunks:
            logger.info("retrieve_chunks: no chunk IDs provided, returning empty string")
            return ""
        
        # Edge case: vector_store is None
        if self.vector_store is None:
            logger.error("retrieve_chunks: vector_store is None")
            return ""
        
        # Edge case: vector_store doesn't have _collection
        if not hasattr(self.vector_store, '_collection'):
            logger.error("retrieve_chunks: vector_store has no _collection attribute")
            return ""
        
        fin_string = ""
        successful_fetches = 0
        failed_fetches = 0
        
        for chunk_id in chunks:
            try:
                # Query Chroma for this chunk
                results = self.vector_store._collection.get(where={"chunk_id": chunk_id})
                
                # Edge case: empty results
                if not results:
                    logger.warning(f"retrieve_chunks: chunk_id={chunk_id} returned None")
                    failed_fetches += 1
                    continue
                
                # Edge case: no documents found
                if not results.get('documents') or len(results['documents']) == 0:
                    logger.warning(f"retrieve_chunks: chunk_id={chunk_id} not found in collection")
                    failed_fetches += 1
                    continue
                
                # Edge case: no metadata found
                if not results.get('metadatas') or len(results['metadatas']) == 0:
                    logger.warning(f"retrieve_chunks: chunk_id={chunk_id} has no metadata")
                    # Still include the document content even without metadata
                    fin_string += "Source: {}\n"
                    fin_string += "Content: " + str(results['documents'][0]) + "\n\n"
                    successful_fetches += 1
                    continue
                
                # Success: append source and content
                fin_string += "Source: " + str(results['metadatas'][0]) + "\n"
                fin_string += "Content: " + str(results['documents'][0]) + "\n\n"
                successful_fetches += 1
                
            except KeyError as e:
                logger.error(f"retrieve_chunks: KeyError for chunk_id={chunk_id}: {e}")
                failed_fetches += 1
                continue
                
            except IndexError as e:
                logger.error(f"retrieve_chunks: IndexError for chunk_id={chunk_id}: {e}")
                failed_fetches += 1
                continue
                
            except Exception as e:
                logger.error(f"retrieve_chunks: unexpected error for chunk_id={chunk_id}: {e}")
                failed_fetches += 1
                continue
        
        # Log summary
        logger.debug(
            f"retrieve_chunks: completed - {successful_fetches} successful, "
            f"{failed_fetches} failed, {len(chunks)} total"
        )
        
        # Edge case: all fetches failed
        if successful_fetches == 0 and failed_fetches > 0:
            logger.warning("retrieve_chunks: all chunk fetches failed, returning empty string")
            return ""
        
        return fin_string.strip()