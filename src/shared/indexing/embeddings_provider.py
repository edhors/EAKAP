"""
Factory class for creating different embedding provider instances.
Supports multiple providers: HuggingFace, Google, OpenAI, Anthropic, and Mistral.
"""

from langchain_core.embeddings import Embeddings


class EmbeddingsProvider:
    """Factory class to create different embedding provider instances."""
    
    @staticmethod
    def create_provider(provider_type: str, **config) -> Embeddings:
        """
        Factory method that returns a LangChain embeddings instance.
        
        Args:
            provider_type: Type of provider ("huggingface", "google", "openai", "anthropic", "mistral")
            **config: Configuration parameters for the provider:
                - For HuggingFace: model_name (default: "sentence-transformers/all-mpnet-base-v2")
                - For Google: model (default: "models/embedding-001"), google_api_key (required)
                - For OpenAI: model (default: "text-embedding-ada-002"), openai_api_key (required)
                - For Anthropic: model (optional), anthropic_api_key (required)
                - For Mistral: model (optional), mistral_api_key (required)
        
        Returns:
            Embeddings: A LangChain embeddings instance
        
        Raises:
            ValueError: If provider_type is unsupported or required config is missing
            ImportError: If the required package for the provider is not installed
        """
        provider_type = provider_type.lower()
        
        if provider_type == "huggingface":
            return EmbeddingsProvider._create_huggingface(**config)
        elif provider_type == "google":
            return EmbeddingsProvider._create_google(**config)
        elif provider_type == "openai":
            return EmbeddingsProvider._create_openai(**config)
        elif provider_type == "anthropic":
            return EmbeddingsProvider._create_anthropic(**config)
        elif provider_type == "mistral":
            return EmbeddingsProvider._create_mistral(**config)
        else:
            supported = ["huggingface", "google", "openai", "anthropic", "mistral"]
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types are: {', '.join(supported)}"
            )
    
    @staticmethod
    def _create_huggingface(**config) -> Embeddings:
        """Create HuggingFace embeddings provider."""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-huggingface package is required for HuggingFace embeddings. "
                "Install it with: pip install langchain-huggingface"
            )
        
        model_name = config.get("model_name", "sentence-transformers/all-mpnet-base-v2")
        return HuggingFaceEmbeddings(model_name=model_name)
    
    @staticmethod
    def _create_google(**config) -> Embeddings:
        """Create Google embeddings provider."""
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-google-genai package is required for Google embeddings. "
                "Install it with: pip install langchain-google-genai"
            )
        
        google_api_key = config.get("google_api_key")
        if not google_api_key:
            raise ValueError(
                "google_api_key is required for Google embeddings. "
                "Provide it in the config or set GOOGLE_API_KEY environment variable."
            )
        
        model = config.get("model", "models/embedding-001")
        return GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=google_api_key
        )
    
    @staticmethod
    def _create_openai(**config) -> Embeddings:
        """Create OpenAI embeddings provider."""
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-openai package is required for OpenAI embeddings. "
                "Install it with: pip install langchain-openai"
            )
        
        openai_api_key = config.get("openai_api_key")
        if not openai_api_key:
            raise ValueError(
                "openai_api_key is required for OpenAI embeddings. "
                "Provide it in the config or set OPENAI_API_KEY environment variable."
            )
        
        model = config.get("model", "text-embedding-ada-002")
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=openai_api_key
        )
    
    @staticmethod
    def _create_anthropic(**config) -> Embeddings:
        """Create Anthropic embeddings provider."""
        try:
            from langchain_anthropic import AnthropicEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-anthropic package is required for Anthropic embeddings. "
                "Install it with: pip install langchain-anthropic"
            )
        
        anthropic_api_key = config.get("anthropic_api_key")
        if not anthropic_api_key:
            raise ValueError(
                "anthropic_api_key is required for Anthropic embeddings. "
                "Provide it in the config or set ANTHROPIC_API_KEY environment variable."
            )
        
        # Anthropic embeddings may not have a model parameter in the same way
        # Pass model if provided, otherwise use default
        model = config.get("model")
        if model:
            return AnthropicEmbeddings(
                model=model,
                anthropic_api_key=anthropic_api_key
            )
        else:
            return AnthropicEmbeddings(anthropic_api_key=anthropic_api_key)
    
    @staticmethod
    def _create_mistral(**config) -> Embeddings:
        """Create Mistral embeddings provider."""
        try:
            from langchain_mistralai import MistralAIEmbeddings
        except ImportError:
            raise ImportError(
                "langchain-mistralai package is required for Mistral embeddings. "
                "Install it with: pip install langchain-mistralai"
            )
        
        mistral_api_key = config.get("mistral_api_key")
        if not mistral_api_key:
            raise ValueError(
                "mistral_api_key is required for Mistral embeddings. "
                "Provide it in the config or set MISTRAL_API_KEY environment variable."
            )
        
        # Mistral embeddings may have a model parameter
        model = config.get("model")
        if model:
            return MistralAIEmbeddings(
                model=model,
                mistral_api_key=mistral_api_key
            )
        else:
            return MistralAIEmbeddings(mistral_api_key=mistral_api_key)