import os
import logging
from typing import Any, Optional, Dict
from pydantic import SecretStr

# Import all LangChain providers with error handling
try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
except ImportError:
    ChatHuggingFace = None
    HuggingFaceEndpoint = None

try:
    from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
except ImportError:
    AzureAIChatCompletionsModel = None

try:
    from langchain_cerebras import ChatCerebras
except ImportError:
    ChatCerebras = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_aws import ChatBedrock
except ImportError:
    ChatBedrock = None

from .config import settings
from .proxy import update_proxy_config, delete_proxy_config


def configure_llm(
    llm_provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.0,
    config_file_content: Optional[Dict[str, Any]] = None,
    proxy_required: bool = False
) -> Any:
    """
    Configure and return the LLM model based on the provider.
    
    Args:
        llm_provider: The LLM provider to use
        model_name: The model name to use
        api_key: API key for the provider (if required)
        base_url: Base URL for the provider (if required)
        temperature: Temperature setting for the model (default: 0.0)
        config_file_content: Configuration file content (required for AWS)
        proxy_required: Whether to configure proxy settings
        
    Returns:
        Configured LLM model instance
        
    Raises:
        ValueError: If unsupported provider or missing required parameters
    """
    
    logger = settings.logger
    provider = llm_provider.lower()
    
    logger.info(f"Configuring LLM model: {provider}")
    
    # Set proxy if required
    if proxy_required:
        update_proxy_config()
        logger.debug("Proxy configuration enabled")
    
    try:
        model = None
        
        if provider == "ollama":
            if ChatOllama is None:
                raise ValueError("ChatOllama is not available. Please install langchain-ollama package.")
            if not model_name:
                raise ValueError("Model name is required for Ollama")
            
            model = ChatOllama(
                model=model_name,
                temperature=temperature
            )
            
        elif provider == "openai":
            if ChatOpenAI is None:
                raise ValueError("ChatOpenAI is not available. Please install langchain-openai package.")
            if not api_key:
                raise ValueError("API key is required for OpenAI")
            if not model_name:
                raise ValueError("Model name is required for OpenAI")
            
            kwargs = {
                "model": model_name,
                "api_key": SecretStr(api_key),
                "temperature": temperature
            }
            if base_url:
                kwargs["base_url"] = base_url
                
            model = ChatOpenAI(**kwargs)
            
        elif provider == "groq":
            if ChatGroq is None:
                raise ValueError("ChatGroq is not available. Please install langchain-groq package.")
            if not api_key:
                raise ValueError("API key is required for Groq")
            if not model_name:
                raise ValueError("Model name is required for Groq")
            
            model = ChatGroq(
                model=model_name,
                api_key=SecretStr(api_key),
                temperature=temperature
            )
            
        elif provider == "azure":
            if AzureAIChatCompletionsModel is None:
                raise ValueError("AzureAIChatCompletionsModel is not available. Please install langchain-azure-ai package.")
            if not api_key:
                raise ValueError("API key is required for Azure AI")
            
            os.environ["AZURE_INFERENCE_CREDENTIAL"] = api_key
            
            model = AzureAIChatCompletionsModel(
                model=model_name,
                endpoint=base_url or "https://models.github.ai/inference"
            )
            
        elif provider == "huggingface":
            if ChatHuggingFace is None or HuggingFaceEndpoint is None:
                raise ValueError("ChatHuggingFace is not available. Please install langchain-huggingface package.")
            if not model_name:
                raise ValueError("Model name is required for HuggingFace")
            if not api_key:
                raise ValueError("API key is required for HuggingFace")
            
            llm = HuggingFaceEndpoint(
                 huggingfacehub_api_token=SecretStr(api_key),
                 repo_id=model_name,
                 task="text-generation"
            ) # type: ignore
            model = ChatHuggingFace(llm=llm, model_id=model_name)

        elif provider == "cerebras":
            if ChatCerebras is None:
                raise ValueError("ChatCerebras is not available. Please install langchain-cerebras package.")
            if not api_key:
                raise ValueError("API key is required for Cerebras")
            if not model_name:
                raise ValueError("Model name is required for Cerebras")
            
            model = ChatCerebras(
                model=model_name,
                api_key=SecretStr(api_key),
                temperature=temperature
            )
            
        elif provider == "openrouter":
            if ChatOpenAI is None:
                raise ValueError("ChatOpenAI is not available. Please install langchain-openai package.")
            if not api_key:
                raise ValueError("API key is required for OpenRouter")
            if not model_name:
                raise ValueError("Model name is required for OpenRouter")
            
            model = ChatOpenAI(
                model=model_name,
                api_key=SecretStr(api_key),
                temperature=temperature,
                base_url="https://openrouter.ai/api/v1"
            )
            
        elif provider == "anthropic":
            if ChatAnthropic is None:
                raise ValueError("ChatAnthropic is not available. Please install langchain-anthropic package.")
            if not api_key:
                raise ValueError("API key is required for Anthropic")
            if not model_name:
                raise ValueError("Model name is required for Anthropic")
            
            model = ChatAnthropic(
                model=model_name, # type: ignore
                api_key=SecretStr(api_key),
                temperature=temperature
            )
            
        elif provider == "aws":
            # Skip AWS due to parameter compatibility issues
            raise ValueError("AWS provider is currently not supported due to parameter compatibility issues")
            
        elif provider == "google":
            # Skip Google due to parameter compatibility issues
            raise ValueError("Google provider is currently not supported due to parameter compatibility issues")

        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        
        if model is None:
            raise ValueError(f"Failed to create model for provider: {llm_provider}")
            
        logger.info(f"LLM model configured successfully: {type(model).__name__}")
        return model
        
    except Exception as e:
        logger.error(f"Error configuring LLM: {str(e)}")
        raise
    finally:
        # Always unset proxy after getting LLM instance
        if proxy_required:
            delete_proxy_config()
            logger.debug("Proxy configuration disabled")


    """Get list of available LLM providers based on installed packages."""
    providers = []
    
    if ChatOllama is not None:
        providers.append("ollama")
    if ChatOpenAI is not None:
        providers.extend(["openai", "openrouter"])
    if ChatGroq is not None:
        providers.append("groq")
    if AzureAIChatCompletionsModel is not None:
        providers.append("azure")
    if ChatCerebras is not None:
        providers.append("cerebras")
    
    # Note: huggingface, anthropic, and aws are temporarily disabled due to parameter compatibility issues
    
    return providers