from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal


class ChatSessionBase(BaseModel):
    cht_name: str = Field(..., max_length=240, description="Chat session name")
    cht_agt_id: str = Field(..., max_length=80, description="Agent ID")


class ChatSessionCreate(ChatSessionBase):
    cht_id: str = Field(..., max_length=80, description="Chat session ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class ChatSessionUpdate(BaseModel):
    cht_name: Optional[str] = Field(None, max_length=240, description="Chat session name")
    cht_agt_id: Optional[str] = Field(None, max_length=80, description="Agent ID")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class ChatSession(ChatSessionBase):
    cht_id: str = Field(..., max_length=80, description="Chat session ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    msg_cht_id: str = Field(..., max_length=80, description="Chat session ID")
    msg_agent_name: str = Field(..., max_length=240, description="Agent name")
    msg_role: Literal["USER", "AI"] = Field(..., description="Message role: USER or AI")
    msg_content: Dict[str, Any] = Field(..., description="Message content as JSON")


class ChatMessageCreate(ChatMessageBase):
    msg_id: str = Field(..., max_length=80, description="Message ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class ChatMessageUpdate(BaseModel):
    msg_agent_name: Optional[str] = Field(None, max_length=240, description="Agent name")
    msg_role: Optional[Literal["USER", "AI"]] = Field(None, description="Message role: USER or AI")
    msg_content: Optional[Dict[str, Any]] = Field(None, description="Message content as JSON")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class ChatMessage(ChatMessageBase):
    msg_id: str = Field(..., max_length=80, description="Message ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True


# Response models with relationships
class ChatSessionWithMessages(ChatSession):
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages in chronological order")


class ChatMessageWithSession(ChatMessage):
    chat_session: Optional[ChatSession] = Field(None, description="Associated chat session")
