from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AgentBase(BaseModel):
    agentName: str = Field(..., max_length=240, description="Agent name", alias="agt_name")
    agentDescription: Optional[str] = Field(None, max_length=4000, description="Agent description", alias="agt_description")
    agentLlmId: str = Field(..., max_length=80, description="LLM configuration ID", alias="agt_llc_id")
    agentSystemPrompt: Optional[str] = Field(None, max_length=4000, description="System prompt for the agent", alias="agt_system_prompt")

    class Config:
        populate_by_name = True


class AgentCreate(AgentBase):
    agentId: str = Field(..., max_length=80, description="Agent ID", alias="agt_id")


class AgentUpdate(BaseModel):
    agentName: Optional[str] = Field(None, max_length=240, description="Agent name", alias="agt_name")
    agentDescription: Optional[str] = Field(None, max_length=4000, description="Agent description", alias="agt_description")
    agentLlmId: Optional[str] = Field(None, max_length=80, description="LLM configuration ID", alias="agt_llc_id")
    agentSystemPrompt: Optional[str] = Field(None, max_length=4000, description="System prompt for the agent", alias="agt_system_prompt")

    class Config:
        populate_by_name = True


class Agent(AgentBase):
    agentId: str = Field(..., max_length=80, description="Agent ID", alias="agt_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


class AgentToolBase(BaseModel):
    agentId: str = Field(..., max_length=80, description="Agent ID", alias="ato_agt_id")
    toolId: str = Field(..., max_length=80, description="Tool ID", alias="ato_tol_id")

    class Config:
        populate_by_name = True


class AgentToolCreate(AgentToolBase):
    pass


class AgentToolUpdate(BaseModel):
    pass


class AgentTool(AgentToolBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


class AgentKnowledgeBaseBase(BaseModel):
    agentId: str = Field(..., max_length=80, description="Agent ID", alias="akb_agt_id")
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID", alias="akb_knb_id")

    class Config:
        populate_by_name = True


class AgentKnowledgeBaseCreate(AgentKnowledgeBaseBase):
    pass


class AgentKnowledgeBaseUpdate(BaseModel):
    pass


class AgentKnowledgeBase(AgentKnowledgeBaseBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


# Response models with relationships
class AgentWithRelations(Agent):
    agentTools: List[AgentTool] = Field(default_factory=list, description="Associated tools", alias="agent_tools")
    agentKnowledgeBases: List[AgentKnowledgeBase] = Field(default_factory=list, description="Associated knowledge bases", alias="agent_knowledge_bases")
