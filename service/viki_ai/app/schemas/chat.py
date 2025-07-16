from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any


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
    messageRole: Literal["system", "user", "assistant", "tool_input", "tool_response"] = Field(
        ..., 
        description="Message role: system, user, assistant, tool_input, or tool_response"
    )
    messageContent: str = Field(
        ..., 
        description="Message content as text"
    )

    class Config:
        populate_by_name = True


class ChatMessageCreate(BaseModel):
    messageContent: str = Field(
        ..., 
        description="Message content as text"
    )

    class Config:
        populate_by_name = True


class ChatMessageUpdateUser(BaseModel):
    messageContent: str = Field(
        ..., 
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
    messageRole: Literal["system", "user", "assistant", "tool_input", "tool_response"] = Field(
        ..., 
        description="Message role: system, user, assistant, tool_input, or tool_response"
    )
    messageContent: str = Field(
        ..., 
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


# Tool call approval schemas
class ToolCallDetail(BaseModel):
    name: str = Field(..., description="Name of the tool to be called")
    parameters: Dict[str, Any] = Field(..., description="Parameters for the tool call")
    toolCallId: str = Field(..., description="Unique identifier for this tool call")


class ToolCallApprovalRequest(BaseModel):
    action: Literal["approve", "modify", "reject"] = Field(
        ..., 
        description="Action to take on the tool call: approve, modify, or reject"
    )
    modifiedParameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Modified parameters if action is 'modify'"
    )
    rejectionReason: Optional[str] = Field(
        None, 
        description="Reason for rejection if action is 'reject'"
    )

    class Config:
        populate_by_name = True


class ToolCallApprovalResponse(BaseModel):
    success: bool = Field(..., description="Whether the approval action was successful")
    message: str = Field(..., description="Status message")
    continuationId: Optional[str] = Field(
        None, 
        description="ID for continuing the conversation after approval"
    )

    class Config:
        populate_by_name = True
