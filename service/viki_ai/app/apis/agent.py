from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.agent import Agent, AgentTool, AgentKnowledgeBase
from app.schemas.agent import (
    Agent as AgentSchema,
    AgentCreate,
    AgentUpdate,
    AgentWithRelations,
    AgentTool as AgentToolSchema,
    AgentToolCreate,
    AgentKnowledgeBase as AgentKnowledgeBaseSchema,
    AgentKnowledgeBaseCreate
)

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


# Agent endpoints
@router.get("/agent", response_model=List[AgentSchema])
def get_agents(
    skip: int = 0,
    limit: int = 100,
    agentName: Optional[str] = None,
    llmId: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all agents with pagination and optional filtering"""
    query = db.query(Agent)
    
    if agentName:
        query = query.filter(Agent.agt_name.ilike(f"%{agentName}%"))
    if llmId:
        query = query.filter(Agent.agt_llc_id == llmId)
    
    agents = query.offset(skip).limit(limit).all()
    return [AgentSchema.from_db_model(agent) for agent in agents]


@router.get("/agent/{agentId}", response_model=AgentSchema)
def get_agent(
    agentId: str,
    db: Session = Depends(get_db)
):
    """Get a specific agent by ID"""
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    return AgentSchema.from_db_model(db_agent)


@router.get("/agent/{agentId}/details", response_model=AgentWithRelations)
def get_agent_with_relations(
    agentId: str,
    db: Session = Depends(get_db)
):
    """Get agent with all related tools and knowledge bases"""
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    # Get agent tools
    agent_tools = db.query(AgentTool).filter(AgentTool.ato_agt_id == agentId).all()
    agent_tool_schemas = [AgentToolSchema.from_db_model(at) for at in agent_tools]
    
    # Get agent knowledge bases
    agent_kbs = db.query(AgentKnowledgeBase).filter(AgentKnowledgeBase.akb_agt_id == agentId).all()
    agent_kb_schemas = [AgentKnowledgeBaseSchema.from_db_model(akb) for akb in agent_kbs]
    
    # Create the response with relations
    agent_dict = AgentSchema.from_db_model(db_agent).model_dump()
    agent_dict["agentTools"] = agent_tool_schemas
    agent_dict["agentKnowledgeBases"] = agent_kb_schemas
    
    return AgentWithRelations(**agent_dict)


@router.post("/agent", response_model=AgentSchema, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_create: AgentCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new agent"""
    # Generate UUID for the agent
    agentId = str(uuid.uuid4())

    # Create agent record
    db_agent = Agent(
        agt_id=agentId,
        agt_name=agent_create.agentName,
        agt_description=agent_create.agentDescription,
        agt_llc_id=agent_create.agentLlmId,
        agt_system_prompt=agent_create.agentSystemPrompt,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return AgentSchema.from_db_model(db_agent)


@router.put("/agent/{agentId}", response_model=AgentSchema)
def update_agent(
    agentId: str,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update an agent"""
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    # Update only provided fields and set last_updated_by
    if agent_update.agentName is not None:
        setattr(db_agent, 'agt_name', agent_update.agentName)
    if agent_update.agentDescription is not None:
        setattr(db_agent, 'agt_description', agent_update.agentDescription)
    if agent_update.agentLlmId is not None:
        setattr(db_agent, 'agt_llc_id', agent_update.agentLlmId)
    if agent_update.agentSystemPrompt is not None:
        setattr(db_agent, 'agt_system_prompt', agent_update.agentSystemPrompt)
    
    setattr(db_agent, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_agent)
    return AgentSchema.from_db_model(db_agent)


@router.delete("/agent/{agentId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agentId: str,
    db: Session = Depends(get_db)
):
    """Delete an agent"""
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    db.delete(db_agent)
    db.commit()


# Agent Tools endpoints
@router.post("/agent/{agentId}/tool", response_model=AgentToolSchema, status_code=status.HTTP_201_CREATED)
def add_tool_to_agent(
    agentId: str,
    agent_tool_create: AgentToolCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Add a tool to an agent"""
    # Check if agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    # Check if association already exists
    existing = db.query(AgentTool).filter(
        AgentTool.ato_agt_id == agentId,
        AgentTool.ato_tol_id == agent_tool_create.toolId
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tool '{agent_tool_create.toolId}' is already associated with agent '{agentId}'"
        )

    # Create agent-tool association
    db_agent_tool = AgentTool(
        ato_agt_id=agentId,
        ato_tol_id=agent_tool_create.toolId,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_agent_tool)
    db.commit()
    db.refresh(db_agent_tool)
    return AgentToolSchema.from_db_model(db_agent_tool)


@router.delete("/agent/{agentId}/tool/{toolId}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tool_from_agent(
    agentId: str,
    toolId: str,
    db: Session = Depends(get_db)
):
    """Remove a tool from an agent"""
    db_agent_tool = db.query(AgentTool).filter(
        AgentTool.ato_agt_id == agentId,
        AgentTool.ato_tol_id == toolId
    ).first()
    
    if db_agent_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association between agent '{agentId}' and tool '{toolId}' not found"
        )
    
    db.delete(db_agent_tool)
    db.commit()


@router.get("/agent/{agentId}/tool", response_model=List[AgentToolSchema])
def get_agent_tools(
    agentId: str,
    db: Session = Depends(get_db)
):
    """Get all tools associated with an agent"""
    # Check if agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    agent_tools = db.query(AgentTool).filter(AgentTool.ato_agt_id == agentId).all()
    return [AgentToolSchema.from_db_model(at) for at in agent_tools]


# Agent Knowledge Base endpoints
@router.post("/agent/{agentId}/knowledge-base", response_model=AgentKnowledgeBaseSchema, status_code=status.HTTP_201_CREATED)
def add_knowledge_base_to_agent(
    agentId: str,
    agent_kb_create: AgentKnowledgeBaseCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Add a knowledge base to an agent"""
    # Check if agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    # Check if association already exists
    existing = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.akb_agt_id == agentId,
        AgentKnowledgeBase.akb_knb_id == agent_kb_create.knowledgeBaseId
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Knowledge base '{agent_kb_create.knowledgeBaseId}' is already associated with agent '{agentId}'"
        )

    # Create agent-knowledge base association
    db_agent_kb = AgentKnowledgeBase(
        akb_agt_id=agentId,
        akb_knb_id=agent_kb_create.knowledgeBaseId,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_agent_kb)
    db.commit()
    db.refresh(db_agent_kb)
    return AgentKnowledgeBaseSchema.from_db_model(db_agent_kb)


@router.delete("/agent/{agentId}/knowledge-base/{knowledgeBaseId}", status_code=status.HTTP_204_NO_CONTENT)
def remove_knowledge_base_from_agent(
    agentId: str,
    knowledgeBaseId: str,
    db: Session = Depends(get_db)
):
    """Remove a knowledge base from an agent"""
    db_agent_kb = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.akb_agt_id == agentId,
        AgentKnowledgeBase.akb_knb_id == knowledgeBaseId
    ).first()
    
    if db_agent_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association between agent '{agentId}' and knowledge base '{knowledgeBaseId}' not found"
        )
    
    db.delete(db_agent_kb)
    db.commit()


@router.get("/agent/{agentId}/knowledge-base", response_model=List[AgentKnowledgeBaseSchema])
def get_agent_knowledge_bases(
    agentId: str,
    db: Session = Depends(get_db)
):
    """Get all knowledge bases associated with an agent"""
    # Check if agent exists
    db_agent = db.query(Agent).filter(Agent.agt_id == agentId).first()
    if db_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agentId}' not found"
        )
    
    agent_kbs = db.query(AgentKnowledgeBase).filter(AgentKnowledgeBase.akb_agt_id == agentId).all()
    return [AgentKnowledgeBaseSchema.from_db_model(akb) for akb in agent_kbs]


# Search endpoints
@router.get("/agent/search/by-llm/{llmId}", response_model=List[AgentSchema])
def get_agents_by_llm(
    llmId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all agents using a specific LLM"""
    agents = db.query(Agent).filter(
        Agent.agt_llc_id == llmId
    ).offset(skip).limit(limit).all()
    return [AgentSchema.from_db_model(agent) for agent in agents]


@router.get("/agent/search/by-name/{agentName}", response_model=List[AgentSchema])
def search_agents_by_name(
    agentName: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search agents by name (case-insensitive partial match)"""
    agents = db.query(Agent).filter(
        Agent.agt_name.ilike(f"%{agentName}%")
    ).offset(skip).limit(limit).all()
    return [AgentSchema.from_db_model(agent) for agent in agents]
