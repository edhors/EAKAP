"""
LangChain tools for the chat agent: RAG + SpiceDB-backed retrieve_context.
"""

import contextvars

from langchain.tools import tool

# Import RAG/SpiceDB dependencies from parent package (after __init__.py loads them)
from src.user.chat import (
    embeddings,
    full_retrieval,
    relationship_reader,
    policy_filter,
    final_retriever,
    InsecureClient,
    settings,
)

current_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "chat_current_user_id", default=None
)


@tool
def retrieve_context(
    query: str,
    threshold: float | None = None,
    top_k: int | None = None,
) -> str:
    """
    Retrieve permission-filtered context from the RAG index for a user query.

    Use this tool when the agent needs to look up information to answer the user.
    It embeds the query, runs vector search, applies SpiceDB-based access control,
    then returns formatted text of the allowed, top-k chunks.

    Args:
        query: The user's question or search text.
        threshold: Similarity threshold for vector search (default from config).
        top_k: Maximum number of chunks to return (default from config).

    Returns:
        Concatenated text of the allowed, top-k chunks.
    """
    user_id = current_user_id.get()
    if user_id is None:
        raise ValueError("user_id not set for this request")
    if threshold is None:
        threshold = settings.default_threshold
    if top_k is None:
        top_k = settings.default_top_k
    vector = embeddings.embed_query(text=query)
    candidates = full_retrieval.search(vector, threshold=threshold)
    spice_client = InsecureClient(settings.spicedb_address, settings.spicedb_prefix)
    allowed_docs = relationship_reader.get_allowed_doc_ids(user_id, candidates, spice_client)
    chunk_ids = policy_filter.filter(candidates, allowed_docs)
    context_string = final_retriever.retrieve_chunks(chunk_ids)
    return context_string


tools = [retrieve_context]
