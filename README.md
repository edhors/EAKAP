![FastAPI](https://img.shields.io/badge/FastAPI-0.128.5-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.2.6-2A4B8D)
![SpiceDB](https://img.shields.io/badge/SpiceDB-authzed%201.24.1-000000)
![Chroma](https://img.shields.io/badge/Chroma-1.1.0-FF6F00)
![SQLModel](https://img.shields.io/badge/SQLModel-0.0.31-FF4B4B)

# EAKAP (Enterprise AI Assistant for Document Intelligence & Workflow Automation)

Enterprise AI Knowledge Assistant Platform (EAKAP) is a secure, enterprise-grade AI assistant that answers employee questions using only the internal documents they are authorized to access. The system combines Retrieval-Augmented Generation (RAG) with deterministic access control so that authorization decisions remain strict and auditable while the LLM remains sandboxed to approved content.

## Why it exists

Modern companies store policies, reports, and project documents across multiple systems with strict access rules. Searching these documents accurately and quickly is hard, which reduces productivity. EAKAP addresses this by splitting deterministic security (SpiceDB) from non-deterministic generation (LLM + RAG), minimizing data leakage risk while keeping answers fast and relevant.

## Key features

- Permission-aware RAG with SpiceDB-backed access control
- OAuth 2.1 Authorization Code + PKCE authentication and JWT access tokens
- Multi-provider LLM support (Google, OpenAI, Anthropic, Mistral, Zhipu, HuggingFace)
- Modular indexing pipeline (loader, chunker, embeddings, vector store)
- User and document metadata persistence with Turso (libSQL)

## High-level architecture

```
[User] -> [Auth (/auth)] -> [Chat API (/chat/ask)]
                       -> [RAG Pipeline]
                          -> Embeddings -> Chroma
                          -> FullRetrieval (vector search)
                          -> SpiceDB (ACL filter)
                          -> FinalRetrieval (chunk fetch)
                          -> LLM response
```

## Repo layout

- `src/main.py` FastAPI app entrypoint
- `src/routers/` HTTP routes (`/auth`, `/chat`)
- `src/shared/auth/` OAuth PKCE + JWT auth
- `src/shared/userdb_handler/` user + token persistence (Turso)
- `src/shared/documentdb_handler/` document metadata persistence (Turso embedded replica)
- `src/shared/indexing/` document loading, chunking, embeddings, vector store
- `src/shared/spicedb_handler/` schema + relationships for RBAC
- `src/user/chat/` LLM agent + RAG tools
- `src/user/full_retrieval/` distance-based retrieval against Chroma
- `src/user/final_retrieval/` policy filter + chunk fetch

## Quickstart

### 1) Install dependencies

```bash
pip install -r requirements.txt
pip install uvicorn
```

### 2) Configure environment

Create a `.env` file in the repo root:

```env
# Auth (env prefix: auth_)
auth_secret_key=replace_me
auth_oauth_client_id=your_client_id
auth_oauth_redirect_uri=http://localhost:3000/callback

# Turso (user + document DBs)
turso_database_url=libsql://your-db-name-your-org.turso.io
turso_auth_token=your_turso_token

# Chat / RAG (env prefix: chat_)
chat_provider_type=google
chat_model=gemini-2.5-flash-lite
chat_spicedb_address=localhost:50051
chat_spicedb_prefix=test
chat_chroma_collection_name=documents_collection
chat_chroma_ip=127.0.0.1
chat_chroma_port=8123

# Provider API key (one of these, matching chat_provider_type)
GOOGLE_API_KEY=your_key
# OPENAI_API_KEY=your_key
# ANTHROPIC_API_KEY=your_key
# MISTRAL_API_KEY=your_key
# ZHIPUAI_API_KEY=your_key
```

### 3) Start dependencies

- SpiceDB setup: [docs/spicedb/spicedb-setup.md](docs/spicedb/spicedb-setup.md)
- Quick SpiceDB run script: [docs/internship_server_run.sh](docs/internship_server_run.sh)
- Turso setup: [docs/userdb/setup-and-usage.md](docs/userdb/setup-and-usage.md)
- Ensure a Chroma server is running and reachable at `chat_chroma_ip:chat_chroma_port`

### 4) Initialize databases

```bash
python -c "from src.shared.userdb_handler import init_db; init_db()"
python -c "from src.shared.documentdb_handler import init_db; init_db()"
```

### 5) Run the API server

```bash
uvicorn src.main:app --reload
```

## API examples

### Register a user

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "tenant_id": "tenant-1",
    "dept": "engineering",
    "project": "proj-a",
    "clearance": 2
  }'
```

### Login and exchange token (PKCE)

```bash
# 1) Login (returns authorization code)
curl -s -X POST "http://localhost:8000/auth/login?client_id=your_client_id&redirect_uri=http://localhost:3000/callback&code_challenge=challenge&code_challenge_method=S256" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# 2) Exchange code for access token
curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"grant_type": "authorization_code", "code": "<auth_code>", "code_verifier": "<verifier>", "client_id": "your_client_id"}'
```

### Ask a question

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our remote work policy?", "threshold": 1.5, "top_k": 2}'
```

## Indexing documents (example)

```python
from src.shared.indexing.embeddings_provider import EmbeddingsProvider
from src.shared.indexing.embeddings import Embeddings
from src.shared.indexing.text_processor import TextProcessor
from src.shared.indexing.indexer import Indexer
from langchain_chroma import Chroma

provider = EmbeddingsProvider.create_provider("huggingface")
embeddings = Embeddings(provider)
text_processor = TextProcessor(chunk_size=1000, chunk_overlap=200)
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embeddings._provider,
    persist_directory="./chroma_db"
)
indexer = Indexer(embeddings, text_processor, vector_store)
indexer.index("Your document text", doc_id="doc_1")
```

## Additional documentation

- [docs/spicedb/spicedb-setup.md](docs/spicedb/spicedb-setup.md) SpiceDB + Postgres setup (Docker)
- [docs/userdb/setup-and-usage.md](docs/userdb/setup-and-usage.md) Turso setup and user DB usage
- [src/shared/auth/README.md](src/shared/auth/README.md) OAuth PKCE auth module details
- [src/shared/userdb_handler/README.md](src/shared/userdb_handler/README.md) User DB API details
- [src/shared/documentdb_handler/README.md](src/shared/documentdb_handler/README.md) Document DB API details
- [src/shared/spicedb_handler/README.md](src/shared/spicedb_handler/README.md) SpiceDB schema and relationship tools
- [src/shared/indexing/README.md](src/shared/indexing/README.md) Indexing module API and examples
- [src/user/chat/README.md](src/user/chat/README.md) Chat module configuration and usage
- [src/user/full_retrieval/README.md](src/user/full_retrieval/README.md) Full retrieval module API
- [src/user/final_retrieval/README.md](src/user/final_retrieval/README.md) Final retrieval pipeline
- [tests/shared/indexing/unit_tests/README.md](tests/shared/indexing/unit_tests/README.md) Indexing unit tests

## Testing

```bash
pytest -q
```
