import sys
import os

# 1. Fix the Python Path so it recognizes 'src'
# This finds the 'EAKAP' directory (3 levels up from this __init__.py)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.shared.indexing.embeddings_provider import EmbeddingsProvider
from src.shared.indexing.embeddings import Embeddings
from src.user.full_retrieval.full_retriever import FullRetrieval
from src.shared.spicedb_handler.read_relationships import RelationshipReader
from src.user.final_retrieval.policy_filter import PolicyFilter
from src.user.final_retrieval.final_retriever import FinalRetriever
from authzed.api.v1 import InsecureClient
from langchain_chroma import Chroma
from src.user.chat.short_memory import summarize_exchange 


embeddings_provider = EmbeddingsProvider.create_provider("huggingface")

embeddings = Embeddings(embeddings_provider)

vector_store = Chroma(
    collection_name="documents_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)
full_retrieval = FullRetrieval(embeddings, vector_store=vector_store)

spice_client = InsecureClient("spicedb:50051", "test")
relationship_reader = RelationshipReader()

policy_filter = PolicyFilter()

final_retriever = FinalRetriever(vector_store=vector_store)


__all__ = [
    "summarize_exchange",
    "InsecureClient",
    "Embeddings",
    "embeddings_provider",
    "embeddings",
    "full_retrieval",
    "spice_client",
    "relationship_reader",
    "policy_filter",
    "final_retriever",
    "FullRetrieval",
    "RelationshipReader",
    "PolicyFilter",
    "FinalRetriever",
]