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

# 3. Create vector store
vector_store = Chroma(
    collection_name="documents",
    embedding_function=embeddings._provider,
    persist_directory="./chroma_db"
)

# 4. Create indexer and index
indexer = Indexer(embeddings, text_processor, vector_store)

# Option A: Index text directly
indexer.index("Your text content here", doc_id="doc_1")

# Option B: Load from file and index (load_file sets doc_id on each document)
documents = text_processor.load_file("./data/document.pdf", file_type="pdf")
indexer.index(documents)

# 5. Search
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

#### `assign_doc_id(documents: List[Document], doc_id: str) -> None` *(static)*

Set `doc_id` on each document's metadata. Use this when you have a list of documents (e.g. chunks from the same source) that should share one document identifier. Modifies documents in place.

**Parameters:**
- `documents` (List[Document]): List of LangChain Document objects to tag
- `doc_id` (str): Document identifier to set on each document's metadata

**Returns:**
- `None`

**Raises:**
- `ValueError`: If documents is None or if doc_id is empty or whitespace
- `TypeError`: If documents is not a list

**Example:**
```python
# Assign the same doc_id to all documents (e.g. from one file)
TextProcessor.assign_doc_id(documents, "doc_1")
```

**Note:** `load_file` calls this internally so loaded documents already have `doc_id` set (from the `doc_id` parameter or the file path stem).

#### `load_file(file_path: Union[str, Path], file_type: Optional[str] = None, encoding: str = "utf-8", doc_id: Optional[str] = None) -> List[Document]`

Load a single file and return Document objects. Each returned document has `doc_id` set in metadata (from `doc_id` if provided, otherwise the file path stem).

**Parameters:**
- `file_path` (Union[str, Path]): Path to the file to load
- `file_type` (Optional[str]): Type of file (`"pdf"`, `"text"`, `"markdown"`). If None, auto-detected from extension
- `encoding` (str): Encoding for text files (default: `"utf-8"`)
- `doc_id` (Optional[str]): Document identifier for all loaded chunks. If None, uses the file path stem (e.g. `"document"` for `document.pdf`)

**Returns:**
- `List[Document]`: List of Document objects loaded from the file, each with `doc_id` in metadata

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
# Auto-detect file type; doc_id defaults to file stem (e.g. "document")
documents = text_processor.load_file("./data/document.pdf")

# Explicit file type and custom doc_id (e.g. for SpiceDB alignment)
documents = text_processor.load_file("./data/file.txt", file_type="text", doc_id="doc_1")
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

#### `index(text: Union[str, List[str]], doc_id: Optional[Union[str, List[str]]] = None) -> None`

Process text through the indexing pipeline and store it.

**Pipeline Steps:**
1. Converts text strings to Document objects
2. Splits documents into chunks using TextProcessor
3. Assigns unique `chunk_id` to each chunk (format: `{doc_id}_chunk_{index}`)
4. Adds split documents to the vector store (embeddings are created automatically)

**Parameters:**
- `text` (Union[str, List[str]]): A single text string or list of text strings to index
- `doc_id` (Optional[Union[str, List[str]]]): Optional document ID(s). If a single string, used for all texts. If a list, must match the length of text list. If None, 'default' is used.

**Returns:**
- `None`

**Raises:**
- `ValueError`: If text is empty or None, or if doc_id list length doesn't match text list
- `TypeError`: If text is not a string or list of strings
- `RuntimeError`: If indexing fails at any step

**Note:** The Indexer automatically assigns `chunk_id` to each chunk based on its position. The format is `{doc_id}_chunk_{index}` where `doc_id` comes from the doc_id parameter or 'default' if not provided.

**Example:**
```python
indexer = Indexer(embeddings, text_processor, vector_store)

# Index a single text string
indexer.index("This is some text to index", doc_id="doc_1")
# Each chunk will have chunk_id like "doc_1_chunk_0", "doc_1_chunk_1", etc.

# Index multiple texts with same doc_id
indexer.index(["Text 1", "Text 2", "Text 3"], doc_id="doc_1")

# Index multiple texts with different doc_ids
indexer.index(
    ["Text 1", "Text 2", "Text 3"],
    doc_id=["doc_1", "doc_2", "doc_3"]
)
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

# Step 3: Create vector store
vector_store = Chroma(
    collection_name="documents_collection",
    embedding_function=embeddings._provider,
    persist_directory="./chroma_db"
)

# Step 4: Create indexer
indexer = Indexer(embeddings, text_processor, vector_store)

# Step 5: Index text directly
indexer.index("Your document text content here", doc_id="doc_1")

# Or load from file and index (load_file sets doc_id automatically; pass custom doc_id if needed)
documents = text_processor.load_file("./data/document.pdf", file_type="pdf")
indexer.index(documents)

print("Documents indexed successfully")
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

### 2. Set Document IDs When Indexing

Document IDs enable proper chunk tracking and alignment with systems like SpiceDB. Use `doc_id` when indexing raw text, or rely on `load_file` which sets `doc_id` automatically (file path stem or a custom value).

```python
# When loading from file: doc_id is set by load_file (default: file stem, or pass doc_id="custom")
documents = text_processor.load_file("./data/document.pdf", doc_id="doc_1")
indexer.index(documents)  # chunk_ids will use doc_id from metadata

# When indexing raw text: pass doc_id explicitly
indexer.index("Your text here", doc_id="unique_doc_id")
indexer.index(["Text 1", "Text 2"], doc_id="unique_doc_id")
indexer.index(["Text 1", "Text 2"], doc_id=["doc_1", "doc_2"])
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
