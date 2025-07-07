from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal


class ChatSessionBase(BaseModel):
    chatName: str = Field(
        ..., 
        max_length=240, 
        description="Chat session name"
    )
    chatAgentId: str = Field(
        ..., 
        max_length=80, 
        description="Agent ID"
    )

    class Config:
        populate_by_name = True


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    chatName: Optional[str] = Field(
        None, 
        max_length=240, 
        description="Chat session name"
    )
    chatAgentId: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Agent ID"
    )

    class Config:
        populate_by_name = True


class ChatSession(ChatSessionBase):
    chatId: str = Field(
        ..., 
        max_length=80, 
        description="Chat session ID"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp"
    )

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            chatId=db_model.cht_id,
            chatName=db_model.cht_name,
            chatAgentId=db_model.cht_agt_id,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )


class ChatMessageBase(BaseModel):
    messageChatId: str = Field(
        ..., 
        max_length=80, 
        description="Chat session ID"
    )
    messageAgentName: str = Field(
        ..., 
        max_length=240, 
        description="Agent name"
    )
    messageRole: Literal["system", "user", "assistant", "tool"] = Field(
        ..., 
        description="Message role: system, user, assistant, or tool"
    )
    messageContent: str = Field(
        ..., 
        max_length=4000,
        description="Message content as text"
    )

    class Config:
        populate_by_name = True


class ChatMessageCreate(BaseModel):
    messageContent: str = Field(
        ..., 
        max_length=4000,
        description="Message content as text"
    )

    class Config:
        populate_by_name = True


class ChatMessageUpdateUser(BaseModel):
    messageContent: str = Field(
        ..., 
        max_length=4000,
        description="Message content as text"
    )

    class Config:
        populate_by_name = True


class ChatMessage(ChatMessageBase):
    messageId: str = Field(
        ..., 
        max_length=80, 
        description="Message ID"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp"
    )

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            messageId=db_model.msg_id,
            messageChatId=db_model.msg_cht_id,
            messageAgentName=db_model.msg_agent_name,
            messageRole=db_model.msg_role,
            messageContent=db_model.msg_content,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )


# Public schemas for clean API responses
class ChatSessionPublic(BaseModel):
    chatId: str = Field(
        ..., 
        max_length=80, 
        description="Chat session ID"
    )
    chatName: str = Field(
        ..., 
        max_length=240, 
        description="Chat session name"
    )
    chatAgentId: str = Field(
        ..., 
        max_length=80, 
        description="Agent ID"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp"
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class ChatMessagePublic(BaseModel):
    messageId: str = Field(
        ..., 
        max_length=80, 
        description="Message ID"
    )
    messageChatId: str = Field(
        ..., 
        max_length=80, 
        description="Chat session ID"
    )
    messageAgentName: str = Field(
        ..., 
        max_length=240, 
        description="Agent name"
    )
    messageRole: Literal["system", "user", "assistant", "tool"] = Field(
        ..., 
        description="Message role: system, user, assistant, or tool"
    )
    messageContent: str = Field(
        ..., 
        max_length=4000,
        description="Message content as text"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp"
    )

    class Config:
        from_attributes = True
        populate_by_name = True


# Response models with relationships
class ChatSessionWithMessages(ChatSessionPublic):
    messages: List[ChatMessagePublic] = Field(default_factory=list, description="Chat messages in chronological order")


class ChatMessageWithSession(ChatMessagePublic):
    chatSession: Optional[ChatSessionPublic] = Field(None, description="Associated chat session", alias="chat_session")


# Special schema for creating chat session with initial message
class ChatSessionCreateWithMessage(BaseModel):
    messageContent: str = Field(
        ..., 
        description="Initial message content"
    )
    chatAgentId: str = Field(
        ..., 
        max_length=80, 
        description="Agent ID"
    )

    class Config:
        populate_by_name = True
