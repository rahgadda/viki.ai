from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import json
import re
from datetime import datetime
from httpx import HTTPStatusError, RequestError, TimeoutException
from app.utils.database import get_db
from app.utils.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.agent import Agent, AgentTool
from app.models.llm import LLM
from app.models.tool import Tool, ToolEnvironmentVariable
from app.schemas.chat import (
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
    ChatSessionUpdate,
    ChatMessageCreate,
    ChatMessageUpdateUser,
    ChatSessionCreateWithMessage,
    ChatSessionPublic,
    ChatMessagePublic,
    ChatSessionWithMessages,
    ToolCallDetail,
    ToolCallApprovalRequest,
    ToolCallApprovalResponse
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.utils.inference import generate_llm_response, process_tool_call_approval, continue_conversation_after_tool

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def create_error_assistant_message(error: Exception, session_id: str, agent_name: str, username: str, db: Session) -> Optional[ChatMessage]:
    """
    Create an assistant message with error details for user-facing errors.
    
    Args:
        error: The exception that occurred
        session_id: Chat session ID
        agent_name: Agent name for the message
        username: Username for audit trail
        db: Database session
        
    Returns:
        ChatMessage object if an error message was created, None otherwise
    """
    error_str = str(error)
    error_content = None
    
    # Handle specific HTTP status errors first
    if isinstance(error, HTTPStatusError):
        status_code = error.response.status_code
        
        if status_code == 413:
            error_content = """I apologize, but your request is too large to process.

**What happened:**
The message or file you're trying to send exceeds the maximum size limit.

**What you can try:**
1. **Reduce message length:** Try sending a shorter message
2. **Split your request:** Break large requests into smaller parts
3. **Remove large attachments:** If you're including files or large amounts of text, try reducing them
4. **Start fresh:** Begin a new conversation to reduce context size

Please try again with a smaller request."""

        elif status_code == 429:
            error_content = """I apologize, but I'm currently receiving too many requests.

**What happened:**
The service is experiencing high traffic and has temporary rate limits in place.

**What you can try:**
1. **Wait a moment:** Please wait 30-60 seconds before trying again
2. **Retry your request:** Your previous message wasn't processed, so you can send it again
3. **Be patient:** High traffic periods usually resolve quickly

Please try again in a few moments."""

        elif status_code in [401, 403]:
            error_content = """I apologize, but there's an authentication issue preventing me from processing your request.

**What happened:**
There's a problem with the service configuration or API access.

**What you can try:**
1. **Try again:** This might be a temporary issue
2. **Contact support:** If the problem persists, please contact your administrator
3. **Check service status:** The AI service might be temporarily unavailable

This appears to be a configuration issue rather than a problem with your request."""

        elif status_code >= 500:
            error_content = """I apologize, but the AI service is currently experiencing technical difficulties.

**What happened:**
The AI service is temporarily unavailable or experiencing issues.

**What you can try:**
1. **Try again:** This is likely a temporary service issue
2. **Wait a moment:** Server issues often resolve quickly
3. **Retry later:** If the problem persists, please try again in a few minutes

Your message wasn't processed, so you can safely try sending it again."""

    # Handle network/connection errors
    elif isinstance(error, (RequestError, TimeoutException)):
        error_content = """I apologize, but I'm having trouble connecting to the AI service.

**What happened:**
There's a network or connectivity issue preventing me from processing your request.

**What you can try:**
1. **Try again:** This is likely a temporary network issue
2. **Wait a moment:** Network issues often resolve quickly
3. **Check your connection:** Ensure your internet connection is stable

Your message wasn't processed, so you can safely try sending it again."""

    # Handle rate limit errors (TPM/RPM limits) - for text-based error messages
    elif "rate_limit_exceeded" in error_str or "Request too large" in error_str:
        # Extract key information from rate limit error
        model_match = re.search(r'model `([^`]+)`', error_str)
        limit_match = re.search(r'Limit (\d+)', error_str)
        requested_match = re.search(r'Requested (\d+)', error_str)
        
        model_name = model_match.group(1) if model_match else "the current model"
        limit = limit_match.group(1) if limit_match else "unknown"
        requested = requested_match.group(1) if requested_match else "unknown"
        
        if "tokens per minute" in error_str or "TPM" in error_str:
            error_content = f"""I apologize, but I've encountered a rate limit error. The request was too large for {model_name}.

**Error Details:**
- **Limit:** {limit} tokens per minute
- **Requested:** {requested} tokens
- **Issue:** Your message or conversation context is too large

**What you can try:**
1. **Reduce message size:** Try sending a shorter message
2. **Start a new conversation:** Begin a fresh chat session to reduce context size
3. **Break down your request:** Split complex requests into smaller parts
4. **Upgrade service tier:** Consider upgrading your plan for higher limits

Please try again with a smaller message or start a new conversation."""

    # Handle HTTP 413 errors (Request Entity Too Large) - text-based
    elif "413" in error_str or "Request Entity Too Large" in error_str:
        error_content = """I apologize, but your request is too large to process.

**What happened:**
The message or file you're trying to send exceeds the maximum size limit.

**What you can try:**
1. **Reduce message length:** Try sending a shorter message
2. **Split your request:** Break large requests into smaller parts
3. **Remove large attachments:** If you're including files or large amounts of text, try reducing them
4. **Start fresh:** Begin a new conversation to reduce context size

Please try again with a smaller request."""

    # Handle 429 errors (Too Many Requests) - text-based
    elif "429" in error_str or "Too Many Requests" in error_str:
        error_content = """I apologize, but I'm currently receiving too many requests.

**What happened:**
The service is experiencing high traffic and has temporary rate limits in place.

**What you can try:**
1. **Wait a moment:** Please wait 30-60 seconds before trying again
2. **Retry your request:** Your previous message wasn't processed, so you can send it again
3. **Be patient:** High traffic periods usually resolve quickly

Please try again in a few moments."""

    # Handle authentication/authorization errors - text-based
    elif "401" in error_str or "403" in error_str or "unauthorized" in error_str.lower() or "forbidden" in error_str.lower():
        error_content = """I apologize, but there's an authentication issue preventing me from processing your request.

**What happened:**
There's a problem with the service configuration or API access.

**What you can try:**
1. **Try again:** This might be a temporary issue
2. **Contact support:** If the problem persists, please contact your administrator
3. **Check service status:** The AI service might be temporarily unavailable

This appears to be a configuration issue rather than a problem with your request."""

    # Handle network/connection errors - text-based
    elif any(term in error_str.lower() for term in ["connection", "network", "timeout", "unreachable"]):
        error_content = """I apologize, but I'm having trouble connecting to the AI service.

**What happened:**
There's a network or connectivity issue preventing me from processing your request.

**What you can try:**
1. **Try again:** This is likely a temporary network issue
2. **Wait a moment:** Network issues often resolve quickly
3. **Check your connection:** Ensure your internet connection is stable

Your message wasn't processed, so you can safely try sending it again."""

    # Handle event loop/async errors (suppress from user)
    elif "Event loop is closed" in error_str or "RuntimeError" in error_str:
        # Log the error but don't create a user-facing message
        settings.logger.error(f"Internal async error (suppressed from user): {error_str}")
        return None

    # Handle generic model/LLM errors
    elif any(term in error_str.lower() for term in ["model", "llm", "inference", "generation"]):
        error_content = """I apologize, but I encountered an issue while generating a response.

**What happened:**
There was a problem with the AI model processing your request.

**What you can try:**
1. **Rephrase your request:** Try asking your question in a different way
2. **Simplify your request:** Break complex questions into smaller parts
3. **Try again:** This might be a temporary issue with the AI service
4. **Start fresh:** Begin a new conversation if the problem persists

Your message was received, but I wasn't able to generate a proper response."""

    # Handle generic errors
    else:
        error_content = """I apologize, but I encountered an unexpected error while processing your request.

**What happened:**
An unexpected technical issue occurred while trying to help you.

**What you can try:**
1. **Try again:** This might be a temporary issue
2. **Rephrase your request:** Try asking your question differently
3. **Start a new conversation:** Begin fresh if the problem persists
4. **Contact support:** If errors continue, please contact your administrator

I'm still here to help once the issue is resolved."""

    # Create assistant message if we have error content
    if error_content:
        error_msg_id = str(uuid.uuid4())
        db_error_message = ChatMessage(
            msg_id=error_msg_id,
            msg_cht_id=session_id,
            msg_agent_name=agent_name,
            msg_role="assistant",
            msg_content=error_content,
            created_by=username,
            last_updated_by=username
        )
        db.add(db_error_message)
        db.commit()
        db.refresh(db_error_message)
        return db_error_message
    
    return None


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


# Utility function to extract content from LangChain message
def extract_message_content(msg) -> str:
    """
    Extract content from a LangChain message, handling both string and list formats.
    
    Args:
        msg: LangChain message object
        
    Returns:
        str: Extracted content as string
    """
    content = getattr(msg, 'content', str(msg))
    
    if isinstance(content, list):
        # Convert list content to string representation
        content_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    content_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'unknown_tool')
                    tool_input = item.get('input', {})
                    content_parts.append(f"[Tool Call: {tool_name} with input: {tool_input}]")
                else:
                    content_parts.append(str(item))
            else:
                content_parts.append(str(item))
        content = ' '.join(content_parts) if content_parts else str(content)
    elif not isinstance(content, str):
        content = str(content)
    
    return content


# Chat Session endpoints
@router.get("/chat/sessions", response_model=List[ChatSessionSchema])
def get_chat_sessions(
    skip: int = 0,
    limit: int = 100,
    agentId: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all chat sessions with pagination and optional filtering"""
    query = db.query(ChatSession)
    
    if agentId:
        query = query.filter(ChatSession.cht_agt_id == agentId)
    
    sessions = query.offset(skip).limit(limit).all()
    return [ChatSessionSchema.from_db_model(session) for session in sessions]


@router.get("/chat/sessions/{sessionId}", response_model=ChatSessionWithMessages)
def get_chat_session(
    sessionId: str,
    db: Session = Depends(get_db)
):
    """Get a specific chat session by ID with all messages"""
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Convert to schema with messages
    session_data = ChatSessionSchema.from_db_model(db_session)
    messages = [ChatMessageSchema.from_db_model(msg) for msg in db_session.messages]
    
    # Convert to public schemas for response
    session_public = ChatSessionPublic(**session_data.dict())
    messages_public = [ChatMessagePublic(**msg.dict()) for msg in messages]
    
    return ChatSessionWithMessages(
        **session_public.dict(),
        messages=messages_public
    )


@router.post("/chat/sessions", response_model=ChatSessionWithMessages, status_code=status.HTTP_201_CREATED)
def create_chat_session_with_message(
    chat_create: ChatSessionCreateWithMessage,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new chat session with an initial message"""
    # Verify agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == chat_create.chatAgentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{chat_create.chatAgentId}' not found"
        )
    
    # Generate UUIDs
    session_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    # Create chat name from first 240 characters of message
    chat_name = chat_create.messageContent[:240].strip()
    if len(chat_create.messageContent) > 240:
        chat_name += "..."
    
    # Create chat session
    db_session = ChatSession(
        cht_id=session_id,
        cht_name=chat_name,
        cht_agt_id=chat_create.chatAgentId,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_session)
    
    # Create initial message with user role
    db_message = ChatMessage(
        msg_id=message_id,
        msg_cht_id=session_id,
        msg_agent_name=db_agent.agt_name,
        msg_role="user",
        msg_content=chat_create.messageContent,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_message)
    
    db.commit()
    db.refresh(db_session)
    db.refresh(db_message)
    
    # Create LangChain message list and generate LLM response
    try:
        # Get agent's LLM configuration
        db_llm = db.query(LLM).filter(LLM.llc_id == db_agent.agt_llc_id).first()
        if db_llm is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration for agent '{chat_create.chatAgentId}' not found"
            )
        
        # Create LangChain message list
        langchain_messages = []
        
        # Add system message if agent has system prompt
        system_prompt = getattr(db_agent, 'agt_system_prompt', None)
        if system_prompt:
            langchain_messages.append(SystemMessage(content=system_prompt))
        
        # Add user message
        langchain_messages.append(HumanMessage(content=chat_create.messageContent))
        
        # Get MCP servers configuration for the agent
        mcp_servers = get_agent_mcp_servers_config(chat_create.chatAgentId, db)

        # Generate LLM response
        ai_response = generate_llm_response(
            llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
            model_name=getattr(db_llm, 'llc_model_cd'),
            api_key=getattr(db_llm, 'llc_api_key', None),
            base_url=getattr(db_llm, 'llc_endpoint_url', None),
            temperature=0.0,
            proxy_required=getattr(db_llm, 'llc_proxy_required', False),
            streaming=getattr(db_llm, 'llc_streaming', False),
            mcp_servers=mcp_servers,
            messages=langchain_messages,
            message_id=message_id
        )
        
        # Create AI response message if we got a response
        if ai_response:
            # Handle different response formats
            messages_to_persist = []
            
            # If response has 'messages' key (agent response), extract messages
            if isinstance(ai_response, dict) and 'messages' in ai_response:
                response_messages = ai_response['messages']
                # Find new messages (those not in our original input)
                for msg in response_messages:
                    if not any(orig_msg.id == getattr(msg, 'id', None) for orig_msg in langchain_messages):
                        messages_to_persist.append(msg)
            # If response is a single message object (direct model response)
            elif hasattr(ai_response, 'content'):
                messages_to_persist.append(ai_response)
            
            # Persist all new messages
            persisted_messages = []
            for msg in messages_to_persist:
                msg_id = str(uuid.uuid4())
                
                # Determine role from message type and extract content properly
                if hasattr(msg, '__class__'):
                    msg_type = msg.__class__.__name__
                    if msg_type == 'AIMessage':
                        # Check if this is a tool call (empty content with tool_calls in additional_kwargs)
                        additional_kwargs = getattr(msg, 'additional_kwargs', {})
                        tool_calls = additional_kwargs.get('tool_calls', [])
                        msg_content = getattr(msg, 'content', '')
                        
                        if not msg_content and tool_calls:
                            # This is a tool call - record as tool_input message
                            role = 'tool_input'
                            # Extract tool name and arguments from first tool call
                            first_tool_call = tool_calls[0]
                            tool_name = first_tool_call.get('function', {}).get('name', 'unknown_tool')
                            tool_arguments = first_tool_call.get('function', {}).get('arguments', '{}')
                            content = f"Tool: {tool_name}, Arguments: {tool_arguments}"
                        else:
                            # Regular assistant message
                            role = 'assistant'
                            content = extract_message_content(msg)
                    elif msg_type == 'HumanMessage':
                        role = 'user'
                        content = extract_message_content(msg)
                    elif msg_type == 'SystemMessage':
                        role = 'system'
                        content = extract_message_content(msg)
                    elif msg_type == 'ToolMessage':
                        role = 'tool_response'
                        content = extract_message_content(msg)
                    else:
                        role = 'assistant'  # Default fallback
                        content = extract_message_content(msg)
                else:
                    role = 'assistant'  # Default fallback
                    content = extract_message_content(msg)
                
                db_message = ChatMessage(
                    msg_id=msg_id,
                    msg_cht_id=session_id,
                    msg_agent_name=db_agent.agt_name,
                    msg_role=role,
                    msg_content=content,
                    created_by=username,
                    last_updated_by=username
                )
                db.add(db_message)
                persisted_messages.append(db_message)
            
            if persisted_messages:
                db.commit()
                for db_msg in persisted_messages:
                    db.refresh(db_msg)
                
                # Convert both user message and all AI messages to schemas
                all_messages = [ChatMessageSchema.from_db_model(db_message)]
                for ai_msg in persisted_messages:
                    all_messages.append(ChatMessageSchema.from_db_model(ai_msg))
                
                # Convert to public schemas for response
                session_data = ChatSessionSchema.from_db_model(db_session)
                session_public = ChatSessionPublic(**session_data.dict())
                messages_public = [ChatMessagePublic(**msg.dict()) for msg in all_messages]
                
                return ChatSessionWithMessages(
                    **session_public.dict(),
                    messages=messages_public
                )
    
    except (HTTPStatusError, RequestError, TimeoutException) as http_error:
        settings.logger.error(f"HTTP/Network error generating LLM response: {str(http_error)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(http_error, session_id, getattr(db_agent, 'agt_name'), username, db)
        if error_message:
            # Update response to include error message
            session_data = ChatSessionSchema.from_db_model(db_session)
            user_message_data = ChatMessageSchema.from_db_model(db_message)
            error_message_data = ChatMessageSchema.from_db_model(error_message)
            
            # Convert to public schemas for response
            session_public = ChatSessionPublic(**session_data.dict())
            user_message_public = ChatMessagePublic(**user_message_data.dict())
            error_message_public = ChatMessagePublic(**error_message_data.dict())
            
            return ChatSessionWithMessages(
                **session_public.dict(),
                messages=[user_message_public, error_message_public]
            )
    except Exception as e:
        settings.logger.error(f"Unexpected error generating LLM response: {str(e)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(e, session_id, getattr(db_agent, 'agt_name'), username, db)
        if error_message:
            # Update response to include error message
            session_data = ChatSessionSchema.from_db_model(db_session)
            user_message_data = ChatMessageSchema.from_db_model(db_message)
            error_message_data = ChatMessageSchema.from_db_model(error_message)
            
            # Convert to public schemas for response
            session_public = ChatSessionPublic(**session_data.dict())
            user_message_public = ChatMessagePublic(**user_message_data.dict())
            error_message_public = ChatMessagePublic(**error_message_data.dict())
            
            return ChatSessionWithMessages(
                **session_public.dict(),
                messages=[user_message_public, error_message_public]
            )
    
    # Return session with the created message
    session_data = ChatSessionSchema.from_db_model(db_session)
    message_data = ChatMessageSchema.from_db_model(db_message)
    
    # Convert to public schemas for response
    session_public = ChatSessionPublic(**session_data.dict())
    message_public = ChatMessagePublic(**message_data.dict())
    
    return ChatSessionWithMessages(
        **session_public.dict(),
        messages=[message_public]
    )

@router.put("/chat/sessions/{sessionId}", response_model=ChatSessionSchema)
def update_chat_session(
    sessionId: str,
    session_update: ChatSessionUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a chat session"""
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Update only provided fields
    if session_update.chatName is not None:
        setattr(db_session, 'cht_name', session_update.chatName)
    if session_update.chatAgentId is not None:
        # Verify agent exists
        db_agent = db.query(Agent).filter(Agent.agt_id == session_update.chatAgentId).first()
        if db_agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{session_update.chatAgentId}' not found"
            )
        setattr(db_session, 'cht_agt_id', session_update.chatAgentId)
    
    setattr(db_session, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_session)
    return ChatSessionSchema.from_db_model(db_session)


@router.delete("/chat/sessions/{sessionId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    sessionId: str,
    db: Session = Depends(get_db)
):
    """Delete a chat session (and all its messages due to CASCADE)"""
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    db.delete(db_session)
    db.commit()

@router.post("/chat/sessions/{sessionId}/messages", response_model=List[ChatMessageSchema], status_code=status.HTTP_201_CREATED)
def create_chat_message(
    sessionId: str,
    message_create: ChatMessageCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Add a new user message to an existing chat session. The message role is automatically set to 'user', 
    chat ID is derived from sessionId, and agent name is determined from the session's associated agent."""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Get agent for the session
    db_agent = db.query(Agent).filter(Agent.agt_id == db_session.cht_agt_id).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent for session '{sessionId}' not found"
        )
    
    # Generate UUID for the message
    message_id = str(uuid.uuid4())
    
    # Create user message with derived values
    db_message = ChatMessage(
        msg_id=message_id,
        msg_cht_id=sessionId,  # Derived from sessionId
        msg_agent_name=db_agent.agt_name,  # Derived from session's agent
        msg_role="user",  # Always "user" for this endpoint
        msg_content=message_create.messageContent,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    created_messages = [ChatMessageSchema.from_db_model(db_message)]
    
    # Generate LLM response since the new message is always from user
    try:
            # Get agent's LLM configuration
            db_llm = db.query(LLM).filter(LLM.llc_id == db_agent.agt_llc_id).first()
            if db_llm is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"LLM configuration for agent not found"
                )
            
            # Get all messages for this session to build context
            all_messages = db.query(ChatMessage).filter(
                ChatMessage.msg_cht_id == sessionId
            ).order_by(ChatMessage.creation_dt).all()
            
            # Create LangChain message list
            langchain_messages = []
            
            # Add system message if agent has system prompt
            system_prompt = getattr(db_agent, 'agt_system_prompt', None)
            if system_prompt:
                langchain_messages.append(SystemMessage(content=system_prompt))
            
            # Add all messages from the session
            for msg in all_messages:
                msg_role = getattr(msg, 'msg_role')
                msg_content = getattr(msg, 'msg_content')
                
                if msg_role == "user":
                    langchain_messages.append(HumanMessage(content=msg_content))
                elif msg_role == "assistant":
                    langchain_messages.append(AIMessage(content=msg_content))
                elif msg_role == "system":
                    langchain_messages.append(SystemMessage(content=msg_content))
                elif msg_role == "tool_input":
                    # Tool input messages represent the tool call request
                    langchain_messages.append(AIMessage(content=msg_content, additional_kwargs={"tool_calls": []}))
                elif msg_role == "tool_response":
                    langchain_messages.append(ToolMessage(content=msg_content, tool_call_id="default_tool_id"))
            
            # Get MCP servers configuration for the agent
            mcp_servers = get_agent_mcp_servers_config(getattr(db_session, 'cht_agt_id'), db)
            
            # Generate LLM response
            ai_response = generate_llm_response(
                llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
                model_name=getattr(db_llm, 'llc_model_cd'),
                api_key=getattr(db_llm, 'llc_api_key', None),
                base_url=getattr(db_llm, 'llc_endpoint_url', None),
                temperature=0.0,
                proxy_required=getattr(db_llm, 'llc_proxy_required', False),
                streaming=getattr(db_llm, 'llc_streaming', False),
                mcp_servers=mcp_servers,
                messages=langchain_messages,
                message_id=message_id
            )
            
            # Create AI response message if we got a response
            if ai_response:
                # Handle different response formats
                messages_to_persist = []
                
                # If response has 'messages' key (agent response), extract messages
                if isinstance(ai_response, dict) and 'messages' in ai_response:
                    response_messages = ai_response['messages']
                    # Find new messages (those not in our original input)
                    for msg in response_messages:
                        if not any(orig_msg.id == getattr(msg, 'id', None) for orig_msg in langchain_messages):
                            messages_to_persist.append(msg)
                # If response is a single message object (direct model response)
                elif hasattr(ai_response, 'content'):
                    messages_to_persist.append(ai_response)
                
                # Persist all new messages
                for msg in messages_to_persist:
                    msg_id = str(uuid.uuid4())
                    
                    # Determine role from message type and extract content properly
                    if hasattr(msg, '__class__'):
                        msg_type = msg.__class__.__name__
                        if msg_type == 'AIMessage':
                            # Check if this is a tool call (empty content with tool_calls in additional_kwargs)
                            additional_kwargs = getattr(msg, 'additional_kwargs', {})
                            tool_calls = additional_kwargs.get('tool_calls', [])
                            msg_content = getattr(msg, 'content', '')
                            
                            if not msg_content and tool_calls:
                                # This is a tool call - record as tool_input message
                                role = 'tool_input'
                                # Extract tool name and arguments from first tool call
                                first_tool_call = tool_calls[0]
                                tool_name = first_tool_call.get('function', {}).get('name', 'unknown_tool')
                                tool_arguments = first_tool_call.get('function', {}).get('arguments', '{}')
                                content = f"Tool: {tool_name}, Arguments: {tool_arguments}"
                            else:
                                # Regular assistant message
                                role = 'assistant'
                                content = extract_message_content(msg)
                        elif msg_type == 'HumanMessage':
                            role = 'user'
                            content = extract_message_content(msg)
                        elif msg_type == 'SystemMessage':
                            role = 'system'
                            content = extract_message_content(msg)
                        elif msg_type == 'ToolMessage':
                            role = 'tool_response'
                            content = extract_message_content(msg)
                        else:
                            role = 'assistant'  # Default fallback
                            content = extract_message_content(msg)
                    else:
                        role = 'assistant'  # Default fallback
                        content = extract_message_content(msg)
                    
                    db_ai_message = ChatMessage(
                        msg_id=msg_id,
                        msg_cht_id=sessionId,
                        msg_agent_name=db_agent.agt_name,
                        msg_role=role,
                        msg_content=content,
                        created_by=username,
                        last_updated_by=username
                    )
                    db.add(db_ai_message)
                    db.commit()
                    db.refresh(db_ai_message)
                    
                    # Add AI message to the response
                    created_messages.append(ChatMessageSchema.from_db_model(db_ai_message))
    
    except (HTTPStatusError, RequestError, TimeoutException) as http_error:
        settings.logger.error(f"HTTP/Network error generating LLM response: {str(http_error)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(http_error, sessionId, getattr(db_agent, 'agt_name'), username, db)
        if error_message:
            created_messages.append(ChatMessageSchema.from_db_model(error_message))
    except Exception as e:
        settings.logger.error(f"Unexpected error generating LLM response: {str(e)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(e, sessionId, getattr(db_agent, 'agt_name'), username, db)
        if error_message:
            created_messages.append(ChatMessageSchema.from_db_model(error_message))
    
    return created_messages


@router.put("/chat/sessions/{sessionId}/messages/{messageId}", response_model=List[ChatMessageSchema])
def update_chat_message(
    sessionId: str,
    messageId: str,
    message_update: ChatMessageUpdateUser,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a user message. Only user messages can be modified. After update, all subsequent messages 
    are deleted and a new LLM response is generated."""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Find message and verify it belongs to the specified session
    db_message = db.query(ChatMessage).filter(
        ChatMessage.msg_id == messageId,
        ChatMessage.msg_cht_id == sessionId
    ).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat message '{messageId}' not found in session '{sessionId}'"
        )
    
    # Only allow modification of user messages
    if getattr(db_message, 'msg_role') != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only user messages can be modified"
        )
    
    # Get agent information
    db_agent = db.query(Agent).filter(Agent.agt_id == db_session.cht_agt_id).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent for session not found"
        )
    
    # Update the message content and derive other fields
    setattr(db_message, 'msg_content', message_update.messageContent)
    setattr(db_message, 'msg_agent_name', db_agent.agt_name)  # Derived from session
    setattr(db_message, 'msg_role', 'user')  # Always user
    setattr(db_message, 'last_updated_by', username)
    
    # Delete all messages after this one in the session
    message_creation_dt = getattr(db_message, 'creation_dt')
    subsequent_messages = db.query(ChatMessage).filter(
        ChatMessage.msg_cht_id == sessionId,
        ChatMessage.creation_dt > message_creation_dt
    ).all()
    
    for msg in subsequent_messages:
        db.delete(msg)
    
    db.commit()
    db.refresh(db_message)
    
    # Prepare response with the updated message
    updated_messages = [ChatMessageSchema.from_db_model(db_message)]
    
    # Generate new LLM response
    try:
        # Get agent's LLM configuration
        db_llm = db.query(LLM).filter(LLM.llc_id == db_agent.agt_llc_id).first()
        if db_llm is None:
            settings.logger.warning(f"LLM configuration for agent not found")
            return updated_messages
        
        # Get all remaining messages for this session to build context
        all_messages = db.query(ChatMessage).filter(
            ChatMessage.msg_cht_id == sessionId
        ).order_by(ChatMessage.creation_dt).all()
        
        # Create LangChain message list
        langchain_messages = []
        
        # Add system message if agent has system prompt
        system_prompt = getattr(db_agent, 'agt_system_prompt', None)
        if system_prompt:
            langchain_messages.append(SystemMessage(content=system_prompt))
        
        # Add all messages from the session
        for msg in all_messages:
            msg_role = getattr(msg, 'msg_role')
            msg_content = getattr(msg, 'msg_content')
            
            if msg_role == "user":
                langchain_messages.append(HumanMessage(content=msg_content))
            elif msg_role == "assistant":
                langchain_messages.append(AIMessage(content=msg_content))
            elif msg_role == "system":
                langchain_messages.append(SystemMessage(content=msg_content))
            elif msg_role == "tool_input":
                # Tool input messages represent the tool call request
                langchain_messages.append(AIMessage(content=msg_content, additional_kwargs={"tool_calls": []}))
            elif msg_role == "tool_response":
                langchain_messages.append(ToolMessage(content=msg_content, tool_call_id="default_tool_id"))
        
        # Get MCP servers configuration for the agent
        mcp_servers = get_agent_mcp_servers_config(getattr(db_session, 'cht_agt_id'), db)
        
        # Generate LLM response
        ai_response = generate_llm_response(
            llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
            model_name=getattr(db_llm, 'llc_model_cd'),
            api_key=getattr(db_llm, 'llc_api_key', None),
            base_url=getattr(db_llm, 'llc_endpoint_url', None),
            temperature=0.0,
            proxy_required=getattr(db_llm, 'llc_proxy_required', False),
            streaming=getattr(db_llm, 'llc_streaming', False),
            mcp_servers=mcp_servers,
            messages=langchain_messages,
            message_id=messageId
        )
        
        # Create AI response message if we got a response
        if ai_response:
            # Handle different response formats
            messages_to_persist = []
            
            # If response has 'messages' key (agent response), extract messages
            if isinstance(ai_response, dict) and 'messages' in ai_response:
                response_messages = ai_response['messages']
                # Find new messages (those not in our original input)
                for msg in response_messages:
                    if not any(orig_msg.id == getattr(msg, 'id', None) for orig_msg in langchain_messages):
                        messages_to_persist.append(msg)
            # If response is a single message object (direct model response)
            elif hasattr(ai_response, 'content'):
                messages_to_persist.append(ai_response)
            
            # Persist all new messages
            for msg in messages_to_persist:
                msg_id = str(uuid.uuid4())
                
                # Determine role from message type and extract content properly
                if hasattr(msg, '__class__'):
                    msg_type = msg.__class__.__name__
                    if msg_type == 'AIMessage':
                        # Check if this is a tool call (empty content with tool_calls in additional_kwargs)
                        additional_kwargs = getattr(msg, 'additional_kwargs', {})
                        tool_calls = additional_kwargs.get('tool_calls', [])
                        msg_content = getattr(msg, 'content', '')
                        
                        if not msg_content and tool_calls:
                            # This is a tool call - record as tool_input message
                            role = 'tool_input'
                            # Extract tool name and arguments from first tool call
                            first_tool_call = tool_calls[0]
                            tool_name = first_tool_call.get('function', {}).get('name', 'unknown_tool')
                            tool_arguments = first_tool_call.get('function', {}).get('arguments', '{}')
                            content = f"Tool: {tool_name}, Arguments: {tool_arguments}"
                        else:
                            # Regular assistant message
                            role = 'assistant'
                            content = extract_message_content(msg)
                    elif msg_type == 'HumanMessage':
                        role = 'user'
                        content = extract_message_content(msg)
                    elif msg_type == 'SystemMessage':
                        role = 'system'
                        content = extract_message_content(msg)
                    elif msg_type == 'ToolMessage':
                        role = 'tool_response'
                        content = extract_message_content(msg)
                    else:
                        role = 'assistant'  # Default fallback
                        content = extract_message_content(msg)
                else:
                    role = 'assistant'  # Default fallback
                    content = extract_message_content(msg)
                
                db_ai_message = ChatMessage(
                    msg_id=msg_id,
                    msg_cht_id=sessionId,
                    msg_agent_name=db_agent.agt_name,
                    msg_role=role,
                    msg_content=content,
                    created_by=username,
                    last_updated_by=username
                )
                db.add(db_ai_message)
                db.commit()
                db.refresh(db_ai_message)
                
                # Add AI message to the response
                updated_messages.append(ChatMessageSchema.from_db_model(db_ai_message))
    
    except (HTTPStatusError, RequestError, TimeoutException) as http_error:
        settings.logger.error(f"HTTP/Network error generating LLM response: {str(http_error)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(http_error, sessionId, getattr(db_agent, 'agt_name'), username, db)
        if error_message:
            updated_messages.append(ChatMessageSchema.from_db_model(error_message))
    except Exception as e:
        settings.logger.error(f"Unexpected error generating LLM response: {str(e)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(e, sessionId, getattr(db_agent, 'agt_name'), username, db)
        if error_message:
            updated_messages.append(ChatMessageSchema.from_db_model(error_message))
    
    return updated_messages


@router.delete("/chat/sessions/{sessionId}/messages/{messageId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_message(
    sessionId: str,
    messageId: str,
    db: Session = Depends(get_db)
):
    """Delete a chat message"""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Find message and verify it belongs to the specified session
    db_message = db.query(ChatMessage).filter(
        ChatMessage.msg_id == messageId,
        ChatMessage.msg_cht_id == sessionId
    ).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat message '{messageId}' not found in session '{sessionId}'"
        )
    
    db.delete(db_message)
    db.commit()


# Utility endpoints
@router.get("/chat/sessions/{sessionId}/messages", response_model=List[ChatMessageSchema])
def get_session_messages(
    sessionId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all messages for a specific chat session"""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.msg_cht_id == sessionId
    ).order_by(ChatMessage.creation_dt).offset(skip).limit(limit).all()
    
    return [ChatMessageSchema.from_db_model(message) for message in messages]


@router.get("/chat/agents/{agentId}/sessions", response_model=List[ChatSessionSchema])
def get_agent_sessions(
    agentId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all chat sessions for a specific agent"""
    # Verify agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    sessions = db.query(ChatSession).filter(
        ChatSession.cht_agt_id == agentId
    ).offset(skip).limit(limit).all()
    
    return [ChatSessionSchema.from_db_model(session) for session in sessions]


def get_agent_mcp_servers_config(agent_id: str, db: Session):
    """
    Get MCP servers configuration for an agent in the new MultiServerMCPClient format.
    Returns a dictionary with server names as keys and configurations as values.
    """
    mcp_servers = {}
    
    # Get all tools associated with the agent
    agent_tools = db.query(AgentTool).filter(AgentTool.ato_agt_id == agent_id).all()
    
    for agent_tool in agent_tools:
        # Get the tool details
        tool = db.query(Tool).filter(Tool.tol_id == getattr(agent_tool, 'ato_tol_id')).first()
        mcp_command = getattr(tool, 'tol_mcp_command', None) if tool else None
        
        # Only include tools with valid MCP commands (not None, not empty string)
        if tool and mcp_command and mcp_command.strip():
            # Get environment variables for this tool
            env_vars = {}
            tool_env_vars = db.query(ToolEnvironmentVariable).filter(
                ToolEnvironmentVariable.tev_tol_id == getattr(tool, 'tol_id')
            ).all()
            
            for env_var in tool_env_vars:
                env_vars[getattr(env_var, 'tev_key')] = getattr(env_var, 'tev_value')
            
            # Parse the MCP command to extract command and args
            command_parts = mcp_command.strip().split()
            if command_parts:
                command = command_parts[0]
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                # Use tool name as server name
                tool_name = getattr(tool, 'tol_name', f"tool_{getattr(tool, 'tol_id')}")
                
                # Create server configuration
                mcp_servers[tool_name] = {
                    "command": command,
                    "args": args,
                    "env": env_vars,
                    "transport": "stdio"
                }
    
    return mcp_servers


# Tool call approval endpoints
@router.get("/chat/sessions/{sessionId}/messages/{messageId}/tool-call", response_model=ToolCallDetail)
def get_tool_call_details(
    sessionId: str,
    messageId: str,
    db: Session = Depends(get_db)
):
    """Get details of a tool call from a tool_input message for approval workflow."""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Find the tool_input message
    db_message = db.query(ChatMessage).filter(
        ChatMessage.msg_id == messageId,
        ChatMessage.msg_cht_id == sessionId,
        ChatMessage.msg_role == "tool_input"
    ).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool input message '{messageId}' not found in session '{sessionId}'"
        )
    
    # Parse tool call details from message content
    msg_content = getattr(db_message, 'msg_content', '')
    try:
        # Expected format: "Tool: {tool_name}, Arguments: {tool_arguments}"
        if msg_content.startswith("Tool: ") and ", Arguments: " in msg_content:
            parts = msg_content.split(", Arguments: ", 1)
            tool_name = parts[0].replace("Tool: ", "")
            tool_arguments_str = parts[1]
            
            # Parse JSON arguments
            try:
                tool_parameters = json.loads(tool_arguments_str)
            except json.JSONDecodeError:
                tool_parameters = {"arguments": tool_arguments_str}
            
            return ToolCallDetail(
                name=tool_name,
                parameters=tool_parameters,
                toolCallId=messageId
            )
        else:
            raise ValueError("Invalid tool call format")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse tool call details: {str(e)}"
        )


@router.post("/chat/sessions/{sessionId}/messages/{messageId}/approve", response_model=ToolCallApprovalResponse)
def approve_tool_call(
    sessionId: str,
    messageId: str,
    approval_request: ToolCallApprovalRequest,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Handle tool call approval, modification, or rejection and continue conversation."""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Find the tool_input message
    db_message = db.query(ChatMessage).filter(
        ChatMessage.msg_id == messageId,
        ChatMessage.msg_cht_id == sessionId,
        ChatMessage.msg_role == "tool_input"
    ).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool input message '{messageId}' not found in session '{sessionId}'"
        )
    
    # Get agent information
    db_agent = db.query(Agent).filter(Agent.agt_id == db_session.cht_agt_id).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent for session not found"
        )
    
    try:
        # Log user approval decision details before processing
        approval_details = {
            "action": approval_request.action,
            "user": username,
            "session_id": sessionId,
            "message_id": messageId,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if approval_request.action == "modify" and approval_request.modifiedParameters:
            approval_details["modified_parameters"] = json.dumps(approval_request.modifiedParameters)
        if approval_request.action == "reject" and approval_request.rejectionReason:
            approval_details["rejection_reason"] = approval_request.rejectionReason
            
        settings.logger.info(f"Tool call approval decision: {json.dumps(approval_details)}")
        
        # Create an approval tracking message in the database
        approval_msg_id = str(uuid.uuid4())
        if approval_request.action == "approve":
            approval_content = f"User {username} approved the tool call"
        elif approval_request.action == "modify":
            modified_params_str = json.dumps(approval_request.modifiedParameters) if approval_request.modifiedParameters else "None"
            approval_content = f"User {username} modified the tool call with parameters: {modified_params_str}"
        else:  # reject
            rejection_reason = approval_request.rejectionReason or "No reason provided"
            approval_content = f"User {username} rejected the tool call. Reason: {rejection_reason}"
        
        db_approval_message = ChatMessage(
            msg_id=approval_msg_id,
            msg_cht_id=sessionId,
            msg_agent_name=db_agent.agt_name,
            msg_role="system",  # System message to track approval decision
            msg_content=f"[APPROVAL DECISION] {approval_content}",
            created_by=username,
            last_updated_by=username
        )
        db.add(db_approval_message)
        db.commit()
        db.refresh(db_approval_message)
        
        if approval_request.action == "reject":
            # Create a rejection response message
            rejection_msg_id = str(uuid.uuid4())
            rejection_reason = approval_request.rejectionReason or "Tool call was rejected by user"
            
            db_rejection_message = ChatMessage(
                msg_id=rejection_msg_id,
                msg_cht_id=sessionId,
                msg_agent_name=db_agent.agt_name,
                msg_role="tool_response",
                msg_content=f"Tool call rejected: {rejection_reason}",
                created_by=username,
                last_updated_by=username
            )
            db.add(db_rejection_message)
            db.commit()
            db.refresh(db_rejection_message)
            
            return ToolCallApprovalResponse(
                success=True,
                message="Tool call rejected successfully",
                continuationId=rejection_msg_id
            )
        
        elif approval_request.action in ["approve", "modify"]:
            # Parse original tool call
            msg_content = getattr(db_message, 'msg_content', '')
            
            if not msg_content.startswith("Tool: ") or ", Arguments: " not in msg_content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid tool call format in message"
                )
            
            parts = msg_content.split(", Arguments: ", 1)
            tool_name = parts[0].replace("Tool: ", "")
            original_arguments_str = parts[1]
            
            # Use modified parameters if provided, otherwise use original
            if approval_request.action == "modify" and approval_request.modifiedParameters:
                tool_parameters = approval_request.modifiedParameters
                # Update the message content with modified parameters
                updated_content = f"Tool: {tool_name}, Arguments: {json.dumps(tool_parameters)}"
                setattr(db_message, 'msg_content', updated_content)
                setattr(db_message, 'last_updated_by', username)
                db.commit()
                db.refresh(db_message)
            else:
                try:
                    tool_parameters = json.loads(original_arguments_str)
                except json.JSONDecodeError:
                    tool_parameters = {"arguments": original_arguments_str}
            
            # Get MCP servers configuration for tool execution
            mcp_servers = get_agent_mcp_servers_config(getattr(db_session, 'cht_agt_id'), db)
            
            # Execute the tool call using the inference module
            tool_execution_result = process_tool_call_approval(
                tool_name=tool_name,
                tool_parameters=tool_parameters,
                action=approval_request.action,
                mcp_servers=mcp_servers,
                modified_parameters=approval_request.modifiedParameters if approval_request.action == "modify" else None
            )
            
            # Create tool response message
            tool_response_id = str(uuid.uuid4())
            
            if tool_execution_result["success"]:
                tool_response_content = tool_execution_result["result"]
            else:
                tool_response_content = f"Tool execution failed: {tool_execution_result.get('error', 'Unknown error')}"
            
            db_tool_response = ChatMessage(
                msg_id=tool_response_id,
                msg_cht_id=sessionId,
                msg_agent_name=db_agent.agt_name,
                msg_role="tool_response",
                msg_content=tool_response_content,
                created_by=username,
                last_updated_by=username
            )
            db.add(db_tool_response)
            db.commit()
            db.refresh(db_tool_response)
            
            # Now continue the conversation by generating the next AI response
            # Get agent's LLM configuration
            db_llm = db.query(LLM).filter(LLM.llc_id == db_agent.agt_llc_id).first()
            if db_llm is None:
                return ToolCallApprovalResponse(
                    success=True,
                    message=f"Tool call {approval_request.action}d successfully, but could not continue conversation (LLM not configured)",
                    continuationId=tool_response_id
                )
            
            # Get all messages for context
            all_messages = db.query(ChatMessage).filter(
                ChatMessage.msg_cht_id == sessionId
            ).order_by(ChatMessage.creation_dt).all()
            
            # Create LangChain message list
            langchain_messages = []
            
            # Add system message if agent has system prompt
            system_prompt = getattr(db_agent, 'agt_system_prompt', None)
            if system_prompt:
                langchain_messages.append(SystemMessage(content=system_prompt))
            
            # Add all messages from the session
            for msg in all_messages:
                msg_role = getattr(msg, 'msg_role')
                msg_content = getattr(msg, 'msg_content')
                
                if msg_role == "user":
                    langchain_messages.append(HumanMessage(content=msg_content))
                elif msg_role == "assistant":
                    langchain_messages.append(AIMessage(content=msg_content))
                elif msg_role == "system":
                    langchain_messages.append(SystemMessage(content=msg_content))
                elif msg_role == "tool_input":
                    # Tool input messages represent the tool call request
                    langchain_messages.append(AIMessage(content=msg_content, additional_kwargs={"tool_calls": []}))
                elif msg_role == "tool_response":
                    langchain_messages.append(ToolMessage(content=msg_content, tool_call_id=getattr(msg, 'msg_id')))
            
            # Get MCP servers configuration for continuation
            mcp_servers = get_agent_mcp_servers_config(getattr(db_session, 'cht_agt_id'), db)
            
            # Continue conversation using the new inference method
            ai_response = continue_conversation_after_tool(
                llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
                model_name=getattr(db_llm, 'llc_model_cd'),
                messages=langchain_messages,
                tool_result=tool_response_content,
                api_key=getattr(db_llm, 'llc_api_key', None),
                base_url=getattr(db_llm, 'llc_endpoint_url', None),
                temperature=0.0,
                proxy_required=getattr(db_llm, 'llc_proxy_required', False),
                streaming=getattr(db_llm, 'llc_streaming', False),
                mcp_servers=mcp_servers,
                message_id=tool_response_id
            )
            
            # Create AI continuation message if we got a response
            continuation_id = tool_response_id
            if ai_response:
                # Handle different response formats
                messages_to_persist = []
                
                # If response has 'messages' key (agent response), extract messages
                if isinstance(ai_response, dict) and 'messages' in ai_response:
                    response_messages = ai_response['messages']
                    # Find new messages (those not in our original input)
                    for msg in response_messages:
                        if not any(orig_msg.id == getattr(msg, 'id', None) for orig_msg in langchain_messages):
                            messages_to_persist.append(msg)
                # If response is a single message object (direct model response)
                elif hasattr(ai_response, 'content'):
                    messages_to_persist.append(ai_response)
                
                # Persist continuation messages
                for msg in messages_to_persist:
                    cont_msg_id = str(uuid.uuid4())
                    continuation_id = cont_msg_id
                    
                    # Determine role from message type and extract content properly
                    if hasattr(msg, '__class__'):
                        msg_type = msg.__class__.__name__
                        if msg_type == 'AIMessage':
                            # Check if this is another tool call
                            additional_kwargs = getattr(msg, 'additional_kwargs', {})
                            tool_calls = additional_kwargs.get('tool_calls', [])
                            msg_content = getattr(msg, 'content', '')
                            
                            if not msg_content and tool_calls:
                                # This is another tool call - record as tool_input message
                                role = 'tool_input'
                                # Extract tool name and arguments from first tool call
                                first_tool_call = tool_calls[0]
                                tool_name = first_tool_call.get('function', {}).get('name', 'unknown_tool')
                                tool_arguments = first_tool_call.get('function', {}).get('arguments', '{}')
                                content = f"Tool: {tool_name}, Arguments: {tool_arguments}"
                            else:
                                # Regular assistant message
                                role = 'assistant'
                                content = extract_message_content(msg)
                        else:
                            role = 'assistant'  # Default fallback
                            content = extract_message_content(msg)
                    else:
                        role = 'assistant'  # Default fallback
                        content = extract_message_content(msg)
                    
                    db_cont_message = ChatMessage(
                        msg_id=cont_msg_id,
                        msg_cht_id=sessionId,
                        msg_agent_name=db_agent.agt_name,
                        msg_role=role,
                        msg_content=content,
                        created_by=username,
                        last_updated_by=username
                    )
                    db.add(db_cont_message)
                    db.commit()
                    db.refresh(db_cont_message)
            
            action_word = "approved" if approval_request.action == "approve" else "modified"
            return ToolCallApprovalResponse(
                success=True,
                message=f"Tool call {action_word} and executed successfully",
                continuationId=continuation_id
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {approval_request.action}"
            )
    
    except (HTTPStatusError, RequestError, TimeoutException) as http_error:
        settings.logger.error(f"HTTP/Network error processing tool call approval: {str(http_error)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(http_error, sessionId, getattr(db_agent, 'agt_name'), username, db)
        error_continuation_id = None
        if error_message:
            error_continuation_id = getattr(error_message, 'msg_id')
        
        return ToolCallApprovalResponse(
            success=False,
            message=f"HTTP/Network error processing tool call approval. An error message has been added to the conversation.",
            continuationId=error_continuation_id
        )
    except Exception as e:
        settings.logger.error(f"Unexpected error processing tool call approval: {str(e)}")
        
        # Create user-friendly error message as assistant response
        error_message = create_error_assistant_message(e, sessionId, getattr(db_agent, 'agt_name'), username, db)
        error_continuation_id = None
        if error_message:
            error_continuation_id = getattr(error_message, 'msg_id')
        
        return ToolCallApprovalResponse(
            success=False,
            message=f"Error processing tool call approval. An error message has been added to the conversation.",
            continuationId=error_continuation_id
        )
