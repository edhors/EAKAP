# Chat Module Documentation

A module for an agentic chat assistant backed by a configurable LLM provider, RAG retrieval, and SpiceDB-based access control.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [Chat](#chat)
  - [ChatProvider](#chatprovider)
  - [Config (ChatSettings)](#config-chatsettings)
  - [Tools](#tools)
  - [short_memory](#short_memory)
  - [HTTP API](#http-api)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The chat module provides:

- **Agentic chat**: A LangChain/LangGraph agent that uses tools to answer questions.
- **RAG retrieval**: Permission-filtered context from a vector store (Chroma) and SpiceDB.
- **Configurable LLM**: Multiple providers (Google, OpenAI, Anthropic, Mistral, HuggingFace, Zhipu AI) via `ChatProvider`.
- **Short-term memory**: Summarized conversation history for multi-turn context.
- **HTTP API**: FastAPI `POST /chat/ask` with `user_id`, `query`, and optional `threshold`/`top_k`.

## Installation

### Required Dependencies

```bash
# Core
pip install langchain langchain-community
pip install langchain-chroma
pip install pydantic-settings python-dotenv

# LLM provider (install at least one)
pip install langchain-google-genai    # Google (Gemini)
pip install langchain-openai         # OpenAI
pip install langchain-anthropic       # Anthropic
pip install langchain-mistralai       # Mistral
pip install langchain-huggingface    # HuggingFace
pip install langchain-community       # Zhipu AI (ChatZhipuAI)

# RAG / embeddings (must match indexing)
pip install langchain-huggingface sentence-transformers  # or your embeddings stack
pip install authzed                    # SpiceDB client
```

### Module Dependencies

This module relies on:

- `src.shared.indexing` (embeddings, Chroma)
- `src.user.full_retrieval`, `src.user.final_retrieval` (RAG pipeline)
- `src.shared.spicedb_handler` (relationship reader)

Ensure the project root is on `PYTHONPATH` when running or importing (e.g. run as `python -m src.user.chat.chat_routes` from the repo root).

## Architecture

```
┌─────────────────────┐
│   ChatProvider      │  Factory for LLM instances (Google, Zhipu, etc.)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│       Chat          │     │   config (settings) │
│  - ReAct agent      │◄────│   SpiceDB, Chroma,  │
│  - ask(message)     │     │   provider, model   │
└──────────┬──────────┘     └─────────────────────┘
           │
           ├──────────────────┐
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│     tools        │  │  short_memory    │
│ retrieve_context │  │ summarize_exchange│
│ (RAG + SpiceDB)  │  │ (for context)    │
└──────────────────┘  └──────────────────┘
           │
           ▼
┌─────────────────────┐
│   chat_routes       │  FastAPI app, POST /chat/ask
└─────────────────────┘
```

## Configuration

All settings are driven by [config.py](config.py) (pydantic-settings). Use a `.env` file (see [.env.example](.env.example)) or environment variables with prefix `CHAT_`. API keys use standard names (e.g. `GOOGLE_API_KEY`, `ZHIPUAI_API_KEY`).

| Variable | Description | Default |
|----------|-------------|---------|
| `CHAT_PROVIDER_TYPE` | LLM provider: `google`, `openai`, `anthropic`, `mistral`, `huggingface`, `zhipuai` | `zhipuai` |
| `CHAT_MODEL` | Model name for the provider | `glm-4-flash` |
| `CHAT_TEMPERATURE` | Sampling temperature (0–2) | `0.7` |
| `CHAT_SPICEDB_ADDRESS` | SpiceDB gRPC address | `spicedb:50051` |
| `CHAT_SPICEDB_PREFIX` | SpiceDB prefix | `test` |
| `CHAT_CHROMA_COLLECTION_NAME` | Chroma collection | `documents_collection` |
| `CHAT_CHROMA_PERSIST_DIRECTORY` | Chroma persistence path | `./chroma_db` |
| `CHAT_EMBEDDINGS_PROVIDER` | Embeddings provider (e.g. for RAG) | `huggingface` |
| `CHAT_DEFAULT_THRESHOLD` | Default similarity threshold for retrieval | `1.5` |
| `CHAT_DEFAULT_TOP_K` | Default number of chunks to retrieve | `2` |
| `CHAT_SERVER_HOST` / `CHAT_SERVER_PORT` | Uvicorn host/port when running this module | `0.0.0.0` / `8000` |

Set the API key for your chosen provider (no `CHAT_` prefix): `GOOGLE_API_KEY`, `ZHIPUAI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`.

## Quick Start

```python
from src.user.chat import Chat, ChatProvider, summarize_exchange, settings
from src.user.chat.tools import tools

# 1. Create LLM provider (uses config if settings are loaded)
provider = ChatProvider.create_provider(
    settings.provider_type,
    model=settings.model,
    temperature=settings.temperature,
    zhipuai_api_key=settings.zhipuai_api_key,
)

# 2. Build agent and ask
system_prompt = "You are a helpful assistant. Use retrieve_context to look up information."
chat = Chat(provider, tools, system_prompt)
response = chat.ask("user_id: user-1, threshold: 1.5, top_k: 2\n\nWhat is the capital of France?")
print(response)
```

**Run the HTTP server:**

```bash
# From project root
python -m src.user.chat.chat_routes
# Or from src/user/chat (path is fixed in script)
python chat_routes.py
```

Then `POST /chat/ask` with JSON: `{"user_id": "user-1", "query": "Your question", "threshold": 1.5, "top_k": 2}`.

## API Reference

### Chat

Wraps an LLM and tools in a ReAct agent and exposes a single `ask` method.

#### `__init__(provider, tools, system_prompt: str)`

**Parameters:**
- `provider`: A LangChain chat model (`BaseChatModel`), e.g. from `ChatProvider.create_provider(...)`.
- `tools`: List of LangChain tools (e.g. `tools` from [tools.py](tools.py)).
- `system_prompt`: System prompt string for the agent.

#### `ask(message: str) -> str`

Invokes the agent with the given message and returns the final assistant reply as a string.

**Parameters:**
- `message`: User message; may include short-term memory and structured lines (e.g. `user_id`, `threshold`, `top_k` for the tool).

**Returns:**
- `str`: The assistant’s reply (plain text).

**Example:**
```python
chat = Chat(provider, tools, "You are the EAKAP AI Assistant. Use retrieve_context to answer.")
answer = chat.ask("user_id: user-1, threshold: 1.5, top_k: 2\n\nWhat is X?")
```

---

### ChatProvider

Factory for creating LangChain chat model instances.

#### `create_provider(provider_type: str, **config) -> BaseChatModel`

**Parameters:**
- `provider_type`: One of `"google"`, `"openai"`, `"anthropic"`, `"mistral"`, `"huggingface"`, `"zhipuai"`.
- `**config`: Provider-specific options, e.g.:
  - **Google**: `model`, `temperature`, `google_api_key` (required).
  - **Zhipu AI**: `model`, `temperature`, `zhipuai_api_key` (required).
  - **OpenAI**: `model`, `temperature`, `openai_api_key` (required).
  - (Similarly for Anthropic, Mistral, HuggingFace.)

**Returns:**
- `BaseChatModel`: A LangChain chat model instance.

**Raises:**
- `ValueError`: Unsupported provider or missing required config (e.g. API key).
- `ImportError`: Required provider package not installed.

**Example:**
```python
# Zhipu AI
model = ChatProvider.create_provider(
    "zhipuai",
    model="glm-4-flash",
    temperature=0.7,
    zhipuai_api_key=os.environ.get("ZHIPUAI_API_KEY"),
)

# Google
model = ChatProvider.create_provider(
    "google",
    model="gemini-2.5-flash-lite",
    temperature=0.7,
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
)
```

---

### Config (ChatSettings)

Defined in [config.py](config.py). A single `settings` instance is exported from the package.

**Attributes (all overridable via env with `CHAT_` prefix, except API keys):**
- `provider_type`, `model`, `temperature`
- `google_api_key`, `zhipuai_api_key`, `openai_api_key`, `anthropic_api_key`, `mistral_api_key` (from env, optional)
- `spicedb_address`, `spicedb_prefix`
- `chroma_collection_name`, `chroma_persist_directory`
- `embeddings_provider`
- `default_threshold`, `default_top_k`
- `server_host`, `server_port`

**Example:**
```python
from src.user.chat import settings
print(settings.provider_type, settings.model)
```

---

### Tools

Defined in [tools.py](tools.py). Used by the Chat agent.

#### `retrieve_context(query: str, user_id: str, threshold: float | None = None, top_k: int | None = None) -> str`

LangChain tool that runs RAG: embed query, vector search, SpiceDB permission filtering, then return concatenated text of allowed chunks.

**Parameters:**
- `query`: User question or search text.
- `user_id`: User ID for SpiceDB checks.
- `threshold`: Similarity threshold (default from `settings.default_threshold`).
- `top_k`: Max chunks (default from `settings.default_top_k`).

**Returns:**
- `str`: Concatenated context from allowed chunks.

**Exported:** `tools = [retrieve_context]` for use with `Chat(provider, tools, system_prompt)`.

---

### short_memory

Helpers for compressing conversation for short-term memory.

#### `summarize_exchange(user_input: str, assistant_response: str) -> str`

Returns a short, cleaned summary of one turn (e.g. for appending to context).

**Parameters:**
- `user_input`: User message.
- `assistant_response`: Assistant reply (string or list of content blocks; normalized internally).

**Returns:**
- `str`: Single line like `"User: ...\nAssistant: ..."`.

#### `clean_text(text) -> str`

Normalizes and compresses text (lowercase, strip URLs/HTML, stopwords, stem/lemmatize). Used internally by `summarize_exchange`.

---

### HTTP API

[chat_routes.py](chat_routes.py) defines a FastAPI app and one endpoint.

#### `POST /chat/ask`

**Request body (JSON):**
- `user_id` (str, required): User identifier for SpiceDB.
- `query` (str, required): User question.
- `threshold` (float, optional): Default from config.
- `top_k` (int, optional): Default from config.

**Response (JSON):**
- `answer` (str): Assistant reply.
- `user_id` (str): Echo of request `user_id`.

**Example:**
```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-1", "query": "What is the capital of France?"}'
```

---

## Usage Examples

### Using the package in another app

```python
from src.user.chat import Chat, ChatProvider, settings
from src.user.chat.tools import tools

provider = ChatProvider.create_provider(
    settings.provider_type,
    model=settings.model,
    temperature=settings.temperature,
    zhipuai_api_key=settings.zhipuai_api_key,
)
chat = Chat(provider, tools, "You are a helpful assistant. Use retrieve_context.")
answer = chat.ask("user_id: u1, threshold: 1.5, top_k: 2\n\nYour question here.")
```

### Mounting the chat app in a larger FastAPI app

```python
from fastapi import FastAPI
from src.user.chat.chat_routes import app as chat_app

app = FastAPI()
app.mount("/chat", chat_app)
# POST /chat/chat/ask
```

### Switching providers via config

Set in `.env`:
```env
CHAT_PROVIDER_TYPE=google
CHAT_MODEL=gemini-2.5-flash-lite
CHAT_TEMPERATURE=0.7
GOOGLE_API_KEY=your-key
```

No code change required; the routes use `settings.provider_type` and the corresponding API key from config.

---

## Best Practices

### 1. Use one provider and set its API key

Set only the API key for the provider you use (e.g. `ZHIPUAI_API_KEY` or `GOOGLE_API_KEY`). The module passes the appropriate key based on `CHAT_PROVIDER_TYPE`.

### 2. Keep embedding models consistent

Use the same embeddings provider and model for indexing and for the chat RAG tool so query embeddings match the stored vectors. Configure `CHAT_EMBEDDINGS_PROVIDER` to match your indexing pipeline.

### 3. Pass user_id and retrieval params in the message

The agent expects `user_id`, and optionally `threshold` and `top_k`, in the message (or in the request body for `/chat/ask`) so it can call `retrieve_context` with the right permissions and retrieval settings.

### 4. Use .env for secrets

Do not commit `.env`. Copy [.env.example](.env.example), fill in values, and keep API keys in environment variables.

---

## Troubleshooting

### Import errors (e.g. `create_agent` or provider package)

**Problem:** `ImportError` for `langchain.agents.create_agent` or for a provider (e.g. `langchain_google_genai`).

**Solution:** Install the required packages. For the agent, ensure your LangChain/LangGraph version provides `create_agent`. For providers:
```bash
pip install langchain-google-genai   # Google
pip install langchain-community     # Zhipu AI (ChatZhipuAI)
```

### API key errors

**Problem:** `ValueError: zhipuai_api_key is required` (or similar).

**Solution:** Set the corresponding env var (no `CHAT_` prefix): e.g. `ZHIPUAI_API_KEY`, `GOOGLE_API_KEY`. Ensure `.env` is loaded (e.g. `load_dotenv()` in your entrypoint or use `python-dotenv`).

### JWT / `jwt.encode` errors

**Problem:** `module 'jwt' has no attribute 'encode'`.

**Solution:** The wrong `jwt` package is installed. Use PyJWT: `pip uninstall jwt && pip install PyJWT`. Do not install the `jwt` package that does not provide `encode`/`decode`.

### Relative import or module not found when running as script

**Problem:** `ImportError` when running `python chat_routes.py` from inside `src/user/chat`.

**Solution:** Run as a module from the project root: `python -m src.user.chat.chat_routes`. The script also adds the project root to `sys.path` when `__name__ == "__main__"`, so running `python chat_routes.py` from `src/user/chat` should work if the path fix runs first.

### SpiceDB or Chroma connection errors

**Problem:** Connection refused to SpiceDB or Chroma.

**Solution:** Check `CHAT_SPICEDB_ADDRESS`, `CHAT_SPICEDB_PREFIX`, and `CHAT_CHROMA_PERSIST_DIRECTORY`. Ensure SpiceDB and Chroma (or the persist directory) are reachable from the process.

---

This module is part of the user chat and RAG assistant stack.
