"""
FastAPI app and POST /chat/ask endpoint. Uses Chat, ChatProvider, and tools from this package.
"""

import os
import sys
import asyncio

# When run as script (python routes.py), add project root so "src" can be imported
if __name__ == "__main__":
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

load_dotenv()

from src.user.chat import Chat, ChatProvider, summarize_exchange, settings
from src.user.chat.tools import tools

app = FastAPI()
app.state.short_term_memory = ""


class QueryRequest(BaseModel):
    user_id: str
    query: str
    threshold: float = settings.default_threshold
    top_k: int = settings.default_top_k


def _provider_config() -> dict:
    """Build kwargs for ChatProvider.create_provider from settings."""
    cfg = {"model": settings.model, "temperature": settings.temperature}
    key_map = {
        "google": ("google_api_key", settings.google_api_key),
        "zhipuai": ("zhipuai_api_key", settings.zhipuai_api_key),
        "openai": ("openai_api_key", settings.openai_api_key),
        "anthropic": ("anthropic_api_key", settings.anthropic_api_key),
        "mistral": ("mistral_api_key", settings.mistral_api_key),
    }
    key_name, value = key_map.get(settings.provider_type, (None, None))
    if key_name and value:
        cfg[key_name] = value
    return cfg


# Wiring at module load
_provider = ChatProvider.create_provider(settings.provider_type, **_provider_config())
_system_prompt = """
You are the EAKAP AI Assistant. Use the following context to answer the user's question.
If the context doesn't contain the answer, say you don't have the answer to that question.
You must use retrieve_context to answer the user's question.
When calling retrieve_context, use the user_id, threshold, and top_k from the user message.
When calling retrieve_context, manipulate the user query to only key points e.g. "what is the capital of France?" -> "capital France", or "Explain the concept of AI"? -> "concept AI".
"""
_chat = Chat(_provider, tools, _system_prompt)


@app.post("/chat/ask")
def chat_endpoint(request: QueryRequest):
    try:
        # Include user_id/threshold/top_k so the agent can pass them to retrieve_context
        context_string = (
            app.state.short_term_memory
            + "\n"
            + f"user_id: {request.user_id}, threshold: {request.threshold}, top_k: {request.top_k}\n\n"
            + request.query
        )
        response = _chat.ask(context_string)
        app.state.short_term_memory += summarize_exchange(request.query, response) + "\n"
        return {
            "answer": response,
            "user_id": request.user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn_config = uvicorn.Config(
        app, host=settings.server_host, port=settings.server_port
    )
    server = uvicorn.Server(uvicorn_config)
    asyncio.run(server.serve())
