import os
import asyncio
import warnings
from turtle import st
from typing import Any, Optional, Dict, List
from httpx import stream
from pydantic import SecretStr
from . mcpTool import load_mcp_connection
from langgraph.prebuilt import create_react_agent

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
    proxy_required: bool = False,
    streaming: bool = False
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
        streaming: Whether to enable streaming for the model
        
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
                "temperature": temperature,
                "streaming": streaming
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
                temperature=temperature,
                streaming=streaming
            )
            
        elif provider == "azure":
            if AzureAIChatCompletionsModel is None:
                raise ValueError("AzureAIChatCompletionsModel is not available. Please install langchain-azure-ai package.")
            if not api_key:
                raise ValueError("API key is required for Azure AI")
            
            os.environ["AZURE_INFERENCE_CREDENTIAL"] = api_key
            
            model = AzureAIChatCompletionsModel(
                model=model_name,
                endpoint=base_url or "https://models.github.ai/inference",
                temperature=temperature
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
            model = ChatHuggingFace(llm=llm, model_id=model_name, streaming=streaming, temperature=temperature)

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
                temperature=temperature,
                streaming=streaming
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
                base_url="https://openrouter.ai/api/v1",
                streaming=streaming
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
                temperature=temperature,
                streaming=streaming
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



def generate_llm_response(
    llm_provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.0,
    proxy_required: bool = False,
    streaming: bool = False,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
    messages: Optional[List[Any]] = None
) -> Any:
    """
    Generate a response from the LLM model based on the provided messages.
    
    Args:
        llm_provider: The LLM provider to use
        model_name: The model name to use
        api_key: API key for the provider (if required)
        base_url: Base URL for the provider (if required)
        temperature: Temperature setting for the model (default: 0.0)
        proxy_required: Whether to configure proxy settings
        streaming: Whether to enable streaming for the model
        mcp_servers: Dictionary of MCP server configurations with server names as keys
                    Example: {
                        "math": {
                            "command": "python",
                            "args": ["/path/to/math_server.py"],
                            "env": {"ENVIRONMENT_VAR": "value"},
                            "transport": "stdio"
                        },
                        "weather": {
                            "url": "http://localhost:8000/mcp/",
                            "transport": "streamable_http"
                        }
                    }
        messages: List of LangChain message objects to send to the LLM
        
    Returns:
        Response from the LLM model
    """
    
    logger = settings.logger
    
    # Configure the LLM model
    model = configure_llm(
        llm_provider=llm_provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        proxy_required=proxy_required
    )

    if model is None:
        logger.error(f"Failed to configure LLM model: {llm_provider}, {model_name}")
        return None

    # Ensure messages is not None
    if messages is None:
        logger.error(f"No input messages provided: {messages} is None")
        return None

    # Create agent with MCP tools if provided
    try:
        if mcp_servers:
            logger.info(f"Loading MCP tools for servers: {list(mcp_servers.keys())}")
            
            async def run_with_mcp_tools():
                all_tools = []
                
                # Load tools from each MCP server
                for server_name, server_config in mcp_servers.items():
                    try:
                        logger.info(f"Loading tools from MCP server: {server_name}")
                        
                        # Handle different transport types
                        if server_config.get("transport") == "stdio":
                            # For stdio transport, construct the command string
                            command = server_config.get("command", "")
                            args = server_config.get("args", [])
                            if args:
                                mcp_command = f"{command} {' '.join(args)}"
                            else:
                                mcp_command = command
                                
                            # Load tools using existing function
                            tools = await load_mcp_connection(mcp_command, server_config.get("env", {}))
                            all_tools.extend(tools)
                            logger.info(f"Loaded {len(tools)} tools from {server_name}")
                            
                        elif server_config.get("transport") == "streamable_http":
                            # For HTTP transport, we would need different handling
                            # This is not implemented in the existing load_mcp_connection function
                            logger.warning(f"HTTP transport not yet supported for server {server_name}")
                            
                        else:
                            logger.warning(f"Unsupported transport type for server {server_name}: {server_config.get('transport')}")
                            
                    except Exception as e:
                        logger.error(f"Failed to load tools from server {server_name}: {str(e)}")
                        # Continue with other servers even if one fails
                        continue
                
                if all_tools:
                    # Create a react agent with all the collected MCP tools
                    agent = create_react_agent(model, all_tools)
                    
                    # Convert messages to agent format and invoke
                    response = await agent.ainvoke({"messages": messages})
                    return response
                else:
                    # No tools loaded, fall back to direct model invocation
                    logger.info("No MCP tools loaded, falling back to direct model invocation")
                    response = await model.ainvoke(messages)
                    return response
            
            response = asyncio.run(run_with_mcp_tools())
            logger.info(f"Agent response generated successfully with MCP tools")
            logger.debug(f"Agent response format: {type(response)}")
            if isinstance(response, dict) and 'messages' in response:
                logger.debug(f"Agent response contains {len(response['messages'])} messages")
                for i, msg in enumerate(response['messages']):
                    logger.debug(f"Message {i}: {type(msg).__name__} - {getattr(msg, 'content', str(msg))[:100]}...")
            return response
        else:
            # Direct model invocation without MCP tools
            response = asyncio.run(model.ainvoke(messages))
            logger.info(f"LLM response generated successfully without MCP tools")
            logger.debug(f"LLM response format: {type(response)}")
            logger.debug(f"LLM response content: {getattr(response, 'content', str(response))[:100]}...")
            return response
            
    except Exception as e:
        logger.error(f"Error invoking model: {str(e)}")
        return None