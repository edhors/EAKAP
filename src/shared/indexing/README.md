# Indexing Module Documentation

A comprehensive module for document indexing, embedding creation, and vector store management using LangChain.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [EmbeddingsProvider](#embeddingsprovider)
  - [Embeddings](#embeddings)
  - [TextProcessor](#textprocessor)
  - [Indexer](#indexer)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The indexing module provides a complete solution for:

- **Document Loading**: Load PDFs, text files, and markdown documents
- **Text Chunking**: Split large documents into manageable chunks
- **Embedding Creation**: Generate embeddings using multiple providers (HuggingFace, Google, OpenAI, Anthropic, Mistral)
- **Vector Storage**: Store embeddings in vector databases (Chroma, InMemoryVectorStore)
- **Query Embeddings**: Create embeddings for user queries for semantic search

## Installation

### Required Dependencies

```bash
# Core dependencies
pip install langchain-text-splitters==1.1.0
pip install langchain-community==0.4.1
pip install langchain-chroma==1.1.0

# Embedding providers (install as needed)
pip install langchain-huggingface==1.2.0
pip install sentence-transformers==5.2.0

# Optional: For other providers
pip install langchain-google-genai  # Google embeddings
pip install langchain-openai        # OpenAI embeddings
pip install langchain-anthropic     # Anthropic embeddings
pip install langchain-mistralai     # Mistral embeddings
```

### Additional Requirements

- `pypdf==6.6.0` - For PDF file loading
- `bs4==0.0.2` - For HTML/Markdown processing

## Architecture

The module follows a modular design with four main components:

```
┌─────────────────────┐
│ EmbeddingsProvider  │  Factory for creating embedding providers
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Embeddings       │  Wrapper for embedding queries and documents
└──────────┬──────────┘
           │
           ├──────────────────┐
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  TextProcessor   │  │     Indexer      │
│  - Load files    │  │  - Orchestrates  │
│  - Split text    │  │    pipeline      │
└──────────────────┘  └──────────────────┘
```

## Quick Start

```python
from src.shared.indexing.embeddings_provider import EmbeddingsProvider
from src.shared.indexing.embeddings import Embeddings
from src.shared.indexing.text_processor import TextProcessor
from src.shared.indexing.indexer import Indexer
from langchain_chroma import Chroma

# 1. Create embeddings provider
provider = EmbeddingsProvider.create_provider("huggingface")
embeddings = Embeddings(provider)

# 2. Create text processor
text_processor = TextProcessor(chunk_size=1000, chunk_overlap=200)

# 3. Load documents
documents = text_processor.load_file("./data/document.pdf", file_type="pdf")

# 4. Create vector store
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embeddings._provider,
    persist_directory="./chroma_db"
)

# 5. Create indexer and index documents
indexer = Indexer(embeddings, text_processor, vector_store)
document_ids = indexer.index(documents)

# 6. Search
results = vector_store.similarity_search("your query", k=5)
```

## API Reference

### EmbeddingsProvider

Factory class for creating embedding provider instances.

#### `create_provider(provider_type: str, **config) -> Embeddings`

Creates a LangChain embeddings instance for the specified provider.

**Parameters:**
- `provider_type` (str): Type of provider. Supported values:
  - `"huggingface"` - Local embeddings (no API key needed)
  - `"google"` - Google Generative AI embeddings
  - `"openai"` - OpenAI embeddings
  - `"anthropic"` - Anthropic embeddings
  - `"mistral"` - Mistral AI embeddings
- `**config`: Provider-specific configuration:
  - **HuggingFace**: `model_name` (default: `"sentence-transformers/all-mpnet-base-v2"`)
  - **Google**: `model` (default: `"models/embedding-001"`), `google_api_key` (required)
  - **OpenAI**: `model` (default: `"text-embedding-ada-002"`), `openai_api_key` (required)
  - **Anthropic**: `model` (optional), `anthropic_api_key` (required)
  - **Mistral**: `model` (optional), `mistral_api_key` (required)

**Returns:**
- `Embeddings`: A LangChain embeddings instance

**Raises:**
- `ValueError`: If provider_type is unsupported or required config is missing
- `ImportError`: If the required package for the provider is not installed

**Example:**
```python
# HuggingFace (local, no API key)
provider = EmbeddingsProvider.create_provider("huggingface")

# Google (requires API key)
provider = EmbeddingsProvider.create_provider(
    "google",
    model="models/embedding-001",
    google_api_key=os.environ.get("GOOGLE_API_KEY")
)
```

---

### Embeddings

Wrapper class that provides a unified interface for creating embeddings.

#### `__init__(provider: LangChainEmbeddings)`

Initialize with a LangChain embeddings provider instance.

**Parameters:**
- `provider`: A LangChain Embeddings instance (created via `EmbeddingsProvider.create_provider`)

**Raises:**
- `TypeError`: If provider is not a LangChain Embeddings instance

#### `embed_query(text: str) -> List[float]`

Create embedding for a single text query.

**Parameters:**
- `text` (str): The text string to embed

**Returns:**
- `List[float]`: The embedding vector as a list of floats

**Raises:**
- `ValueError`: If text is empty or None
- `RuntimeError`: If embedding creation fails

**Example:**
```python
embeddings = Embeddings(provider)
query_embedding = embeddings.embed_query("What is machine learning?")
# Returns: [0.123, -0.456, 0.789, ...]
```

#### `embed_chunks(texts: List[str]) -> List[List[float]]`

Create embeddings for multiple text chunks.

**Parameters:**
- `texts` (List[str]): List of text strings (chunks) to embed

**Returns:**
- `List[List[float]]`: List of embedding vectors, one per input chunk

**Raises:**
- `ValueError`: If texts is empty or contains invalid entries
- `RuntimeError`: If embedding creation fails

**Example:**
```python
texts = ["Chunk 1 text", "Chunk 2 text", "Chunk 3 text"]
embeddings_list = embeddings.embed_chunks(texts)
# Returns: [[0.1, 0.2, ...], [0.3, 0.4, ...], [0.5, 0.6, ...]]
```

---

### TextProcessor

Handles document loading and text chunking.

#### `__init__(chunk_size: int = 1000, chunk_overlap: int = 200, splitter_type: str = "recursive")`

Initialize the TextProcessor with chunking parameters.

**Parameters:**
- `chunk_size` (int): Maximum size of each text chunk in characters (default: 1000)
- `chunk_overlap` (int): Number of characters to overlap between chunks (default: 200)
- `splitter_type` (str): Type of splitter to use (default: `"recursive"`)

**Raises:**
- `ValueError`: If chunk_size <= 0, chunk_overlap < 0, or chunk_overlap >= chunk_size

#### `split_text(text: str) -> List[str]`

Split a single text string into chunks.

**Parameters:**
- `text` (str): The text string to split

**Returns:**
- `List[str]`: List of text chunks as strings

**Raises:**
- `ValueError`: If text is empty or None
- `TypeError`: If text is not a string

#### `split_documents(documents: List[Document]) -> List[Document]`

Split LangChain Document objects into chunks.

**Parameters:**
- `documents` (List[Document]): List of LangChain Document objects to split

**Returns:**
- `List[Document]`: List of chunked Document objects with preserved metadata

**Raises:**
- `ValueError`: If documents list is empty or None
- `TypeError`: If documents is not a list

#### `load_file(file_path: Union[str, Path], file_type: Optional[str] = None, encoding: str = "utf-8") -> List[Document]`

Load a single file and return Document objects.

**Parameters:**
- `file_path` (Union[str, Path]): Path to the file to load
- `file_type` (Optional[str]): Type of file (`"pdf"`, `"text"`, `"markdown"`). If None, auto-detected from extension
- `encoding` (str): Encoding for text files (default: `"utf-8"`)

**Returns:**
- `List[Document]`: List of Document objects loaded from the file

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If file type is unsupported or cannot be determined
- `ImportError`: If required package for the file type is not installed

**Supported File Types:**
- PDF files (`.pdf`) - using `PyPDFLoader`
- Text files (`.txt`, `.text`) - using `TextLoader`
- Markdown files (`.md`, `.markdown`) - using `UnstructuredMarkdownLoader`

**Example:**
```python
# Auto-detect file type
documents = text_processor.load_file("./data/document.pdf")

# Explicit file type
documents = text_processor.load_file("./data/file.txt", file_type="text")
```

#### `load_directory(directory_path: Union[str, Path], glob_pattern: str = "**/*", loader_type: Optional[str] = None, show_progress: bool = False) -> List[Document]`

Load multiple files from a directory.

**Parameters:**
- `directory_path` (Union[str, Path]): Path to the directory containing files
- `glob_pattern` (str): Glob pattern to match files (default: `"**/*"`)
  - Examples: `"**/*.pdf"`, `"**/*.txt"`, `"**/*.md"`
- `loader_type` (Optional[str]): Type of loader (`"pdf"`, `"text"`, `"markdown"`). If None, auto-detected
- `show_progress` (bool): Whether to show loading progress (default: False)

**Returns:**
- `List[Document]`: List of Document objects loaded from all matching files

**Raises:**
- `FileNotFoundError`: If the directory doesn't exist
- `ValueError`: If loader_type is unsupported or cannot be determined
- `ImportError`: If required package for the loader type is not installed

**Example:**
```python
# Load all PDFs from a directory
documents = text_processor.load_directory(
    "./data",
    glob_pattern="**/*.pdf",
    loader_type="pdf",
    show_progress=True
)
```

#### `load_and_split(source: Union[str, Path], source_type: str = "file", **load_kwargs) -> List[Document]`

Load documents from a file or directory and automatically split them into chunks.

**Parameters:**
- `source` (Union[str, Path]): Path to file or directory
- `source_type` (str): Type of source (`"file"` or `"directory"`, default: `"file"`)
- `**load_kwargs`: Additional keyword arguments passed to `load_file` or `load_directory`

**Returns:**
- `List[Document]`: List of chunked Document objects

**Raises:**
- `ValueError`: If source_type is invalid

**Example:**
```python
# Load and split in one step
chunks = text_processor.load_and_split(
    "./data/document.pdf",
    source_type="file"
)
```

---

### Indexer

Orchestrates the indexing pipeline: document splitting, embedding creation, and storage.

#### `__init__(embeddings: Embeddings, text_processor: TextProcessor, vector_store: VectorStore)`

Initialize the Indexer with required components.

**Parameters:**
- `embeddings` (Embeddings): Embeddings instance (wrapper around LangChain embeddings)
- `text_processor` (TextProcessor): TextProcessor instance for splitting documents
- `vector_store` (VectorStore): VectorStore instance that must be initialized with the LangChain embeddings function (`embeddings._provider`)

**Raises:**
- `TypeError`: If any parameter is not of the expected type
- `ValueError`: If vector_store is not properly initialized

#### `index(documents: List[Document]) -> List[str]`

Process documents through the indexing pipeline and store them.

**Pipeline Steps:**
1. Splits documents into chunks using TextProcessor
2. Assigns unique `chunk_id` to each chunk (format: `{document_id}_chunk_{index}`)
3. Adds split documents to the vector store (embeddings are created automatically)
4. Returns document IDs from the vector store

**Parameters:**
- `documents` (List[Document]): List of LangChain Document objects to index

**Returns:**
- `List[str]`: List of document IDs returned by the vector store

**Raises:**
- `ValueError`: If documents list is empty or None
- `TypeError`: If documents is not a list or contains invalid items
- `RuntimeError`: If indexing fails at any step

**Note:** The Indexer automatically assigns `chunk_id` to each chunk based on its position. If `document_id` exists in metadata, the format is `{document_id}_chunk_{index}`. Otherwise, it uses `chunk_{index}`.

**Example:**
```python
indexer = Indexer(embeddings, text_processor, vector_store)

# Add document_id to metadata before indexing
for doc in documents:
    doc.metadata["document_id"] = "doc_1"

# Index documents
document_ids = indexer.index(documents)
# Each chunk will have chunk_id like "doc_1_chunk_0", "doc_1_chunk_1", etc.
```

---

## Usage Examples

### Complete Indexing Workflow

```python
from src.shared.indexing.embeddings_provider import EmbeddingsProvider
from src.shared.indexing.embeddings import Embeddings
from src.shared.indexing.text_processor import TextProcessor
from src.shared.indexing.indexer import Indexer
from langchain_chroma import Chroma
import os

# Step 1: Create embeddings
provider = EmbeddingsProvider.create_provider("huggingface")
embeddings = Embeddings(provider)

# Step 2: Create text processor
text_processor = TextProcessor(chunk_size=1000, chunk_overlap=200)

# Step 3: Load documents
documents = text_processor.load_file("./data/document.pdf", file_type="pdf")

# Step 4: Add metadata
for doc in documents:
    doc.metadata["document_id"] = "doc_1"
    doc.metadata["source"] = "document.pdf"

# Step 5: Create vector store
vector_store = Chroma(
    collection_name="documents_collection",
    embedding_function=embeddings._provider,
    persist_directory="./chroma_db"
)

# Step 6: Create indexer and index
indexer = Indexer(embeddings, text_processor, vector_store)
document_ids = indexer.index(documents)

print(f"Indexed {len(document_ids)} chunks")
```

### Using Different Embedding Providers

```python
# HuggingFace (local, no API key)
provider = EmbeddingsProvider.create_provider("huggingface")

# Google (requires API key)
provider = EmbeddingsProvider.create_provider(
    "google",
    model="models/embedding-001",
    google_api_key=os.environ.get("GOOGLE_API_KEY")
)

# OpenAI (requires API key)
provider = EmbeddingsProvider.create_provider(
    "openai",
    model="text-embedding-ada-002",
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)
```

### Loading Multiple Files

```python
# Load all PDFs from a directory
documents = text_processor.load_directory(
    "./data",
    glob_pattern="**/*.pdf",
    loader_type="pdf",
    show_progress=True
)

# Load and split in one step
chunks = text_processor.load_and_split(
    "./data/document.pdf",
    source_type="file"
)
```

### Creating Query Embeddings

```python
# Use the same embeddings instance used for indexing
user_query = "What is machine learning?"
query_embedding = embeddings.embed_query(user_query)

# Use query_embedding for semantic search
# (vector stores handle this automatically with similarity_search)
results = vector_store.similarity_search(user_query, k=5)
```

### Searching Indexed Documents

```python
# Simple similarity search
results = vector_store.similarity_search("your query", k=5)

# Search with metadata filtering
results = vector_store.similarity_search(
    "your query",
    k=5,
    filter={"document_id": "doc_1"}
)

# Access results
for result in results:
    print(f"Content: {result.page_content[:100]}...")
    print(f"Metadata: {result.metadata}")
    print(f"Chunk ID: {result.metadata.get('chunk_id')}")
```

---

## Best Practices

### 1. Use Consistent Embedding Models

Always use the same embedding model/provider for both indexing and querying to ensure compatibility.

```python
# Good: Same provider for both
provider = EmbeddingsProvider.create_provider("huggingface")
embeddings = Embeddings(provider)
# Use this for both indexing and querying
```

### 2. Set Document IDs Before Indexing

Add `document_id` to metadata before indexing to enable proper chunk tracking.

```python
for doc in documents:
    doc.metadata["document_id"] = "unique_doc_id"
    
# Indexer will create chunk_ids like "unique_doc_id_chunk_0"
document_ids = indexer.index(documents)
```

### 3. Choose Appropriate Chunk Sizes

- **Small chunks (500-800)**: Better for precise retrieval, more chunks
- **Medium chunks (1000-1500)**: Balanced approach (default)
- **Large chunks (2000+)**: Better context, fewer chunks

```python
# For technical documents
text_processor = TextProcessor(chunk_size=1500, chunk_overlap=300)

# For general text
text_processor = TextProcessor(chunk_size=1000, chunk_overlap=200)
```

### 4. Use Persistent Vector Stores for Production

```python
# Production: Use Chroma with persistence
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embeddings._provider,
    persist_directory="./chroma_db"  # Persists to disk
)

# Development/Testing: Use InMemoryVectorStore
from langchain_core.vectorstores import InMemoryVectorStore
vector_store = InMemoryVectorStore(embeddings._provider)
```

### 5. Handle Errors Gracefully

```python
try:
    documents = text_processor.load_file("./data/document.pdf")
except FileNotFoundError:
    print("File not found")
except ImportError as e:
    print(f"Missing dependency: {e}")
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

---

## Troubleshooting

### Import Errors

**Problem:** `ImportError: langchain-huggingface package is required`

**Solution:** Install the required package:
```bash
pip install langchain-huggingface
```

### API Key Errors

**Problem:** `ValueError: google_api_key is required`

**Solution:** Provide the API key in config or set environment variable:
```python
# Option 1: In code
provider = EmbeddingsProvider.create_provider(
    "google",
    google_api_key="your-api-key"
)

# Option 2: Environment variable
import os
os.environ["GOOGLE_API_KEY"] = "your-api-key"
provider = EmbeddingsProvider.create_provider("google")
```

### Vector Store Not Initialized

**Problem:** `ValueError: vector_store must have an 'add_documents' method`

**Solution:** Ensure the vector store is initialized with the embeddings function:
```python
# Correct
vector_store = Chroma(
    embedding_function=embeddings._provider,  # Use _provider, not embeddings
    ...
)

# Incorrect
vector_store = Chroma(embedding_function=embeddings, ...)
```

### Chunk IDs Not Assigned

**Problem:** Chunks don't have `chunk_id` in metadata

**Solution:** The Indexer automatically assigns `chunk_id` during indexing. If you see old values, clear the vector store and re-index:
```python
import shutil
shutil.rmtree("./chroma_db", ignore_errors=True)
# Recreate vector store and re-index
```

### File Loading Fails

**Problem:** `FileNotFoundError` or unsupported file type

**Solution:**
- Check file path is correct
- Ensure file type is supported (PDF, text, markdown)
- Install required packages (`pypdf` for PDFs)

---

## License

This module is part of the shared indexing infrastructure.
