"""
Unit tests for the TextProcessor class.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from langchain_core.documents import Document
from src.shared.indexing.text_processor import TextProcessor


class TestTextProcessorInit:
    """Tests for TextProcessor.__init__"""

    def test_init_accepts_valid_params(self):
        """Should successfully initialize with valid parameters."""
        processor = TextProcessor(chunk_size=1000, chunk_overlap=200)
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200
        assert processor.splitter_type == "recursive"

    def test_init_raises_value_error_for_chunk_size_zero(self):
        """Should raise ValueError if chunk_size is 0."""
        with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
            TextProcessor(chunk_size=0)

    def test_init_raises_value_error_for_chunk_size_negative(self):
        """Should raise ValueError if chunk_size is negative."""
        with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
            TextProcessor(chunk_size=-100)

    def test_init_raises_value_error_for_negative_chunk_overlap(self):
        """Should raise ValueError if chunk_overlap is negative."""
        with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
            TextProcessor(chunk_size=1000, chunk_overlap=-50)

    def test_init_raises_value_error_when_chunk_overlap_ge_chunk_size(self):
        """Should raise ValueError if chunk_overlap >= chunk_size."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            TextProcessor(chunk_size=1000, chunk_overlap=1000)
        
        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            TextProcessor(chunk_size=1000, chunk_overlap=1500)

    def test_init_raises_value_error_for_unsupported_splitter_type(self):
        """Should raise ValueError for unsupported splitter_type."""
        with pytest.raises(ValueError, match="Unsupported splitter_type"):
            TextProcessor(splitter_type="unsupported")


class TestSplitText:
    """Tests for TextProcessor.split_text"""

    def test_split_text_returns_chunks(self):
        """Should return list of text chunks."""
        processor = TextProcessor(chunk_size=50, chunk_overlap=10)
        text = "This is a long text. " * 10  # Create text longer than chunk_size
        
        chunks = processor.split_text(text)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_text_raises_value_error_for_empty_string(self):
        """Should raise ValueError for empty string."""
        processor = TextProcessor()
        with pytest.raises(ValueError, match="Text cannot be empty or None"):
            processor.split_text("")

    def test_split_text_raises_value_error_for_none(self):
        """Should raise ValueError for None."""
        processor = TextProcessor()
        with pytest.raises(ValueError, match="Text cannot be empty or None"):
            processor.split_text(None)

    def test_split_text_raises_type_error_for_non_string(self):
        """Should raise TypeError for non-string input."""
        processor = TextProcessor()
        with pytest.raises(TypeError, match="Text must be a string"):
            processor.split_text(123)


class TestSplitDocuments:
    """Tests for TextProcessor.split_documents"""

    def test_split_documents_returns_chunked_documents_with_metadata(self, sample_documents_with_doc_id):
        """Should return chunked documents preserving metadata."""
        processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        
        result = processor.split_documents(sample_documents_with_doc_id)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(doc, Document) for doc in result)
        # Check metadata is preserved
        assert all(doc.metadata.get("doc_id") in ["doc_1", "doc_2"] for doc in result)

    def test_split_documents_raises_value_error_for_empty_list(self):
        """Should raise ValueError for empty list."""
        processor = TextProcessor()
        with pytest.raises(ValueError, match="Documents list cannot be empty or None"):
            processor.split_documents([])

    def test_split_documents_raises_value_error_for_none(self):
        """Should raise ValueError for None."""
        processor = TextProcessor()
        with pytest.raises(ValueError, match="Documents list cannot be empty or None"):
            processor.split_documents(None)

    def test_split_documents_raises_type_error_for_non_list(self):
        """Should raise TypeError for non-list input."""
        processor = TextProcessor()
        with pytest.raises(TypeError, match="Documents must be a list"):
            processor.split_documents("not a list")


class TestLoadFile:
    """Tests for TextProcessor.load_file"""

    def test_load_file_raises_file_not_found_for_missing_path(self):
        """Should raise FileNotFoundError if file doesn't exist."""
        processor = TextProcessor()
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.load_file("/nonexistent/path/file.pdf")

    def test_load_file_raises_value_error_for_unknown_extension_without_file_type(self, tmp_path):
        """Should raise ValueError if file extension is unknown and file_type not specified."""
        processor = TextProcessor()
        test_file = tmp_path / "test.unknown"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="Cannot auto-detect file type"):
            processor.load_file(test_file)

    def test_load_file_raises_value_error_for_unsupported_file_type(self, tmp_path):
        """Should raise ValueError for unsupported file_type."""
        processor = TextProcessor()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.load_file(test_file, file_type="unsupported")

    def test_load_file_returns_documents_for_text_file(self, tmp_path):
        """Should successfully load a text file and return documents."""
        processor = TextProcessor()
        test_file = tmp_path / "test.txt"
        test_content = "This is test content for the text file."
        test_file.write_text(test_content)
        
        documents = processor.load_file(test_file, file_type="text")
        
        assert isinstance(documents, list)
        assert len(documents) > 0
        assert all(isinstance(doc, Document) for doc in documents)


class TestLoadDirectory:
    """Tests for TextProcessor.load_directory"""

    def test_load_directory_raises_file_not_found_for_missing_dir(self):
        """Should raise FileNotFoundError if directory doesn't exist."""
        processor = TextProcessor()
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            processor.load_directory("/nonexistent/directory")

    def test_load_directory_raises_value_error_when_path_not_directory(self, tmp_path):
        """Should raise ValueError if path is not a directory."""
        processor = TextProcessor()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            processor.load_directory(test_file)

    @patch('langchain_community.document_loaders.DirectoryLoader')
    @patch('langchain_community.document_loaders.TextLoader')
    def test_load_directory_returns_documents_with_mocked_loader(
        self, mock_text_loader_class, mock_dir_loader_class, tmp_path
    ):
        """Should successfully load directory with mocked DirectoryLoader."""
        processor = TextProcessor()
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        # Create a test file to match
        (test_dir / "test.txt").write_text("content")
        
        # Mock the DirectoryLoader
        mock_loader_instance = MagicMock()
        mock_loader_instance.load.return_value = [
            Document(page_content="Loaded content", metadata={"source": "test.txt"})
        ]
        mock_dir_loader_class.return_value = mock_loader_instance
        
        documents = processor.load_directory(test_dir, glob_pattern="*.txt", loader_type="text")
        
        assert isinstance(documents, list)
        assert len(documents) > 0
        mock_loader_instance.load.assert_called_once()


class TestLoadAndSplit:
    """Tests for TextProcessor.load_and_split"""

    def test_load_and_split_delegates_to_load_file_then_split(self, tmp_path):
        """Should delegate to load_file and then split_documents."""
        processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is test content. " * 10)
        
        with patch.object(processor, 'load_file', wraps=processor.load_file) as mock_load:
            with patch.object(processor, 'split_documents', wraps=processor.split_documents) as mock_split:
                result = processor.load_and_split(test_file, source_type="file", file_type="text")
                
                mock_load.assert_called_once()
                mock_split.assert_called_once()
                assert isinstance(result, list)

    def test_load_and_split_delegates_to_load_directory_then_split(self, tmp_path):
        """Should delegate to load_directory and then split_documents."""
        processor = TextProcessor(chunk_size=20, chunk_overlap=5)
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("Content " * 10)
        
        with patch.object(processor, 'load_directory') as mock_load_dir:
            mock_load_dir.return_value = [
                Document(page_content="Test content " * 10, metadata={})
            ]
            with patch.object(processor, 'split_documents', wraps=processor.split_documents) as mock_split:
                result = processor.load_and_split(
                    test_dir,
                    source_type="directory",
                    glob_pattern="*.txt",
                    loader_type="text"
                )
                
                mock_load_dir.assert_called_once()
                mock_split.assert_called_once()
                assert isinstance(result, list)

    def test_load_and_split_raises_value_error_for_invalid_source_type(self, tmp_path):
        """Should raise ValueError for invalid source_type."""
        processor = TextProcessor()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="Invalid source_type"):
            processor.load_and_split(test_file, source_type="invalid")
