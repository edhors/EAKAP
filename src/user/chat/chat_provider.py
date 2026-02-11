"""
Factory class for creating different chat model provider instances.
Supports multiple providers: Google, OpenAI, Anthropic, Mistral, HuggingFace, and Zhipu AI.
"""

from langchain_core.language_models.chat_models import BaseChatModel


class ChatProvider:
    """Factory class to create different chat model provider instances."""
    
    @staticmethod
    def create_provider(provider_type: str, **config) -> BaseChatModel:
        """
        Factory method that returns a LangChain chat model instance.
        
        Args:
            provider_type: Type of provider ("google", "openai", "anthropic", "mistral", "huggingface", "zhipuai")
            **config: Configuration parameters for the provider:
                - For Google: model (default: "gemini-2.5-flash-lite"), temperature (default: 0.7), google_api_key (required)
                - For OpenAI: model (default: "gpt-3.5-turbo"), temperature (default: 0.7), openai_api_key (required)
                - For Anthropic: model (default: "claude-3-sonnet-20240229"), temperature (default: 0.7), anthropic_api_key (required)
                - For Mistral: model (default: "mistral-small-latest"), temperature (default: 0.7), mistral_api_key (required)
                - For HuggingFace: repo_id (required), task (default: "text-generation"), 
                  huggingfacehub_api_token (optional), max_new_tokens (default: 512)
                - For Zhipu AI: model (default: "glm-4-flash"), temperature (default: 0.5), zhipuai_api_key (required)
        
        Returns:
            BaseChatModel: A LangChain chat model instance
        
        Raises:
            ValueError: If provider_type is unsupported or required config is missing
            ImportError: If the required package for the provider is not installed
        """
        provider_type = provider_type.lower()
        
        if provider_type == "google":
            return ChatProvider._create_google(**config)
        elif provider_type == "openai":
            return ChatProvider._create_openai(**config)
        elif provider_type == "anthropic":
            return ChatProvider._create_anthropic(**config)
        elif provider_type == "mistral":
            return ChatProvider._create_mistral(**config)
        elif provider_type == "huggingface":
            return ChatProvider._create_huggingface(**config)
        elif provider_type == "zhipuai":
            return ChatProvider._create_zhipuai(**config)
        else:
            supported = ["google", "openai", "anthropic", "mistral", "huggingface", "zhipuai"]
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types are: {', '.join(supported)}"
            )
    
    @staticmethod
    def _create_google(**config) -> BaseChatModel:
        """Create Google chat model provider."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai package is required for Google chat models. "
                "Install it with: pip install langchain-google-genai"
            )
        
        google_api_key = config.get("google_api_key")
        if not google_api_key:
            raise ValueError(
                "google_api_key is required for Google chat models. "
                "Provide it in the config or set GOOGLE_API_KEY environment variable."
            )
        
        model = config.get("model", "gemini-2.5-flash-lite")
        temperature = config.get("temperature", 0.7)
        
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=google_api_key
        )
    
    @staticmethod
    def _create_openai(**config) -> BaseChatModel:
        """Create OpenAI chat model provider."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai package is required for OpenAI chat models. "
                "Install it with: pip install langchain-openai"
            )
        
        openai_api_key = config.get("openai_api_key")
        if not openai_api_key:
            raise ValueError(
                "openai_api_key is required for OpenAI chat models. "
                "Provide it in the config or set OPENAI_API_KEY environment variable."
            )
        
        model = config.get("model", "gpt-3.5-turbo")
        temperature = config.get("temperature", 0.7)
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=openai_api_key
        )
    
    @staticmethod
    def _create_anthropic(**config) -> BaseChatModel:
        """Create Anthropic chat model provider."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic package is required for Anthropic chat models. "
                "Install it with: pip install langchain-anthropic"
            )
        
        anthropic_api_key = config.get("anthropic_api_key")
        if not anthropic_api_key:
            raise ValueError(
                "anthropic_api_key is required for Anthropic chat models. "
                "Provide it in the config or set ANTHROPIC_API_KEY environment variable."
            )
        
        model = config.get("model", "claude-3-sonnet-20240229")
        temperature = config.get("temperature", 0.7)
        
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=anthropic_api_key
        )
    
    @staticmethod
    def _create_mistral(**config) -> BaseChatModel:
        """Create Mistral chat model provider."""
        try:
            from langchain_mistralai import ChatMistralAI
        except ImportError:
            raise ImportError(
                "langchain-mistralai package is required for Mistral chat models. "
                "Install it with: pip install langchain-mistralai"
            )
        
        mistral_api_key = config.get("mistral_api_key")
        if not mistral_api_key:
            raise ValueError(
                "mistral_api_key is required for Mistral chat models. "
                "Provide it in the config or set MISTRAL_API_KEY environment variable."
            )
        
        model = config.get("model", "mistral-small-latest")
        temperature = config.get("temperature", 0.7)
        
        return ChatMistralAI(
            model=model,
            temperature=temperature,
            mistral_api_key=mistral_api_key
        )
    
    @staticmethod
    def _create_huggingface(**config) -> BaseChatModel:
        """Create HuggingFace chat model provider."""
        try:
            from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
        except ImportError:
            raise ImportError(
                "langchain-huggingface package is required for HuggingFace chat models. "
                "Install it with: pip install langchain-huggingface"
            )
        
        repo_id = config.get("repo_id")
        if not repo_id:
            raise ValueError(
                "repo_id is required for HuggingFace chat models. "
                "Provide a model repository ID (e.g., 'microsoft/Phi-3-mini-4k-instruct')."
            )
        
        task = config.get("task", "text-generation")
        max_new_tokens = config.get("max_new_tokens", 512)
        huggingfacehub_api_token = config.get("huggingfacehub_api_token")
        
        # Build HuggingFaceEndpoint kwargs
        endpoint_kwargs = {
            "repo_id": repo_id,
            "task": task,
            "max_new_tokens": max_new_tokens,
        }
        
        # Add API token if provided
        if huggingfacehub_api_token:
            endpoint_kwargs["huggingfacehub_api_token"] = huggingfacehub_api_token
        
        # Create the underlying LLM endpoint
        llm = HuggingFaceEndpoint(**endpoint_kwargs)
        
        # Wrap it in ChatHuggingFace
        return ChatHuggingFace(llm=llm)
    
    @staticmethod
    def _create_zhipuai(**config) -> BaseChatModel:
        """Create Zhipu AI chat model provider."""
        try:
            from langchain_community.chat_models import ChatZhipuAI
        except ImportError:
            raise ImportError(
                "langchain-community package is required for Zhipu AI chat models. "
                "Install it with: pip install langchain-community"
            )
        
        zhipuai_api_key = config.get("zhipuai_api_key")
        if not zhipuai_api_key:
            raise ValueError(
                "zhipuai_api_key is required for Zhipu AI chat models. "
                "Provide it in the config or set ZHIPUAI_API_KEY environment variable."
            )
        
        model = config.get("model", "glm-4-flash")
        temperature = config.get("temperature", 0.5)
        
        return ChatZhipuAI(
            model=model,
            temperature=temperature,
            api_key=zhipuai_api_key
        )
