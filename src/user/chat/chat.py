import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
import asyncio

from dotenv import load_dotenv
load_dotenv()


project_root = os.path.abspath(os.path.join(os.getcwd(), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# 2. Import the methods from the chat module (which handles the sub-imports)
# This looks at src/user/chat/__init__.py
from src.user.chat import (
    summarize_exchange,
    InsecureClient,
    embeddings,
    embeddings_provider,
    full_retrieval,
    spice_client,
    relationship_reader,
    policy_filter,
    final_retriever
)

app = FastAPI()
# Use app.state to hold mutable server state (safer than a module-level global)
app.state.short_term_memory = ''  # List to hold recent interactions for short-term memory
model="gemini-2.5-flash-lite"
class QueryRequest(BaseModel):
    user_id: str
    query: str
    threshold: float = 1.5
    top_k: int = 2

def generate_rag_response(context, user_query, model="gemini-2.5-flash-lite"):
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    prompt = f"""
    You are the EAKAP AI Assistant. Use the following context to answer the user's question.
    If the context doesn't contain the answer, say you don't have the answer to that question.
    
    Context: {context} 
    
    Question: {user_query}
    """
    
    # Generate content using the specified Gemini model
    response = client.models.generate_content(
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3, # Low temperature for factual RAG tasks
            max_output_tokens=10000
        )
    )
    return response


@app.post("/chat/ask")
def chat_endpoint(request: QueryRequest):
    try:
        # Step 1: Generate Query Embedding
        vector = embeddings.embed_query(text=request.query)
        
        # Step 2: Vector Search
        candidates = full_retrieval.search(vector, threshold=request.threshold)
        # if not candidates:
          #  return {"answer": "I don't have enough context to answer that.", "context": "", "vector": vector}
            
        # Step 3: SpiceDB Permissions
        spice_client = InsecureClient("laughing_benz:50051", "test")
        allowed_docs = relationship_reader.get_allowed_doc_ids(request.user_id, candidates, spice_client)
        
        # Step 4: Policy Filtering & Top-K
        chunk_ids = policy_filter.filter(candidates, allowed_docs)
        
        # Step 5: Retrieve Formatted Context
        context_string = final_retriever.retrieve_chunks(chunk_ids)
        
        # if not context_string:
          #  return {"answer": "I don't have the answer to that question based on the documents you can access."}
        context_string = app.state.short_term_memory + "\n" + context_string
        # Step 6: Generate Final Response
        llm_response = generate_rag_response(context_string, request.query, model)

        app.state.short_term_memory += summarize_exchange(request.query, llm_response.text) + "\n"


        return {
            "answer": llm_response.text,
            "user_id": request.user_id,
            "chunks_used": len(chunk_ids)
        }
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())