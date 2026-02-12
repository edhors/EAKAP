"""
FastAPI app and POST /chat/ask endpoint. Uses Chat, ChatProvider, and tools from this package.
"""

import os
import sys
from .schemas import QueryRequest
# When run as script (python routes.py), add project root so "src" can be imported
if __name__ == "__main__":
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, APIRouter, Request, Depends

load_dotenv()

from src.user.chat import Chat, ChatProvider, summarize_exchange, settings
from src.user.chat.tools import tools
from src.shared.auth.dependencies import get_current_active_user
from src.shared.userdb_handler import User

router = APIRouter(prefix="/chat", tags=["Chat"])


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
_system_prompt = settings.system_prompt
_chat = Chat(_provider, tools, _system_prompt)


@router.post("/ask")
def chat_endpoint(
    request: Request,
    body: QueryRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        user_id = current_user.id
        # Include user_id/threshold/top_k so the agent can pass them to retrieve_context
        state_short_mem = request.app.state.short_term_memory
        context_string = (
            state_short_mem
            + "\n"
            + f"user_id: {user_id}, threshold: {body.threshold}, top_k: {body.top_k}\n\n"
            + body.query
        )
        response = _chat.ask(context_string)
        state_short_mem += summarize_exchange(body.query, response) + "\n"
        return {
            "answer": response,
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


