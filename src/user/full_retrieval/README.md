# Full Retrieval Module

## Overview

The `full_retrieval` module provides a similarity search functionality using pre-computed query embeddings against a ChromaDB vectorstore. Unlike traditional retrieval systems that accept text queries, this module works directly with embedding vectors, making it suitable for scenarios where embeddings are computed separately or reused across multiple queries.

## Purpose

This module is designed to:
- Perform similarity search using pre-computed query embeddings (not text)
- Filter results by a configurable similarity threshold
- Return structured results with document IDs, chunk IDs, and similarity scores
- Support both path-based and dependency injection initialization patterns

## Architecture

The module consists of a single class `FullRetrieval` that encapsulates all retrieval logic:

```
src/user/full_retrieval/
├── __init__.py          # Empty module file (no exports)
├── full_retriever.py    # Main FullRetrieval class implementation
└── README.md            # This file
```

## Class: FullRetrieval

### Initialization

The `FullRetrieval` class supports two initialization patterns:

#### 1. Path-based Initialization

Initialize by providing ChromaDB connection parameters:

```python
from src.user.full_retrieval.full_retriever import FullRetrieval
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

retriever = FullRetrieval(
    persist_directory="./chroma_langchain_db",
    collection_name="documents_collection",
    embedding_function=embeddings
)
```

**Parameters:**
- `persist_directory` (str, required): Path to the ChromaDB persistence directory
- `collection_name` (str, required): Name of the ChromaDB collection
- `embedding_function` (LangChainEmbeddings, required): LangChain embeddings instance (must match embeddings used during indexing)

#### 2. Dependency Injection

Initialize by providing an existing Chroma vectorstore instance:

```python
from langchain_chroma import Chroma
from src.user.full_retrieval.full_retriever import FullRetrieval

vector_store = Chroma(
    collection_name="documents_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db"
)

retriever = FullRetrieval(vector_store=vector_store)
```

**Parameters:**
- `vector_store` (Chroma, required): Existing Chroma vectorstore instance

### Method: search()

Performs similarity search using pre-computed query embeddings.

#### Signature

```python
def search(
    self,
    query_embeddings: List[float],
    threshold: float = 0.5,
    k: Optional[int] = None
) -> List[Dict[str, Any]]
```

#### Parameters

- **query_embeddings** (List[float], required): 
  - List of float values representing the query embedding vector
  - Must be non-empty and contain only finite numeric values
  - Dimension must match the embedding dimension used during indexing

- **threshold** (float, optional, default=0.5):
  - Minimum similarity score (0-1) to include in results
  - Results with similarity scores below this threshold are filtered out
  - Range: 0.0 to 1.0 (inclusive)

- **k** (int, optional, default=None):
  - Maximum number of candidate results to retrieve before threshold filtering
  - If None, retrieves all results (up to 10,000)
  - Useful for performance optimization when only top results are needed

#### Returns

List of dictionaries, each containing:
- `doc_id` (str): Document identifier (shared by all chunks from the same document)
- `chunk_id` (str): Unique chunk identifier
- `score` (float): Similarity score (0.0 to 1.0, higher is more similar)

**Format:**
```python
[
    {"doc_id": "doc_1", "chunk_id": "doc_1_chunk_0", "score": 0.85},
    {"doc_id": "doc_1", "chunk_id": "doc_1_chunk_1", "score": 0.72},
    ...
]
```

#### Example Usage

```python
# Create query embeddings (example using LangChain)
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

query_text = "What is bioremediation?"
query_embeddings = embeddings.embed_query(query_text)

# Perform search
results = retriever.search(
    query_embeddings=query_embeddings,
    threshold=0.6,
    k=10
)

# Process results
for result in results:
    print(f"Document: {result['doc_id']}, Chunk: {result['chunk_id']}, Score: {result['score']:.4f}")
```

## Implementation Details

### Similarity Score Calculation

The module converts ChromaDB distance values to similarity scores:

1. **Distance to Similarity Conversion**: 
   - ChromaDB returns cosine distances (0 = identical, 2 = opposite)
   - Similarity score = `1 - distance`
   - Scores are clamped to [0, 1] range

2. **Threshold Filtering**:
   - Only results with `similarity_score >= threshold` are included
   - Results are returned in descending order of similarity (most similar first)

### Metadata Extraction

The module extracts `doc_id` and `chunk_id` from ChromaDB metadata:

1. **Primary Source**: Metadata dictionary from ChromaDB
2. **Fallback**: If metadata is missing, uses the document ID as fallback
3. **Validation**: Ensures all returned values are strings

### Error Handling

The module includes comprehensive error handling:

#### Input Validation
- Validates query embeddings are non-empty lists
- Checks for NaN and Infinity values
- Validates threshold is between 0 and 1
- Validates k is a positive integer if provided

#### ChromaDB Errors
- Handles missing or inaccessible collections
- Validates query result structure
- Handles dimension mismatches
- Provides descriptive error messages

#### Runtime Errors
- Validates collection initialization
- Handles metadata extraction failures
- Skips invalid results (NaN/Infinity distances) instead of failing
- Provides context in error messages

### Performance Considerations

1. **k Parameter**: Use `k` to limit candidates when you only need top results
2. **Threshold**: Higher thresholds reduce result processing time
3. **Empty Collections**: Returns empty list immediately if collection is empty
4. **Batch Processing**: Processes results sequentially but efficiently

## Dependencies

- `langchain_chroma`: ChromaDB integration for LangChain
- `langchain_core`: Core LangChain types (Embeddings interface)
- Python standard library: `typing`, `math`

## Expected ChromaDB Structure

The module expects chunks stored in ChromaDB with the following metadata structure:

```python
{
    "doc_id": "doc_1",           # Document identifier (required)
    "chunk_id": "doc_1_chunk_0",  # Chunk identifier (required)
    # ... other metadata fields
}
```

## Error Messages

Common errors and their meanings:

- **"query_embeddings must be a non-empty list"**: Provide a valid embedding vector
- **"threshold must be between 0 and 1"**: Adjust threshold to valid range
- **"ChromaDB persistence directory not found"**: Check persist_directory path
- **"Invalid query embeddings format or dimension mismatch"**: Ensure embedding dimension matches collection
- **"ChromaDB collection is None"**: Collection may not exist or initialization failed

## Best Practices

1. **Embedding Consistency**: Use the same embedding model/function that was used during indexing
2. **Threshold Tuning**: Start with 0.5 and adjust based on result quality
3. **k Parameter**: Use `k` when you only need top-N results for better performance
4. **Error Handling**: Wrap search calls in try-except blocks for production code
5. **Metadata Validation**: Ensure your indexed chunks have proper `doc_id` and `chunk_id` metadata

## Limitations

1. **Single Query**: Currently processes one query embedding at a time
2. **Cosine Similarity**: Assumes cosine distance metric (may need adjustment for other metrics)
3. **Metadata Dependency**: Relies on proper metadata structure in ChromaDB
4. **No Text Input**: Does not accept text queries directly (embeddings must be pre-computed)

## Testing

See `full_retrieval_test.ipynb` in the project root for comprehensive usage examples and testing scenarios.
