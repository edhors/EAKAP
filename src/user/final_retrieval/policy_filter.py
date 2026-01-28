"""
Policy Filter Module

Receives:
    1. candidates: List of dicts from Full Retrieval
    2. allowed_doc_ids: List of doc_ids from SpiceDB

Pipeline:
    1. policy_filter() - Filter by allowed docs
    2. sort_and_select_top_k() - Sort desc, pick top K
    3. extract_chunk_ids() - Get chunk_id list

Output:
    List of chunk_ids → Goes to next module for Chroma retrieval
"""

import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Step 1: Policy Filter
# =============================================================================

def policy_filter(
    candidates: list[dict],
    allowed_doc_ids: list[str],
) -> list[dict]:
    """
    Filter candidates by allowed document IDs (ACL check).
    
    Args:
        candidates: List from Full Retrieval
            [{'doc_id': 'doc_1', 'chunk_id': 'doc_1_chunk_1', 'score': '0.88'}, ...]
        allowed_doc_ids: List from SpiceDB
            ['doc_1', 'doc_2', 'doc_3']
    
    Returns:
        Filtered list of candidates (only allowed docs)
    """
    if not allowed_doc_ids:
        logger.info("policy_filter: allowed_doc_ids is empty, returning empty list")
        return []
    
    allowed_set = set(allowed_doc_ids)  # O(1) lookup
    
    filtered = [
        candidate 
        for candidate in candidates 
        if candidate['doc_id'] in allowed_set
    ]
    
    dropped = len(candidates) - len(filtered)
    logger.debug(f"policy_filter: kept {len(filtered)}, dropped {dropped}")
    
    return filtered


# =============================================================================
# Step 2: Sort and Select Top-K
# =============================================================================

def sort_and_select_top_k(
    candidates: list[dict],
    top_k: int = 2,
) -> list[dict]:
    """
    Sort candidates by score (descending) and select top K.
    
    Args:
        candidates: Filtered list from policy_filter()
        top_k: Number of top candidates to select (default=2)
    
    Returns:
        Top K candidates sorted by score (highest first)
    """
    if not candidates:
        logger.info("sort_and_select_top_k: no candidates to sort")
        return []
    
    # Sort by score descending (score is string, convert to float)
    sorted_candidates = sorted(
        candidates,
        key=lambda x: float(x['score']),
        reverse=True
    )
    
    # Select top K
    selected = sorted_candidates[:top_k]
    
    if len(selected) < top_k:
        logger.info(
            f"sort_and_select_top_k: only {len(selected)} available "
            f"(requested {top_k})"
        )
    
    logger.debug(f"sort_and_select_top_k: selected {len(selected)} from {len(candidates)}")
    
    return selected


# =============================================================================
# Step 3: Extract Chunk IDs
# =============================================================================

def extract_chunk_ids(candidates: list[dict]) -> list[str]:
    """
    Extract chunk_ids from candidates list.
    
    Args:
        candidates: List from sort_and_select_top_k()
    
    Returns:
        List of chunk_ids (preserves order)
    """
    chunk_ids = [c['chunk_id'] for c in candidates]
    logger.debug(f"extract_chunk_ids: extracted {len(chunk_ids)} chunk_ids")
    return chunk_ids


# =============================================================================
# Combined Pipeline (convenience function)
# =============================================================================

def get_filtered_chunk_ids(
    candidates: list[dict],
    allowed_doc_ids: list[str],
    top_k: int = 2,
) -> list[str]:
    """
    Run the full pipeline: filter → sort → top-k → extract chunk_ids.
    
    Args:
        candidates: List from Full Retrieval
        allowed_doc_ids: List from SpiceDB
        top_k: Number of top chunks to select
    
    Returns:
        List of chunk_ids
    """
    # Step 1: Policy filter
    filtered = policy_filter(candidates, allowed_doc_ids)
    
    # Step 2: Sort and select top-k
    selected = sort_and_select_top_k(filtered, top_k)
    
    # Step 3: Extract chunk IDs
    chunk_ids = extract_chunk_ids(selected)
    
    return chunk_ids


# =============================================================================
# Main - For testing
# =============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # -----------------------------------------
    # INPUT 1: From Full Retrieval
    # -----------------------------------------
    candidates = [
        {'doc_id': 'doc_1', 'chunk_id': 'doc_1_chunk_1', 'score': '0.88'},
        {'doc_id': 'doc_1', 'chunk_id': 'doc_1_chunk_2', 'score': '0.80'},
        {'doc_id': 'doc_1', 'chunk_id': 'doc_1_chunk_3', 'score': '0.90'},
        {'doc_id': 'doc_2', 'chunk_id': 'doc_2_chunk_1', 'score': '0.85'},
        {'doc_id': 'doc_3', 'chunk_id': 'doc_3_chunk_1', 'score': '0.92'},
        {'doc_id': 'doc_4', 'chunk_id': 'doc_4_chunk_1', 'score': '0.78'},  # Not allowed
    ]
    
    # -----------------------------------------
    # INPUT 2: From SpiceDB
    # -----------------------------------------
    allowed_doc_ids = ['doc_1', 'doc_2', 'doc_3']
    
    # -----------------------------------------
    # Step-by-step execution
    # -----------------------------------------
    print("=" * 50)
    print("STEP-BY-STEP EXECUTION")
    print("=" * 50)
    
    # Step 1
    print("\n[Step 1] Policy Filter")
    print(f"Input: {len(candidates)} candidates")
    filtered = policy_filter(candidates, allowed_doc_ids)
    print(f"Output: {len(filtered)} candidates")
    for c in filtered:
        print(f"  {c}")
    
    # Step 2
    print("\n[Step 2] Sort and Select Top-K (K=2)")
    print(f"Input: {len(filtered)} candidates")
    selected = sort_and_select_top_k(filtered, top_k=2)
    print(f"Output: {len(selected)} candidates")
    for c in selected:
        print(f"  {c}")
    
    # Step 3
    print("\n[Step 3] Extract Chunk IDs")
    print(f"Input: {len(selected)} candidates")
    chunk_ids = extract_chunk_ids(selected)
    print(f"Output: {chunk_ids}")
    
    # -----------------------------------------
    # Or use the combined function
    # -----------------------------------------
    print("\n" + "=" * 50)
    print("COMBINED FUNCTION")
    print("=" * 50)
    chunk_ids = get_filtered_chunk_ids(candidates, allowed_doc_ids, top_k=2)
    print(f"Final chunk_ids: {chunk_ids}")
    print("\n→ These go to the next module for Chroma retrieval")
