from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AgentBase(BaseModel):
    agentName: str = Field(..., max_length=240, description="Agent name")
    agentDescription: Optional[str] = Field(None, max_length=4000, description="Agent description")
    agentLlmId: str = Field(..., max_length=80, description="LLM configuration ID")
    agentSystemPrompt: Optional[str] = Field(None, max_length=4000, description="System prompt for the agent")


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    agentName: Optional[str] = Field(None, max_length=240, description="Agent name")
    agentDescription: Optional[str] = Field(None, max_length=4000, description="Agent description")
    agentLlmId: Optional[str] = Field(None, max_length=80, description="LLM configuration ID")
    agentSystemPrompt: Optional[str] = Field(None, max_length=4000, description="System prompt for the agent")


class Agent(AgentBase):
    agentId: str = Field(..., max_length=80, description="Agent ID")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            agentId=db_model.agt_id,
            agentName=db_model.agt_name,
            agentDescription=db_model.agt_description,
            agentLlmId=db_model.agt_llc_id,
            agentSystemPrompt=db_model.agt_system_prompt,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )        

class AgentToolCreate(BaseModel):
    toolId: str = Field(..., max_length=80, description="Tool ID")


class AgentTool(BaseModel):
    agentId: str = Field(..., max_length=80, description="Agent ID")
    toolId: str = Field(..., max_length=80, description="Tool ID")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            agentId=db_model.ato_agt_id,
            toolId=db_model.ato_tol_id,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
        

class AgentKnowledgeBaseCreate(BaseModel):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID")


class AgentKnowledgeBase(BaseModel):
    agentId: str = Field(..., max_length=80, description="Agent ID")
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            agentId=db_model.akb_agt_id,
            knowledgeBaseId=db_model.akb_knb_id,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
        

# Response models with relationships
class AgentWithRelations(Agent):
    agentTools: List[AgentTool] = Field(default_factory=list, description="Associated tools")
    agentKnowledgeBases: List[AgentKnowledgeBase] = Field(default_factory=list, description="Associated knowledge bases")
