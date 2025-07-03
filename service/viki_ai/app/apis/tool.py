from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.tool import Tool, ToolEnvironmentVariable, ToolResource
from app.schemas.tool import (
    Tool as ToolSchema,
    ToolCreate,
    ToolUpdate,
    ToolWithDetails,
    ToolEnvironmentVariable as ToolEnvironmentVariableSchema,
    ToolEnvironmentVariableCreate,
    ToolEnvironmentVariableUpdate,
    ToolResource as ToolResourceSchema
)

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


# Tool endpoints
@router.get("/tool", response_model=List[ToolSchema])
def get_tools(
    skip: int = 0,
    limit: int = 100,
    toolName: Optional[str] = None,
    toolMcpCommand: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tool configurations with pagination and optional filtering"""
    query = db.query(Tool)
    
    if toolName:
        query = query.filter(Tool.tol_name.ilike(f"%{toolName}%"))
    if toolMcpCommand:
        query = query.filter(Tool.tol_mcp_command.ilike(f"%{toolMcpCommand}%"))
    
    tools = query.offset(skip).limit(limit).all()
    return tools


@router.get("/tool/{toolId}", response_model=ToolWithDetails)
def get_tool(
    toolId: str,
    db: Session = Depends(get_db)
):
    """Get a specific tool configuration by ID with environment variables and resources"""
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    return db_tool


@router.post("/tool", response_model=ToolSchema, status_code=status.HTTP_201_CREATED)
def create_tool(
    tool_create: ToolCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new tool configuration"""
    # Check if tool ID already exists
    existing_tool = db.query(Tool).filter(Tool.tol_id == tool_create.toolId).first()
    if existing_tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool with ID '{tool_create.toolId}' already exists"
        )

    # Create tool record using schema data with aliases
    create_data = tool_create.dict(by_alias=True)
    create_data['created_by'] = username
    create_data['last_updated_by'] = username
    
    db_tool = Tool(**create_data)
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool


@router.put("/tool/{toolId}", response_model=ToolSchema)
def update_tool(
    toolId: str,
    tool_update: ToolUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a tool configuration"""
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    # Update only provided fields and set last_updated_by
    update_data = tool_update.dict(exclude_unset=True, by_alias=True)
    update_data['last_updated_by'] = username
    
    for field, value in update_data.items():
        setattr(db_tool, field, value)
    
    db.commit()
    db.refresh(db_tool)
    return db_tool


@router.delete("/tool/{toolId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool(
    toolId: str,
    db: Session = Depends(get_db)
):
    """Delete a tool configuration"""
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    db.delete(db_tool)
    db.commit()


# Tool Environment Variable endpoints
@router.get("/tool/{toolId}/environmentVariables", response_model=List[ToolEnvironmentVariableSchema])
def get_tool_environment_variables(
    toolId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all environment variables for a specific tool"""
    # First check if tool exists
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    env_vars = db.query(ToolEnvironmentVariable).filter(
        ToolEnvironmentVariable.tev_tol_id == toolId
    ).offset(skip).limit(limit).all()
    return env_vars


@router.get("/tool/{toolId}/environmentVariables/{envVarKey}", response_model=ToolEnvironmentVariableSchema)
def get_tool_environment_variable(
    toolId: str,
    envVarKey: str,
    db: Session = Depends(get_db)
):
    """Get a specific environment variable for a tool"""
    db_env_var = db.query(ToolEnvironmentVariable).filter(
        ToolEnvironmentVariable.tev_tol_id == toolId,
        ToolEnvironmentVariable.tev_key == envVarKey
    ).first()
    if db_env_var is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment variable '{envVarKey}' not found for tool '{toolId}'"
        )
    return db_env_var


@router.post("/tool/{toolId}/environmentVariables", response_model=ToolEnvironmentVariableSchema, status_code=status.HTTP_201_CREATED)
def create_tool_environment_variable(
    toolId: str,
    env_var_create: ToolEnvironmentVariableCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new environment variable for a tool"""
    # Check if tool exists
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    # Check if environment variable already exists
    existing_env_var = db.query(ToolEnvironmentVariable).filter(
        ToolEnvironmentVariable.tev_tol_id == toolId,
        ToolEnvironmentVariable.tev_key == env_var_create.envVarKey
    ).first()
    if existing_env_var:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Environment variable '{env_var_create.envVarKey}' already exists for tool '{toolId}'"
        )

    # Create environment variable record
    create_data = env_var_create.dict(by_alias=True)
    create_data['tev_tol_id'] = toolId  # Ensure toolId is set correctly
    create_data['created_by'] = username
    create_data['last_updated_by'] = username
    
    db_env_var = ToolEnvironmentVariable(**create_data)
    db.add(db_env_var)
    db.commit()
    db.refresh(db_env_var)
    return db_env_var


@router.put("/tool/{toolId}/environmentVariables/{envVarKey}", response_model=ToolEnvironmentVariableSchema)
def update_tool_environment_variable(
    toolId: str,
    envVarKey: str,
    env_var_update: ToolEnvironmentVariableUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update an environment variable for a tool"""
    db_env_var = db.query(ToolEnvironmentVariable).filter(
        ToolEnvironmentVariable.tev_tol_id == toolId,
        ToolEnvironmentVariable.tev_key == envVarKey
    ).first()
    if db_env_var is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment variable '{envVarKey}' not found for tool '{toolId}'"
        )
    
    # Update only provided fields and set last_updated_by
    update_data = env_var_update.dict(exclude_unset=True, by_alias=True)
    update_data['last_updated_by'] = username
    
    for field, value in update_data.items():
        setattr(db_env_var, field, value)
    
    db.commit()
    db.refresh(db_env_var)
    return db_env_var


@router.delete("/tool/{toolId}/environmentVariables/{envVarKey}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool_environment_variable(
    toolId: str,
    envVarKey: str,
    db: Session = Depends(get_db)
):
    """Delete an environment variable for a tool"""
    db_env_var = db.query(ToolEnvironmentVariable).filter(
        ToolEnvironmentVariable.tev_tol_id == toolId,
        ToolEnvironmentVariable.tev_key == envVarKey
    ).first()
    if db_env_var is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment variable '{envVarKey}' not found for tool '{toolId}'"
        )
    
    db.delete(db_env_var)
    db.commit()


# Tool Resource endpoints
@router.get("/tool/{toolId}/resources", response_model=List[ToolResourceSchema])
def get_tool_resources(
    toolId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all resources for a specific tool"""
    # First check if tool exists
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    resources = db.query(ToolResource).filter(
        ToolResource.tre_tol_id == toolId
    ).offset(skip).limit(limit).all()
    return resources


@router.get("/tool/{toolId}/resources/{resourceName}", response_model=ToolResourceSchema)
def get_tool_resource(
    toolId: str,
    resourceName: str,
    db: Session = Depends(get_db)
):
    """Get a specific resource for a tool"""
    db_resource = db.query(ToolResource).filter(
        ToolResource.tre_tol_id == toolId,
        ToolResource.tre_resource_name == resourceName
    ).first()
    if db_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource '{resourceName}' not found for tool '{toolId}'"
        )
    return db_resource
