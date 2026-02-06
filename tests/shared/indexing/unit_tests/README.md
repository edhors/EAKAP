# Indexing Module Unit Tests

Comprehensive unit test suite for the `src/shared/indexing` module using pytest.

## Overview

This test suite provides unit tests for all components of the indexing module:
- **Embeddings**: Wrapper for LangChain embeddings providers
- **EmbeddingsProvider**: Factory for creating different embedding providers
- **TextProcessor**: Document loading and text chunking
- **Indexer**: Orchestration of the indexing pipeline

## Test Structure

```
tests/shared/indexing/unit_tests/
├── __init__.py                      # Package marker
├── conftest.py                      # Shared pytest fixtures
├── test_embeddings.py              # Tests for Embeddings class (11 tests)
├── test_embeddings_provider.py     # Tests for EmbeddingsProvider (12 tests)
├── test_text_processor.py          # Tests for TextProcessor (19 tests)
├── test_indexer.py                 # Tests for Indexer (14 tests)
└── README.md                       # This file
```

## Test Statistics

- **Total Test Files**: 4
- **Total Test Methods**: 63

### Breakdown by Module

| Module | Tests | Focus Areas |
|--------|-------|-------------|
| `test_embeddings.py` | 11 | Constructor validation, embed_query, embed_chunks, error handling |
| `test_embeddings_provider.py` | 12 | Provider dispatch, API key validation, default configs, ImportError handling |
| `test_text_processor.py` | 19 | Constructor validation, split_text, split_documents, load_file, load_directory |
| `test_indexer.py` | 14 | Constructor validation, index method, chunk_id assignment, metadata handling |

## Running the Tests

### Run all unit tests
```bash
pytest tests/shared/indexing/unit_tests/ -v
```

### Run specific test file
```bash
pytest tests/shared/indexing/unit_tests/test_embeddings.py -v
```

### Run specific test class
```bash
pytest tests/shared/indexing/unit_tests/test_embeddings.py::TestEmbedQuery -v
```

### Run specific test method
```bash
pytest tests/shared/indexing/unit_tests/test_embeddings.py::TestEmbedQuery::test_embed_query_returns_list_of_floats -v
```

### Run with coverage
```bash
pytest tests/shared/indexing/unit_tests/ --cov=src/shared/indexing --cov-report=html
```

## Test Coverage Areas

### 1. Embeddings (`test_embeddings.py`)

**Constructor Tests (2):**
- Valid LangChain embeddings provider acceptance
- TypeError for non-embeddings provider

**embed_query Tests (5):**
- Returns list of floats for valid query
- ValueError for empty/None/non-string text
- RuntimeError when provider fails

**embed_chunks Tests (5):**
- Returns list of embeddings for valid chunks
- ValueError for empty list, non-list, invalid items
- RuntimeError when provider fails

### 2. EmbeddingsProvider (`test_embeddings_provider.py`)

**Provider Dispatch Tests (3):**
- HuggingFace, Google, OpenAI

**Validation Tests (3):**
- Unsupported provider type
- Missing API keys for Google, OpenAI

**Configuration Tests (3):**
- Case-insensitive provider type
- Default model for HuggingFace
- Custom model for HuggingFace

**ImportError Tests (2):**
- HuggingFace package not installed
- Google package not installed

### 3. TextProcessor (`test_text_processor.py`)

**Constructor Tests (6):**
- Valid parameters acceptance
- ValueError for invalid chunk_size, chunk_overlap, splitter_type

**split_text Tests (4):**
- Returns chunks for valid text
- ValueError for empty/None text
- TypeError for non-string

**split_documents Tests (4):**
- Returns chunked documents with metadata
- ValueError for empty/None list
- TypeError for non-list

**load_file Tests (4):**
- FileNotFoundError for missing file
- ValueError for unknown extension, unsupported type
- Success for text file

**load_directory Tests (3):**
- FileNotFoundError for missing directory
- ValueError for non-directory path
- Success with mocked loader

**load_and_split Tests (3):**
- Delegates to load_file then split
- Delegates to load_directory then split
- ValueError for invalid source_type

### 4. Indexer (`test_indexer.py`)

**Constructor Tests (5):**
- Valid components acceptance
- TypeError for invalid embeddings, text_processor, vector_store
- ValueError for vector_store lacking add_documents

**index Method Tests (9):**
- Calls text_processor.split then vector_store.add_documents
- Assigns chunk_id in format `{doc_id}_chunk_{index}`
- Uses document_id fallback when doc_id missing
- Uses 'default' when no ID in metadata
- ValueError for empty/None documents
- TypeError for non-list, non-Document items
- No shared metadata references across chunks
- RuntimeError when split_documents or add_documents fails

## Key Testing Strategies

### Mocking Strategy

The test suite uses extensive mocking to isolate units:

1. **LangChain Embeddings**: Mocked to pass `isinstance` checks and return predictable vectors
2. **VectorStore**: Mocked to verify add_documents calls without actual storage
3. **File System**: Uses pytest's `tmp_path` for safe file operations
4. **External Packages**: Mocked imports to test ImportError handling

### Fixtures (conftest.py)

- `mock_langchain_embeddings`: Mock LangChain embeddings provider
- `mock_vector_store`: Mock VectorStore with add_documents method
- `sample_documents_with_doc_id`: Documents with 'doc_id' in metadata
- `sample_documents_with_document_id`: Documents with 'document_id' (backward compatibility)
- `sample_documents_no_id`: Documents without ID metadata

## Notes

- All tests use mocks for external dependencies (no real API calls)
- Tests focus on contracts, validation, and control flow
- Tests verify error messages match expected patterns
- Tests ensure metadata handling and chunk_id assignment work correctly
- Tests verify no shared references across document chunks

## Future Enhancements

Potential additions to the test suite:

1. **Integration Tests**: Tests with real vector stores (Chroma, InMemoryVectorStore)
2. **Performance Tests**: Tests for large document processing
3. **Parameterized Tests**: More test variations using pytest.mark.parametrize
4. **Property-Based Tests**: Using hypothesis for edge case discovery
5. **End-to-End Tests**: Complete indexing workflows with real files
