import sys
import os
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Adjusting imports to match the project root structure
from src.user.chat.chat_routes import app
from src.user.chat.short_memory import clean_text, summarize_exchange
from src.user.chat.chat_provider import ChatProvider
from src.user.chat.config import settings

client = TestClient(app)

# --- Unit Tests: short_memory.py ---
def test_clean_text_processing():
    """Tests if text cleaning removes stop words, punctuation, and applies stemming."""
    raw_text = "What is the capital of France? It is Paris!"
    cleaned = clean_text(raw_text)
    # Expected behavior: "capit franc pari" (stemmed and stopwords removed)
    assert "franc" in cleaned
    assert "pari" in cleaned
    assert "the" not in cleaned

def test_summarize_exchange_format():
    """Tests the formatting of the summary for short term memory."""
    summary = summarize_exchange("Hello AI", "Hello User")
    assert "User:" in summary
    assert "Assistant:" in summary

# --- Unit Tests: chat_provider.py ---
def test_chat_provider_invalid_type():
    """Tests that the factory raises ValueError for unsupported providers."""
    with pytest.raises(ValueError, match="Unsupported provider type"):
        ChatProvider.create_provider("invalid_llm", google_api_key="test")

# --- Integration Tests: chat_routes.py & chat.py ---
@patch("src.user.chat.chat_routes._chat.ask")
def test_chat_endpoint_success(mock_ask):
    """Tests the /chat/ask endpoint and short_term_memory update."""
    mock_ask.return_value = "The capital of France is Paris."
    
    payload = {
        "user_id": "user_123",
        "query": "What is the capital of France?",
        "threshold": 1.2,
        "top_k": 3
    }
    
    response = client.post("/chat/ask", json=payload)
    
    assert response.status_code == 200
    assert response.json()["answer"] == "The capital of France is Paris."
    # Verify memory was updated in app state via the summarize_exchange logic
    assert "franc" in app.state.short_term_memory

@patch("src.user.chat.chat_routes._chat.ask")
def test_chat_endpoint_error_handling(mock_ask):
    """Tests if the API correctly returns a 500 error on LLM failure."""
    mock_ask.side_effect = Exception("LLM connection failed")
    
    payload = {"user_id": "user_1", "query": "error test"}
    response = client.post("/chat/ask", json=payload)
    
    assert response.status_code == 500
    assert "LLM connection failed" in response.json()["detail"]

# --- Tool Tests: src/user/chat/tools.py ---
@patch("src.user.chat.tools.embeddings")
@patch("src.user.chat.tools.full_retrieval")
@patch("src.user.chat.tools.relationship_reader")
@patch("src.user.chat.tools.final_retriever")
@patch("src.user.chat.tools.InsecureClient")
def test_retrieve_context_tool(mock_spice, mock_final, mock_rel, mock_retrieval, mock_emb):
    """Tests the retrieve_context tool logic including SpiceDB filtering."""
    from src.user.chat.tools import retrieve_context
    
    # Setup mocks for the RAG pipeline
    mock_emb.embed_query.return_value = [0.1, 0.2]
    mock_retrieval.search.return_value = [
    {"doc_id": "doc1", "chunk_id": "chunk_1", "score": "0.9"},
    {"doc_id": "doc2", "chunk_id": "chunk_2", "score": "0.8"}
    ]
    mock_rel.get_allowed_doc_ids.return_value = ["doc1"] # Simulation: only doc1 allowed
    mock_final.retrieve_chunks.return_value = "Content from doc1"
    
    
    result = retrieve_context.invoke({
    "query": "search query", 
    "user_id": "user_1", 
    "threshold": 1.5, 
    "top_k": 2
})
    
    assert result == "Content from doc1"
    mock_rel.get_allowed_doc_ids.assert_called_once()
    mock_spice.assert_called_once_with(settings.spicedb_address, settings.spicedb_prefix)