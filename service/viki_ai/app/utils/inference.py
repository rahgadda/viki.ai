import os
import asyncio
import warnings
import json
from turtle import st
from typing import Any, Optional, Dict, List, Literal, Union
from httpx import stream
from pydantic import SecretStr
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

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
    messages: Optional[List[Any]] = None,
    message_id: Optional[str] = None
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
        message_id: Optional message ID for thread management in MCP agents
        
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
            logger.debug(f"MCP servers configuration: {mcp_servers}")
            
            async def get_mcp_response():

                memory = MemorySaver()
                client = MultiServerMCPClient(mcp_servers) # type: ignore
                tools = await client.get_tools()
                agent = create_react_agent(
                    model=model,
                    tools=tools, # type: ignore
                    interrupt_before=["tools"],
                    checkpointer=memory
                )

                # LangGraph agents expect messages in dict format with configurable thread_id
                config = RunnableConfig(configurable={"thread_id": message_id or "default_thread"})
                return await agent.ainvoke({"messages": messages}, config=config)
            
            response = asyncio.run(get_mcp_response())
            logger.info(f"LLM response generated successfully with MCP tools")
            logger.debug(f"LLM response format: {response}")
            return response

        else:
            # Direct model invocation without MCP tools
            response = asyncio.run(model.ainvoke(messages))
            logger.info(f"LLM response generated successfully without MCP tools")
            logger.debug(f"LLM response format: {response}")
            return response
            
    except Exception as e:
        logger.error(f"Error invoking model: {str(e)}")
        return None


def process_tool_call_approval(
    tool_name: str,
    tool_parameters: Dict[str, Any],
    action: Literal["approve", "modify", "reject"],
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
    modified_parameters: Optional[Dict[str, Any]] = None,
    rejection_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process tool call approval, modification, or rejection.
    
    Args:
        tool_name: Name of the tool to execute or reject
        tool_parameters: Original tool parameters
        action: Action to take - "approve", "modify", or "reject"
        mcp_servers: Dictionary of MCP server configurations
        modified_parameters: Modified parameters if action is "modify"
        rejection_reason: Reason for rejection if action is "reject"
        
    Returns:
        Dict containing execution result with keys:
        - success: bool indicating if operation was successful
        - action: str indicating what action was taken
        - tool_name: str name of the tool
        - parameters: dict final parameters used (original or modified)
        - result: str result message or error description
        - error: Optional[str] error message if execution failed
    """
    
    logger = settings.logger
    
    try:
        if action == "reject":
            reason = rejection_reason or "Tool call was rejected by user"
            logger.info(f"Tool call rejected: {tool_name} - {reason}")
            
            return {
                "success": True,
                "action": "reject",
                "tool_name": tool_name,
                "parameters": tool_parameters,
                "result": f"Tool call rejected: {reason}",
                "error": None
            }
        
        elif action in ["approve", "modify"]:
            # Use modified parameters if provided, otherwise use original
            final_parameters = modified_parameters if action == "modify" and modified_parameters else tool_parameters
            
            if action == "modify":
                logger.info(f"Tool call modified: {tool_name} - parameters updated")
                logger.debug(f"Original parameters: {tool_parameters}")
                logger.debug(f"Modified parameters: {final_parameters}")
            else:
                logger.info(f"Tool call approved: {tool_name}")
            
            # Execute the tool call
            execution_result = execute_mcp_tool(
                tool_name=tool_name,
                parameters=final_parameters,
                mcp_servers=mcp_servers
            )
            
            return {
                "success": execution_result["success"],
                "action": action,
                "tool_name": tool_name,
                "parameters": final_parameters,
                "result": execution_result["result"],
                "error": execution_result.get("error")
            }
        
        else:
            error_msg = f"Invalid action: {action}. Must be 'approve', 'modify', or 'reject'"
            logger.error(error_msg)
            return {
                "success": False,
                "action": action,
                "tool_name": tool_name,
                "parameters": tool_parameters,
                "result": error_msg,
                "error": error_msg
            }
    
    except Exception as e:
        error_msg = f"Error processing tool call approval: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "action": action,
            "tool_name": tool_name,
            "parameters": tool_parameters,
            "result": error_msg,
            "error": error_msg
        }


def execute_mcp_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Execute a specific MCP tool with given parameters.
    
    Args:
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool
        mcp_servers: Dictionary of MCP server configurations
        
    Returns:
        Dict containing execution result:
        - success: bool indicating if execution was successful
        - result: str result from tool execution
        - error: Optional[str] error message if execution failed
    """
    
    logger = settings.logger
    
    try:
        if not mcp_servers:
            logger.warning("No MCP servers configured for tool execution")
            return {
                "success": False,
                "result": "No MCP servers configured",
                "error": "No MCP servers available for tool execution"
            }
        
        async def execute_tool():
            try:
                client = MultiServerMCPClient(mcp_servers) # type: ignore
                tools = await client.get_tools()
                
                # Find the specific tool
                target_tool = None
                for tool in tools:
                    if hasattr(tool, 'name') and tool.name == tool_name:
                        target_tool = tool
                        break
                
                if not target_tool:
                    available_tools = [getattr(tool, 'name', 'unnamed') for tool in tools]
                    return {
                        "success": False,
                        "result": f"Tool '{tool_name}' not found",
                        "error": f"Tool '{tool_name}' not found. Available tools: {available_tools}"
                    }
                
                # Execute the tool
                logger.debug(f"Executing tool '{tool_name}' with parameters: {parameters}")
                result = await target_tool.ainvoke(parameters)
                
                logger.info(f"Tool '{tool_name}' executed successfully")
                return {
                    "success": True,
                    "result": str(result),
                    "error": None
                }
                
            except Exception as e:
                error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "result": error_msg,
                    "error": error_msg
                }
        
        # Run the async tool execution
        result = asyncio.run(execute_tool())
        return result
        
    except Exception as e:
        error_msg = f"Error setting up tool execution: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "result": error_msg,
            "error": error_msg
        }


def continue_conversation_after_tool(
    llm_provider: str,
    model_name: str,
    messages: List[Any],
    tool_result: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.0,
    proxy_required: bool = False,
    streaming: bool = False,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
    message_id: Optional[str] = None
) -> Any:
    """
    Continue the conversation after tool execution by generating the next AI response.
    
    Args:
        llm_provider: The LLM provider to use
        model_name: The model name to use
        messages: List of conversation messages including the tool result
        tool_result: Result from the tool execution
        api_key: API key for the provider (if required)
        base_url: Base URL for the provider (if required)
        temperature: Temperature setting for the model
        proxy_required: Whether to configure proxy settings
        streaming: Whether to enable streaming
        mcp_servers: Dictionary of MCP server configurations
        message_id: Optional message ID for thread management
        
    Returns:
        Response from the LLM model or None if failed
    """
    
    logger = settings.logger
    
    try:
        # Add the tool result as a ToolMessage to the conversation
        updated_messages = messages.copy()
        updated_messages.append(ToolMessage(content=tool_result, tool_call_id=message_id or "tool_execution"))
        
        # Generate the next AI response
        response = generate_llm_response(
            llm_provider=llm_provider,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            proxy_required=proxy_required,
            streaming=streaming,
            mcp_servers=mcp_servers,
            messages=updated_messages,
            message_id=message_id
        )
        
        logger.info("Conversation continued successfully after tool execution")
        return response
        
    except Exception as e:
        logger.error(f"Error continuing conversation after tool execution: {str(e)}")
        return None