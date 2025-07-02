from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal


class ChatSessionBase(BaseModel):
    chatName: str = Field(..., max_length=240, description="Chat session name", alias="cht_name")
    chatAgentId: str = Field(..., max_length=80, description="Agent ID", alias="cht_agt_id")

    class Config:
        populate_by_name = True


class ChatSessionCreate(ChatSessionBase):
    chatId: str = Field(..., max_length=80, description="Chat session ID", alias="cht_id")


class ChatSessionUpdate(BaseModel):
    chatName: Optional[str] = Field(None, max_length=240, description="Chat session name", alias="cht_name")
    chatAgentId: Optional[str] = Field(None, max_length=80, description="Agent ID", alias="cht_agt_id")

    class Config:
        populate_by_name = True


class ChatSession(ChatSessionBase):
    chatId: str = Field(..., max_length=80, description="Chat session ID", alias="cht_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ChatMessageBase(BaseModel):
    messageChatId: str = Field(..., max_length=80, description="Chat session ID", alias="msg_cht_id")
    messageAgentName: str = Field(..., max_length=240, description="Agent name", alias="msg_agent_name")
    messageRole: Literal["USER", "AI"] = Field(..., description="Message role: USER or AI", alias="msg_role")
    messageContent: Dict[str, Any] = Field(..., description="Message content as JSON", alias="msg_content")

    class Config:
        populate_by_name = True


class ChatMessageCreate(ChatMessageBase):
    messageId: str = Field(..., max_length=80, description="Message ID", alias="msg_id")


class ChatMessageUpdate(BaseModel):
    messageAgentName: Optional[str] = Field(None, max_length=240, description="Agent name", alias="msg_agent_name")
    messageRole: Optional[Literal["USER", "AI"]] = Field(None, description="Message role: USER or AI", alias="msg_role")
    messageContent: Optional[Dict[str, Any]] = Field(None, description="Message content as JSON", alias="msg_content")

    class Config:
        populate_by_name = True


class ChatMessage(ChatMessageBase):
    messageId: str = Field(..., max_length=80, description="Message ID", alias="msg_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True


# Response models with relationships
class ChatSessionWithMessages(ChatSession):
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages in chronological order")


class ChatMessageWithSession(ChatMessage):
    chatSession: Optional[ChatSession] = Field(None, description="Associated chat session", alias="chat_session")
