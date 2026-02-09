import sys
import os

# 1. Fix the Python Path so it recognizes 'src'
# This finds the 'EAKAP' directory (3 levels up from this __init__.py)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)


from src.shared.indexing.embeddings import embeddings
from src.user.final_retrieval import final_retriever
from src.user.full_retrieval.full_retriever import full_retriever
from src.shared.spicedb_handler.read_relationships import read_relationships
from src.user.final_retrieval.policy_filter import policy_filter
from src.user.final_retrieval.final_retriever import final_retriever
from authzed.api.v1 import InsecureClient

Embeddings = embeddings.Embeddings
FullRetrieval = full_retriever.FullRetrieval
RelationshipReader = read_relationships.RelationshipReader
PolicyFilter = policy_filter.PolicyFilter
FinalRetriever = final_retriever.FinalRetriever

# Specific Methods
# 1- embed_query(self, text:str)
embed_query = Embeddings.embed_query

# 2- search(self, query_embeddings, threshold, k)
search = FullRetrieval.search

# 3- get_allowed_doc_ids(self, user_id, candidates, client)
get_allowed_doc_ids = RelationshipReader.get_allowed_doc_ids

# 4- filter(self, candidates, allowed_doc_ids)
filter_candidates = PolicyFilter.filter

# 5- retrieve_chunks(self, chunks)
retrieve_chunks = FinalRetriever.retrieve_chunks

__all__ = [
    "InsecureClient",
    "Embeddings",
    "FullRetrieval",
    "RelationshipReader",
    "PolicyFilter",
    "FinalRetriever",
    "embed_query",
    "search",
    "get_allowed_doc_ids",
    "filter_candidates",
    "retrieve_chunks",
]