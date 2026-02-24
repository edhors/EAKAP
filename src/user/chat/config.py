"""
Chat module configuration. All values can be overridden via environment variables
with prefix CHAT_ (e.g. CHAT_PROVIDER_TYPE, CHAT_MODEL), except API keys which
use standard names (GOOGLE_API_KEY, ZHIPUAI_API_KEY) via validation_alias.
"""

from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = find_dotenv()


class ChatSettings(BaseSettings):
    # LLM / provider
    provider_type: str = Field(default="zhipuai", description="One of: google, openai, anthropic, mistral, huggingface, zhipuai")
    model: str = Field(default="glm-4.5-flash", description="Model name for the chosen provider")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    # System prompt
    system_prompt: str = Field(default="You are the EAKAP AI Assistant. Use the following context to answer the user's question. If the context doesn't contain the answer, say you don't have the answer to that question.", description="System prompt for the EAKAP AI Assistant")
    # API keys (read from standard env names; optional so only the active provider needs to be set)
    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    zhipuai_api_key: str | None = Field(default=None, validation_alias="ZHIPUAI_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    mistral_api_key: str | None = Field(default=None, validation_alias="MISTRAL_API_KEY")

    # SpiceDB
    spicedb_address: str = Field(default="spicedb:50051")
    spicedb_prefix: str = Field(default="test")

    # Chroma
    chroma_collection_name: str = Field(default="documents_collection")
    chroma_persist_directory: str = Field(default="./chroma_db")
    chroma_ip: str = Field(default="chromadb")
    chroma_port: int = Field(default=8123)

    # Embeddings
    embeddings_provider: str = Field(default="huggingface")

    # Retrieval defaults (used by API and tool)
    default_threshold: float = Field(default=1.5)
    default_top_k: int = Field(default=2, ge=1)

    # Server (when running uvicorn from this module)
    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8000, ge=1, le=65535)

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        env_prefix="chat_",
        extra="ignore",
    )


settings = ChatSettings()
