"""
Policy Filter Module

A class-based policy filter for RAG pipelines.
Filters document chunks based on user permissions (ACL) from SpiceDB.

Usage:
    from policy_filter import PolicyFilter
    
    pf = PolicyFilter(top_k=2)
    chunk_ids = pf.filter(candidates, allowed_doc_ids)
"""

import logging

logger = logging.getLogger(__name__)


class PolicyFilter:
    """
    Policy-aware filter for RAG retrieval pipeline.
    
    Filters candidates by allowed document IDs, sorts by relevance score,
    and selects top-K chunks for retrieval.
    
    Attributes:
        top_k (int): Number of top chunks to select (default=2)
    
    Example:
        >>> pf = PolicyFilter(top_k=2)
        >>> candidates = [
        ...     {'doc_id': 'doc_1', 'chunk_id': 'chunk_1', 'score': '0.9'},
        ...     {'doc_id': 'doc_2', 'chunk_id': 'chunk_2', 'score': '0.8'},
        ... ]
        >>> allowed = ['doc_1']
        >>> chunk_ids = pf.filter(candidates, allowed)
        >>> print(chunk_ids)
        ['chunk_1']
    """
    
    def __init__(self, top_k: int = 2):
        """
        Initialize PolicyFilter.
        
        Args:
            top_k: Number of top chunks to select after filtering (default=2)
        """
        self.top_k = top_k
        logger.debug(f"PolicyFilter initialized with top_k={top_k}")
    
    def filter(
        self,
        candidates: list[dict],
        allowed_doc_ids: list[str],
    ) -> list[str]:
        """
        Run the full filtering pipeline and return chunk IDs.
        
        This is the main method that combines all steps:
        1. Filter by policy (ACL check)
        2. Sort by score (descending)
        3. Select top-K
        4. Extract chunk IDs
        
        Args:
            candidates: List from Full Retrieval.
                Each dict must have: doc_id, chunk_id, score
                Example: [{'doc_id': 'doc_1', 'chunk_id': 'chunk_1', 'score': '0.88'}, ...]
            allowed_doc_ids: List of doc_ids from SpiceDB that user can access.
                Example: ['doc_1', 'doc_2', 'doc_3']
        
        Returns:
            List of chunk_ids ready for Chroma retrieval.
            Returns empty list if no candidates pass the filter.
        
        Example:
            >>> pf = PolicyFilter(top_k=2)
            >>> chunk_ids = pf.filter(candidates, allowed_doc_ids)
            >>> print(chunk_ids)
            ['doc_3_chunk_1', 'doc_1_chunk_3']
        """
        # Step 1: Policy filter
        filtered = self.policy_filter(candidates, allowed_doc_ids)
        
        # Step 2: Sort and select top-k
        selected = self.sort_and_select_top_k(filtered)
        
        # Step 3: Extract chunk IDs
        chunk_ids = self.extract_chunk_ids(selected)
        
        return chunk_ids
    
    def policy_filter(
        self,
        candidates: list[dict],
        allowed_doc_ids: list[str],
    ) -> list[dict]:
        """
        Filter candidates by allowed document IDs (ACL check).
        
        Keeps only candidates whose doc_id is in the allowed list.
        
        Args:
            candidates: List of candidate dicts with doc_id, chunk_id, score
            allowed_doc_ids: List of allowed doc_ids from SpiceDB
        
        Returns:
            Filtered list of candidates (only allowed docs)
        """
        # Edge case: empty allowed list
        if not allowed_doc_ids:
            logger.info("policy_filter: allowed_doc_ids is empty, returning empty list")
            return []
        
        # Edge case: empty candidates
        if not candidates:
            logger.info("policy_filter: candidates is empty, returning empty list")
            return []
        
        allowed_set = set(allowed_doc_ids)  # O(1) lookup
        
        filtered = [
            candidate
            for candidate in candidates
            if candidate.get('doc_id') in allowed_set
        ]
        
        dropped = len(candidates) - len(filtered)
        logger.debug(f"policy_filter: kept {len(filtered)}, dropped {dropped}")
        
        return filtered
    
    def sort_and_select_top_k(
        self,
        candidates: list[dict],
    ) -> list[dict]:
        """
        Sort candidates by score (descending) and select top K.
        
        Args:
            candidates: Filtered list from policy_filter()
        
        Returns:
            Top K candidates sorted by score (highest first)
        """
        # Edge case: empty candidates
        if not candidates:
            logger.info("sort_and_select_top_k: no candidates to sort")
            return []
        
        # Sort by score descending (score is string, convert to float)
        try:
            sorted_candidates = sorted(
                candidates,
                key=lambda x: float(x.get('score', 0)),
                reverse=True
            )
        except (ValueError, TypeError) as e:
            logger.error(f"sort_and_select_top_k: error converting score to float: {e}")
            return []
        
        # Select top K
        selected = sorted_candidates[:self.top_k]
        
        if len(selected) < self.top_k:
            logger.info(
                f"sort_and_select_top_k: only {len(selected)} available "
                f"(requested {self.top_k})"
            )
        
        logger.debug(f"sort_and_select_top_k: selected {len(selected)} from {len(candidates)}")
        
        return selected
    
    def extract_chunk_ids(
        self,
        candidates: list[dict],
    ) -> list[str]:
        """
        Extract chunk_ids from candidates list.
        
        Args:
            candidates: List from sort_and_select_top_k()
        
        Returns:
            List of chunk_ids (preserves order)
        """
        # Edge case: empty candidates
        if not candidates:
            logger.debug("extract_chunk_ids: no candidates, returning empty list")
            return []
        
        chunk_ids = [c.get('chunk_id', '') for c in candidates if c.get('chunk_id')]
        logger.debug(f"extract_chunk_ids: extracted {len(chunk_ids)} chunk_ids")
        
        return chunk_ids
    
    def get_filtered_candidates(
        self,
        candidates: list[dict],
        allowed_doc_ids: list[str],
    ) -> str:
        """
        Get filtered chunk IDs as a comma-separated string.
        
        Args:
            candidates: List from Full Retrieval
            allowed_doc_ids: List from SpiceDB
        
        Returns:
            Comma-separated string of chunk IDs.
            Example: "doc_3_chunk_1, doc_1_chunk_3"
            Returns empty string if no candidates pass filter.
        """
        chunk_ids = self.filter(candidates, allowed_doc_ids)
        
        if not chunk_ids:
            return ""
        
        return ", ".join(chunk_ids)