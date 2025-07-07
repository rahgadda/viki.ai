from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.agent import Agent
from app.models.llm import LLM
from app.schemas.chat import (
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
    ChatSessionUpdate,
    ChatMessageCreate,
    ChatMessageUpdateUser,
    ChatSessionCreateWithMessage,
    ChatSessionPublic,
    ChatMessagePublic,
    ChatSessionWithMessages
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.utils.inference import generate_llm_response

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


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
        
        # Generate LLM response
        ai_response = generate_llm_response(
            llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
            model_name=getattr(db_llm, 'llc_model_cd'),
            api_key=getattr(db_llm, 'llc_api_key', None),
            base_url=getattr(db_llm, 'llc_endpoint_url', None),
            temperature=0.0,
            proxy_required=getattr(db_llm, 'llc_proxy_required', False),
            streaming=getattr(db_llm, 'llc_streaming', False),
            messages=langchain_messages
        )
        
        # Create AI response message if we got a response
        if ai_response and hasattr(ai_response, 'content'):
            ai_message_id = str(uuid.uuid4())
            db_ai_message = ChatMessage(
                msg_id=ai_message_id,
                msg_cht_id=session_id,
                msg_agent_name=db_agent.agt_name,
                msg_role="assistant",
                msg_content=ai_response.content,
                created_by=username,
                last_updated_by=username
            )
            db.add(db_ai_message)
            db.commit()
            db.refresh(db_ai_message)
            
            # Convert both messages to schemas
            message_data = ChatMessageSchema.from_db_model(db_message)
            ai_message_data = ChatMessageSchema.from_db_model(db_ai_message)
            
            # Convert to public schemas for response
            session_data = ChatSessionSchema.from_db_model(db_session)
            session_public = ChatSessionPublic(**session_data.dict())
            message_public = ChatMessagePublic(**message_data.dict())
            ai_message_public = ChatMessagePublic(**ai_message_data.dict())
            
            return ChatSessionWithMessages(
                **session_public.dict(),
                messages=[message_public, ai_message_public]
            )
    
    except Exception as e:
        settings.logger.error(f"Error generating LLM response: {str(e)}")
        # Continue without AI response if LLM fails
    
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
                elif msg_role == "tool":
                    langchain_messages.append(ToolMessage(content=msg_content, tool_call_id=""))
            
            # Generate LLM response
            ai_response = generate_llm_response(
                llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
                model_name=getattr(db_llm, 'llc_model_cd'),
                api_key=getattr(db_llm, 'llc_api_key', None),
                base_url=getattr(db_llm, 'llc_endpoint_url', None),
                temperature=0.0,
                proxy_required=getattr(db_llm, 'llc_proxy_required', False),
                streaming=getattr(db_llm, 'llc_streaming', False),
                messages=langchain_messages
            )
            
            # Create AI response message if we got a response
            if ai_response and hasattr(ai_response, 'content'):
                ai_message_id = str(uuid.uuid4())
                db_ai_message = ChatMessage(
                    msg_id=ai_message_id,
                    msg_cht_id=sessionId,
                    msg_agent_name=db_agent.agt_name,
                    msg_role="assistant",
                    msg_content=ai_response.content,
                    created_by=username,
                    last_updated_by=username
                )
                db.add(db_ai_message)
                db.commit()
                db.refresh(db_ai_message)
                
                # Add AI message to the response
                created_messages.append(ChatMessageSchema.from_db_model(db_ai_message))
    
    except Exception as e:
        settings.logger.error(f"Error generating LLM response: {str(e)}")
        # Continue without AI response if LLM fails
    
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
            elif msg_role == "tool":
                langchain_messages.append(ToolMessage(content=msg_content, tool_call_id=""))
        
        # Generate LLM response
        ai_response = generate_llm_response(
            llm_provider=getattr(db_llm, 'llc_provider_type_cd'),
            model_name=getattr(db_llm, 'llc_model_cd'),
            api_key=getattr(db_llm, 'llc_api_key', None),
            base_url=getattr(db_llm, 'llc_endpoint_url', None),
            temperature=0.0,
            proxy_required=getattr(db_llm, 'llc_proxy_required', False),
            streaming=getattr(db_llm, 'llc_streaming', False),
            messages=langchain_messages
        )
        
        # Create AI response message if we got a response
        if ai_response and hasattr(ai_response, 'content'):
            ai_message_id = str(uuid.uuid4())
            db_ai_message = ChatMessage(
                msg_id=ai_message_id,
                msg_cht_id=sessionId,
                msg_agent_name=db_agent.agt_name,
                msg_role="assistant",
                msg_content=ai_response.content,
                created_by=username,
                last_updated_by=username
            )
            db.add(db_ai_message)
            db.commit()
            db.refresh(db_ai_message)
            
            # Add AI message to the response
            updated_messages.append(ChatMessageSchema.from_db_model(db_ai_message))
    
    except Exception as e:
        settings.logger.error(f"Error generating LLM response: {str(e)}")
        # Continue without AI response if LLM fails
    
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
