# Final Retrieval Module

A policy-aware retrieval system for RAG (Retrieval-Augmented Generation) pipelines. This module filters document chunks based on user permissions (ACL) and retrieves relevant content from a Chroma vector store.

## Overview

This module is part of the **EAKAP** (Enterprise AI Knowledge Assistant Platform) project. It ensures that users only receive document chunks they have permission to access, while maintaining relevance ranking.

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INPUTS                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Full Retrieval Output              SpiceDB Output                      │
│  [candidates]                       [allowed_doc_ids]                   │
│  ┌──────────────────────┐           ┌──────────────────┐               │
│  │ doc_id: 'doc_1'      │           │ 'doc_1'          │               │
│  │ chunk_id: 'chunk_1'  │           │ 'doc_2'          │               │
│  │ score: '0.92'        │           │ 'doc_3'          │               │
│  └──────────────────────┘           └──────────────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        policy_filter.py                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌─────────────────────────────────────────────────────────────┐     │
│    │  Step 1: policy_filter()                                     │     │
│    │  Filter candidates by allowed_doc_ids (ACL check)            │     │
│    └─────────────────────────────────────────────────────────────┘     │
│                                 │                                       │
│                                 ▼                                       │
│    ┌─────────────────────────────────────────────────────────────┐     │
│    │  Step 2: sort_and_select_top_k()                             │     │
│    │  Sort by score (descending), select top K                    │     │
│    └─────────────────────────────────────────────────────────────┘     │
│                                 │                                       │
│                                 ▼                                       │
│    ┌─────────────────────────────────────────────────────────────┐     │
│    │  Step 3: extract_chunk_ids()                                 │     │
│    │  Extract chunk_id list from selected candidates              │     │
│    └─────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                         [chunk_ids list]
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       final_retriever.py                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌─────────────────────────────────────────────────────────────┐     │
│    │  Step 4: retrieve_chunks()                                   │     │
│    │  Fetch chunk text from Chroma vector store                   │     │
│    │  Build formatted context string                              │     │
│    └─────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Context String (for LLM)                                               │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │ Source: {'doc_id': 'doc_1', 'source': 'policy.pdf'}          │      │
│  │ Content: Remote work is allowed up to 3 days per week.       │      │
│  │                                                               │      │
│  │ Source: {'doc_id': 'doc_2', 'source': 'handbook.pdf'}        │      │
│  │ Content: The engineering team follows agile methodology.     │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Installation

### Dependencies

```bash
pip install langchain-chroma
```

### File Structure

```
your_project/
├── policy_filter.py      # Steps 1-3: Filter, sort, extract
└── final_retriever.py    # Step 4: Chroma retrieval
```

## Usage

### Quick Start

```python
from policy_filter import PolicyFilter
from final_retriever import FinalRetriever

# Input from Full Retrieval (upstream)
candidates = [
    {'doc_id': 'doc_1', 'chunk_id': 'doc_1_chunk_1', 'score': '0.88'},
    {'doc_id': 'doc_1', 'chunk_id': 'doc_1_chunk_2', 'score': '0.92'},
    {'doc_id': 'doc_2', 'chunk_id': 'doc_2_chunk_1', 'score': '0.85'},
]

# Input from SpiceDB (user permissions)
allowed_doc_ids = ['doc_1', 'doc_2']

# Step 1-3: Initialize PolicyFilter and get chunk IDs
# The top_k value is now set during initialization
pf = PolicyFilter(top_k=2)
chunk_ids = pf.filter(
    candidates=candidates,
    allowed_doc_ids=allowed_doc_ids
)
# Output: ['doc_1_chunk_2', 'doc_1_chunk_1']

# Step 4: Initialize FinalRetriever and retrieve from Chroma
# The vector_store is now passed during initialization
retriever = FinalRetriever(vector_store)
context = retriever.retrieve_chunks(chunk_ids)

# Use in LLM prompt
prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: What is the remote work policy?
"""
```

### Step-by-Step Usage

```python
from policy_filter import PolicyFilter
from final_retriever import FinalRetriever

# Initialize the modules
pf = PolicyFilter(top_k=2) # top_k is now set at the class level
retriever = FinalRetriever(vector_store) # vector_store is passed at init

# Step 1: Filter by policy (ACL check)
filtered = pf.policy_filter(candidates, allowed_doc_ids)

# Step 2: Sort by score and select top K
# Note: This now uses the top_k value provided during pf initialization
selected = pf.sort_and_select_top_k(filtered)

# Step 3: Extract chunk IDs
chunk_ids = pf.extract_chunk_ids(selected)

# Step 4: Retrieve from Chroma
context = retriever.retrieve_chunks(chunk_ids)
```

## API Reference

### policy_filter.py

#### `policy_filter(candidates, allowed_doc_ids) -> list[dict]`

Filters candidates by allowed document IDs (ACL check).

| Parameter | Type | Description |
|-----------|------|-------------|
| `candidates` | `list[dict]` | List of candidates from Full Retrieval. Each dict must have `doc_id`, `chunk_id`, `score` |
| `allowed_doc_ids` | `list[str]` | List of document IDs the user has permission to access |

**Returns:** Filtered list of candidates (only allowed docs)

**Example:**
```python
candidates = [
    {'doc_id': 'doc_1', 'chunk_id': 'chunk_1', 'score': '0.9'},
    {'doc_id': 'doc_2', 'chunk_id': 'chunk_2', 'score': '0.8'},  # Not allowed
]
allowed = ['doc_1']

result = policy_filter(candidates, allowed)
# [{'doc_id': 'doc_1', 'chunk_id': 'chunk_1', 'score': '0.9'}]
```

---

#### `sort_and_select_top_k(candidates, top_k=2) -> list[dict]`

Sorts candidates by score (descending) and selects top K.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `candidates` | `list[dict]` | - | Filtered candidates from `policy_filter()` |
| `top_k` | `int` | `2` | Number of top candidates to select |

**Returns:** Top K candidates sorted by score (highest first)

**Example:**
```python
candidates = [
    {'doc_id': 'doc_1', 'chunk_id': 'chunk_1', 'score': '0.7'},
    {'doc_id': 'doc_1', 'chunk_id': 'chunk_2', 'score': '0.9'},
    {'doc_id': 'doc_1', 'chunk_id': 'chunk_3', 'score': '0.8'},
]

result = sort_and_select_top_k(candidates, top_k=2)
# [
#   {'doc_id': 'doc_1', 'chunk_id': 'chunk_2', 'score': '0.9'},
#   {'doc_id': 'doc_1', 'chunk_id': 'chunk_3', 'score': '0.8'},
# ]
```

---

#### `extract_chunk_ids(candidates) -> list[str]`

Extracts chunk_ids from candidates list.

| Parameter | Type | Description |
|-----------|------|-------------|
| `candidates` | `list[dict]` | List from `sort_and_select_top_k()` |

**Returns:** List of chunk_ids (preserves order)

**Example:**
```python
candidates = [
    {'doc_id': 'doc_1', 'chunk_id': 'chunk_2', 'score': '0.9'},
    {'doc_id': 'doc_1', 'chunk_id': 'chunk_3', 'score': '0.8'},
]

result = extract_chunk_ids(candidates)
# ['chunk_2', 'chunk_3']
```

---

#### `get_filtered_chunk_ids(candidates, allowed_doc_ids, top_k=2) -> list[str]`

Combined pipeline: filter → sort → top-k → extract chunk_ids.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `candidates` | `list[dict]` | - | List from Full Retrieval |
| `allowed_doc_ids` | `list[str]` | - | List from SpiceDB |
| `top_k` | `int` | `2` | Number of top chunks to select |

**Returns:** List of chunk_ids

---

### final_retriever.py

#### `retrieve_chunks(vector_store, chunks) -> str`

Fetches chunk texts from Chroma vector store and builds a formatted context string.

| Parameter | Type | Description |
|-----------|------|-------------|
| `vector_store` | `Chroma` | LangChain Chroma vector store with `_collection` attribute |
| `chunks` | `list[str]` | List of chunk IDs to retrieve |

**Returns:** Formatted context string with source and content for each chunk

**Output Format:**
```
Source: {'doc_id': 'doc_1', 'chunk_id': 'chunk_1', 'source': 'policy.pdf'}
Content: Employees are entitled to 20 vacation days per year.

Source: {'doc_id': 'doc_2', 'chunk_id': 'chunk_2', 'source': 'handbook.pdf'}
Content: Remote work is allowed up to 3 days per week.
```

**Example:**
```python
chunk_ids = ['doc_1_chunk_1', 'doc_2_chunk_1']
context = retrieve_chunks(vector_store, chunk_ids)
```

## Edge Cases Handled

### policy_filter.py

| Edge Case | Behavior |
|-----------|----------|
| Empty `allowed_doc_ids` | Returns empty list, logs info |
| No matching documents | Returns empty list |
| Empty `candidates` | Returns empty list |
| `top_k` > available results | Returns all available |

### final_retriever.py

| Edge Case | Behavior |
|-----------|----------|
| Empty `chunks` list | Returns `""`, logs info |
| `vector_store` is `None` | Returns `""`, logs error |
| `vector_store` has no `_collection` | Returns `""`, logs error |
| Chunk not found in collection | Skips chunk, logs warning |
| Chunk has no metadata | Includes content with empty source |
| All fetches failed | Returns `""`, logs warning |

## Logging

Both modules use Python's `logging` module. To enable debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Log Levels Used:**

| Level | When |
|-------|------|
| `DEBUG` | Successful operations, counts |
| `INFO` | Empty inputs, fewer results than requested |
| `WARNING` | Missing chunks, all fetches failed |
| `ERROR` | None inputs, missing attributes, exceptions |

## Input/Output Formats

### Candidate Format (Input from Full Retrieval)

```python
{
    'doc_id': str,      # Document ID
    'chunk_id': str,    # Chunk ID (unique identifier in Chroma)
    'score': str,       # Similarity score (string, will be converted to float)
}
```

### Allowed Doc IDs Format (Input from SpiceDB)

```python
['doc_1', 'doc_2', 'doc_3']  # List of document IDs user can access
```

### Context String Format (Output)

```
Source: {metadata_dict}
Content: {document_text}

Source: {metadata_dict}
Content: {document_text}
```

## Integration with EAKAP

This module fits into the EAKAP RAG pipeline:

```
User Query
    │
    ▼
Embedding Generation
    │
    ▼
Full Retrieval (Vector Search)  ──────┐
    │                                  │
    │                                  ▼
    │                           SpiceDB (ACL Check)
    │                                  │
    └──────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Final Retrieval     │  ◄── THIS MODULE
        │   (policy_filter +    │
        │    final_retriever)   │
        └───────────────────────┘
                    │
                    ▼
            Context String
                    │
                    ▼
            LLM Response Generation
                    │
                    ▼
            User Response
```

## License

This project is part of the EAKAP internship project.
