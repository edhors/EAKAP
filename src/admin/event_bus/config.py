import os
from pydantic_settings import BaseSettings

class EventBusSettings(BaseSettings):
    # --- Redis Connection ---
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = 6379
    
    # --- Stream Names ---
    # We use prefixes like 'stream:' to keep the Redis keyspace organized
    DOC_OPS_STREAM: str = "stream:doc_ops"
    POLICY_OPS_STREAM: str = "stream:policy_ops"
    FAILED_EVENTS_STREAM: str = "stream:failed_events"
    
    # --- Consumer Group Names ---
    # These must be unique per "logical job" as we discussed
    INDEXING_GROUP: str = "group:indexing"
    RS_DOC_GROUP: str = "group:rs_docs"
    RS_POLICY_GROUP: str = "group:rs_policies"
    
    # --- Path Variables ---
    # Local directory where uploaded documents are temporarily stored
    # This is what the 'link' in your message will point to locally
    LOCAL_STORAGE_PATH: str = "./storage/raw_docs"
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

# Create a singleton instance to be used across the project
bus_settings = EventBusSettings()