from pydantic import BaseModel
from src.user.chat import Chat, ChatProvider, summarize_exchange, settings
from fastapi import Request



class QueryRequest(BaseModel):
    query: str
    threshold: float = settings.default_threshold
    top_k: int = settings.default_top_k
    


