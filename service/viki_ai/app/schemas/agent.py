from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AgentBase(BaseModel):
    agt_name: str = Field(..., max_length=240, description="Agent name")
    agt_description: Optional[str] = Field(None, max_length=4000, description="Agent description")
    agt_llc_id: str = Field(..., max_length=80, description="LLM configuration ID")
    agt_system_prompt: Optional[str] = Field(None, max_length=4000, description="System prompt for the agent")


class AgentCreate(AgentBase):
    agt_id: str = Field(..., max_length=80, description="Agent ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class AgentUpdate(BaseModel):
    agt_name: Optional[str] = Field(None, max_length=240, description="Agent name")
    agt_description: Optional[str] = Field(None, max_length=4000, description="Agent description")
    agt_llc_id: Optional[str] = Field(None, max_length=80, description="LLM configuration ID")
    agt_system_prompt: Optional[str] = Field(None, max_length=4000, description="System prompt for the agent")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class Agent(AgentBase):
    agt_id: str = Field(..., max_length=80, description="Agent ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        


class AgentToolBase(BaseModel):
    ato_agt_id: str = Field(..., max_length=80, description="Agent ID")
    ato_tol_id: str = Field(..., max_length=80, description="Tool ID")


class AgentToolCreate(AgentToolBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class AgentToolUpdate(BaseModel):
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class AgentTool(AgentToolBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        


class AgentKnowledgeBaseBase(BaseModel):
    akb_agt_id: str = Field(..., max_length=80, description="Agent ID")
    akb_knb_id: str = Field(..., max_length=80, description="Knowledge base ID")


class AgentKnowledgeBaseCreate(AgentKnowledgeBaseBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class AgentKnowledgeBaseUpdate(BaseModel):
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class AgentKnowledgeBase(AgentKnowledgeBaseBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        


# Response models with relationships
class AgentWithRelations(Agent):
    agent_tools: List[AgentTool] = Field(default_factory=list, description="Associated tools")
    agent_knowledge_bases: List[AgentKnowledgeBase] = Field(default_factory=list, description="Associated knowledge bases")
