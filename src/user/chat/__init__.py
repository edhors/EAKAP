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
from .chat import Chat
from .chat_provider import ChatProvider
from .config import settings  # type: ignore[reportMissingImports]

embeddings_provider = EmbeddingsProvider.create_provider(settings.embeddings_provider)

embeddings = Embeddings(embeddings_provider)

vector_store = Chroma(
    collection_name=settings.chroma_collection_name,
    embedding_function=embeddings,
    persist_directory=settings.chroma_persist_directory,
)
full_retrieval = FullRetrieval(embeddings, vector_store=vector_store)

spice_client = InsecureClient(settings.spicedb_address, settings.spicedb_prefix)
relationship_reader = RelationshipReader()

policy_filter = PolicyFilter()

final_retriever = FinalRetriever(vector_store=vector_store)

__all__ = [
    "Chat",
    "ChatProvider",
    "summarize_exchange",
    "settings",
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