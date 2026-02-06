"""
Unit tests for the EmbeddingsProvider class.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.shared.indexing.embeddings_provider import EmbeddingsProvider


class TestCreateProviderDispatch:
    """Tests for create_provider dispatching to correct provider types"""

    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    def test_create_provider_returns_huggingface_embeddings(self, mock_hf_class):
        """Should create and return HuggingFace embeddings provider."""
        mock_instance = MagicMock()
        mock_hf_class.return_value = mock_instance
        
        result = EmbeddingsProvider.create_provider("huggingface")
        
        assert result == mock_instance
        mock_hf_class.assert_called_once()

    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_create_provider_returns_google_embeddings(self, mock_google_class):
        """Should create and return Google embeddings provider."""
        mock_instance = MagicMock()
        mock_google_class.return_value = mock_instance
        
        result = EmbeddingsProvider.create_provider(
            "google",
            google_api_key="test_key"
        )
        
        assert result == mock_instance
        mock_google_class.assert_called_once_with(
            model="models/embedding-001",
            google_api_key="test_key"
        )

    @patch('langchain_openai.OpenAIEmbeddings')
    def test_create_provider_returns_openai_embeddings(self, mock_openai_class):
        """Should create and return OpenAI embeddings provider."""
        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        
        result = EmbeddingsProvider.create_provider(
            "openai",
            openai_api_key="test_key"
        )
        
        assert result == mock_instance
        mock_openai_class.assert_called_once_with(
            model="text-embedding-ada-002",
            openai_api_key="test_key"
        )


class TestCreateProviderValidation:
    """Tests for create_provider validation"""

    def test_create_provider_raises_value_error_for_unsupported_type(self):
        """Should raise ValueError for unsupported provider type."""
        with pytest.raises(ValueError, match="Unsupported provider type: invalid"):
            EmbeddingsProvider.create_provider("invalid")

    def test_create_provider_raises_value_error_when_google_api_key_missing(self):
        """Should raise ValueError if google_api_key is not provided."""
        with pytest.raises(ValueError, match="google_api_key is required"):
            EmbeddingsProvider.create_provider("google")

    def test_create_provider_raises_value_error_when_openai_api_key_missing(self):
        """Should raise ValueError if openai_api_key is not provided."""
        with pytest.raises(ValueError, match="openai_api_key is required"):
            EmbeddingsProvider.create_provider("openai")


class TestCreateProviderOptions:
    """Tests for create_provider configuration options"""

    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    def test_create_provider_accepts_lowercase_provider_type(self, mock_hf_class):
        """Should accept case-insensitive provider type (already lowercase)."""
        mock_instance = MagicMock()
        mock_hf_class.return_value = mock_instance
        
        # Test uppercase
        result = EmbeddingsProvider.create_provider("HUGGINGFACE")
        assert result == mock_instance
        
        # Test mixed case
        mock_hf_class.reset_mock()
        result = EmbeddingsProvider.create_provider("HuggingFace")
        assert result == mock_instance

    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    def test_create_provider_uses_default_model_for_huggingface(self, mock_hf_class):
        """Should use default model name for HuggingFace if not specified."""
        mock_instance = MagicMock()
        mock_hf_class.return_value = mock_instance
        
        EmbeddingsProvider.create_provider("huggingface")
        
        mock_hf_class.assert_called_once_with(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

    @patch('langchain_huggingface.HuggingFaceEmbeddings')
    def test_create_provider_accepts_custom_model_for_huggingface(self, mock_hf_class):
        """Should use custom model name for HuggingFace if provided."""
        mock_instance = MagicMock()
        mock_hf_class.return_value = mock_instance
        
        EmbeddingsProvider.create_provider(
            "huggingface",
            model_name="custom-model"
        )
        
        mock_hf_class.assert_called_once_with(model_name="custom-model")


class TestCreateProviderImportError:
    """Tests for create_provider ImportError handling"""

    def test_create_provider_raises_import_error_when_huggingface_not_installed(self):
        """Should raise ImportError if langchain-huggingface is not installed."""
        import sys
        
        # Remove the module from sys.modules temporarily
        langchain_hf = sys.modules.pop('langchain_huggingface', None)
        
        try:
            # Mock the import to fail
            sys.modules['langchain_huggingface'] = None
            
            with pytest.raises(ImportError, match="langchain-huggingface package is required"):
                EmbeddingsProvider.create_provider("huggingface")
        finally:
            # Restore the module
            if langchain_hf is not None:
                sys.modules['langchain_huggingface'] = langchain_hf
            else:
                sys.modules.pop('langchain_huggingface', None)

    def test_create_provider_raises_import_error_when_google_not_installed(self):
        """Should raise ImportError if langchain-google-genai is not installed."""
        import sys
        
        # Remove the module from sys.modules temporarily
        langchain_google = sys.modules.pop('langchain_google_genai', None)
        
        try:
            # Mock the import to fail
            sys.modules['langchain_google_genai'] = None
            
            with pytest.raises(ImportError, match="langchain-google-genai package is required"):
                EmbeddingsProvider.create_provider("google", google_api_key="test")
        finally:
            # Restore the module
            if langchain_google is not None:
                sys.modules['langchain_google_genai'] = langchain_google
            else:
                sys.modules.pop('langchain_google_genai', None)
