from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.agent import Agent
from app.schemas.chat import (
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatSessionCreateWithMessage,
    ChatSessionPublic,
    ChatMessagePublic,
    ChatSessionWithMessages,
    ChatMessageWithSession
)

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
    
    # Create initial message with USER role
    db_message = ChatMessage(
        msg_id=message_id,
        msg_cht_id=session_id,
        msg_agent_name=db_agent.agt_name,
        msg_role="USER",
        msg_content=chat_create.messageContent,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_message)
    
    db.commit()
    db.refresh(db_session)
    db.refresh(db_message)
    
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


@router.post("/chat/sessions/simple", response_model=ChatSessionSchema, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    chat_create: ChatSessionCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new empty chat session"""
    # Verify agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == chat_create.chatAgentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{chat_create.chatAgentId}' not found"
        )
    
    # Generate UUID for the chat session
    session_id = str(uuid.uuid4())
    
    # Create chat session
    db_session = ChatSession(
        cht_id=session_id,
        cht_name=chat_create.chatName,
        cht_agt_id=chat_create.chatAgentId,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return ChatSessionSchema.from_db_model(db_session)


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


# Chat Message endpoints
@router.get("/chat/messages", response_model=List[ChatMessageSchema])
def get_chat_messages(
    sessionId: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get chat messages with pagination and optional filtering"""
    query = db.query(ChatMessage)
    
    if sessionId:
        query = query.filter(ChatMessage.msg_cht_id == sessionId)
    if role:
        if role not in ["USER", "AI"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be either 'USER' or 'AI'"
            )
        query = query.filter(ChatMessage.msg_role == role)
    
    # Order by creation date
    query = query.order_by(ChatMessage.creation_dt)
    
    messages = query.offset(skip).limit(limit).all()
    return [ChatMessageSchema.from_db_model(message) for message in messages]


@router.get("/chat/messages/{messageId}", response_model=ChatMessageWithSession)
def get_chat_message(
    messageId: str,
    db: Session = Depends(get_db)
):
    """Get a specific chat message by ID with session info"""
    db_message = db.query(ChatMessage).filter(ChatMessage.msg_id == messageId).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat message '{messageId}' not found"
        )
    
    # Convert to schema with session
    message_data = ChatMessageSchema.from_db_model(db_message)
    session_data = ChatSessionSchema.from_db_model(db_message.chat_session)
    
    # Convert to public schemas for response
    message_public = ChatMessagePublic(**message_data.dict())
    session_public = ChatSessionPublic(**session_data.dict())
    
    return ChatMessageWithSession(
        **message_public.dict(),
        chat_session=session_public
    )


@router.post("/chat/sessions/{sessionId}/messages", response_model=ChatMessageSchema, status_code=status.HTTP_201_CREATED)
def create_chat_message(
    sessionId: str,
    message_create: ChatMessageCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Add a new message to an existing chat session"""
    # Verify session exists
    db_session = db.query(ChatSession).filter(ChatSession.cht_id == sessionId).first()
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{sessionId}' not found"
        )
    
    # Generate UUID for the message
    message_id = str(uuid.uuid4())
    
    # Create message
    db_message = ChatMessage(
        msg_id=message_id,
        msg_cht_id=sessionId,
        msg_agent_name=message_create.messageAgentName,
        msg_role=message_create.messageRole,
        msg_content=message_create.messageContent,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return ChatMessageSchema.from_db_model(db_message)


@router.put("/chat/messages/{messageId}", response_model=ChatMessageSchema)
def update_chat_message(
    messageId: str,
    message_update: ChatMessageUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a chat message"""
    db_message = db.query(ChatMessage).filter(ChatMessage.msg_id == messageId).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat message '{messageId}' not found"
        )
    
    # Update only provided fields
    if message_update.messageAgentName is not None:
        setattr(db_message, 'msg_agent_name', message_update.messageAgentName)
    if message_update.messageRole is not None:
        setattr(db_message, 'msg_role', message_update.messageRole)
    if message_update.messageContent is not None:
        setattr(db_message, 'msg_content', message_update.messageContent)
    
    setattr(db_message, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_message)
    return ChatMessageSchema.from_db_model(db_message)


@router.delete("/chat/messages/{messageId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_message(
    messageId: str,
    db: Session = Depends(get_db)
):
    """Delete a chat message"""
    db_message = db.query(ChatMessage).filter(ChatMessage.msg_id == messageId).first()
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat message '{messageId}' not found"
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
