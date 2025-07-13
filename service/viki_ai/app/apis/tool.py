from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import asyncio
from typing import List, Optional, Dict
import uuid
import logging
from app.utils.database import get_db
from app.utils.config import settings
from app.utils.mcpTool import test_mcp_configuration
from app.models.tool import Tool, ToolEnvironmentVariable, ToolResource
from app.schemas.tool import (
    Tool as ToolSchema,
    ToolCreate,
    ToolUpdate,
    ToolWithDetails,
    ToolEnvironmentVariable as ToolEnvironmentVariableSchema,
    ToolEnvironmentVariableBulkItem,
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
@router.get("/tools", response_model=List[ToolSchema])
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
    return [ToolSchema.from_db_model(tool) for tool in tools]


@router.get("/tools/{toolId}", response_model=ToolSchema)
def get_tool(
    toolId: str,
    db: Session = Depends(get_db)
):
    """Get a specific tool configuration by ID"""
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    return ToolSchema.from_db_model(db_tool)


@router.post("/tools", response_model=ToolSchema, status_code=status.HTTP_201_CREATED)
def create_tool(
    tool_create: ToolCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new tool configuration"""
    # Generate a new UUID for the tool
    tool_id = str(uuid.uuid4())
    
    # Create tool record - manually map camelCase schema fields to snake_case DB columns
    db_tool = Tool(
        tol_id=tool_id,
        tol_name=tool_create.toolName,
        tol_description=tool_create.toolDescription,
        tol_mcp_command=tool_create.toolMcpCommand,
        tol_mcp_function_count=0,  # Auto-populated by populate resources endpoint
        tol_proxy_required=tool_create.toolProxyRequired,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return ToolSchema.from_db_model(db_tool)


@router.put("/tools/{toolId}", response_model=ToolSchema)
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
    if tool_update.toolName is not None:
        setattr(db_tool, 'tol_name', tool_update.toolName)
    if tool_update.toolDescription is not None:
        setattr(db_tool, 'tol_description', tool_update.toolDescription)
    if tool_update.toolMcpCommand is not None:
        setattr(db_tool, 'tol_mcp_command', tool_update.toolMcpCommand)
    if tool_update.toolProxyRequired is not None:
        setattr(db_tool, 'tol_proxy_required', tool_update.toolProxyRequired)
    
    setattr(db_tool, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_tool)
    return ToolSchema.from_db_model(db_tool)


@router.delete("/tools/{toolId}", status_code=status.HTTP_204_NO_CONTENT)
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
@router.get("/tools/{toolId}/environmentVariables", response_model=List[ToolEnvironmentVariableSchema])
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
    return [ToolEnvironmentVariableSchema.from_db_model(env_var) for env_var in env_vars]


@router.get("/tools/{toolId}/environmentVariables/{envVarKey}", response_model=ToolEnvironmentVariableSchema)
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
    return ToolEnvironmentVariableSchema.from_db_model(db_env_var)


@router.post("/tools/{toolId}/environmentVariables", response_model=List[ToolEnvironmentVariableSchema], status_code=status.HTTP_201_CREATED)
def create_tool_environment_variables(
    toolId: str,
    env_vars_create: List[ToolEnvironmentVariableBulkItem],
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create multiple environment variables for a tool"""
    # Check if tool exists
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    created_env_vars = []
    
    for env_var_item in env_vars_create:
        # Check if environment variable already exists
        existing_env_var = db.query(ToolEnvironmentVariable).filter(
            ToolEnvironmentVariable.tev_tol_id == toolId,
            ToolEnvironmentVariable.tev_key == env_var_item.envVarKey
        ).first()
        if existing_env_var:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment variable '{env_var_item.envVarKey}' already exists for tool '{toolId}'"
            )

        # Create environment variable record
        db_env_var = ToolEnvironmentVariable(
            tev_tol_id=toolId,
            tev_key=env_var_item.envVarKey,
            tev_value=env_var_item.envVarValue,
            created_by=username,
            last_updated_by=username
        )
        db.add(db_env_var)
        created_env_vars.append(db_env_var)
    
    db.commit()
    
    # Refresh all created environment variables
    for env_var in created_env_vars:
        db.refresh(env_var)
    
    return [ToolEnvironmentVariableSchema.from_db_model(env_var) for env_var in created_env_vars]


@router.put("/tools/{toolId}/environmentVariables/{envVarKey}", response_model=ToolEnvironmentVariableSchema)
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
    return ToolEnvironmentVariableSchema.from_db_model(db_env_var)


@router.delete("/tools/{toolId}/environmentVariables/{envVarKey}", status_code=status.HTTP_204_NO_CONTENT)
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
@router.get("/tools/{toolId}/resources", response_model=List[ToolResourceSchema])
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
    return [ToolResourceSchema.from_db_model(resource) for resource in resources]


@router.get("/tools/{toolId}/resources/{resourceName}", response_model=ToolResourceSchema)
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
    return ToolResourceSchema.from_db_model(db_resource)


@router.post("/tools/{toolId}/resources", response_model=List[ToolResourceSchema])
def populate_tool_resources(
    toolId: str,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """
    Populate tool resources by connecting to MCP server and discovering available resources
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting resource population for tool: {toolId}")
    
    # Check if tool exists
    db_tool = db.query(Tool).filter(Tool.tol_id == toolId).first()
    if db_tool is None:
        logger.error(f"Tool not found: {toolId}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool configuration '{toolId}' not found"
        )
    
    logger.info(f"Found tool: {db_tool.tol_name}, command: {db_tool.tol_mcp_command}")
    
    # Get environment variables for the tool
    env_vars = {}
    tool_env_vars = db.query(ToolEnvironmentVariable).filter(
        ToolEnvironmentVariable.tev_tol_id == toolId
    ).all()
    
    for env_var in tool_env_vars:
        env_vars[env_var.tev_key] = env_var.tev_value
    
    logger.info(f"Found {len(env_vars)} environment variables")
    
    # Test MCP configuration and get resources
    try:
        logger.info(f"Testing MCP configuration with command: {db_tool.tol_mcp_command}")
        success, function_count, error_message, functions = asyncio.run(test_mcp_configuration(
            str(db_tool.tol_mcp_command), 
            env_vars
        ))

        if success:
            logger.info(f"Successfully retrieved {function_count} functions from MCP server")
            
            # Clear existing resources and add new ones
            logger.info(f"Clearing existing resources for tool {toolId}")
            db.query(ToolResource).filter(ToolResource.tre_tol_id == toolId).delete()
            
            created_resources = []
            
            # Save or update tool resources
            if functions:
                for func in functions:
                    db_resource = ToolResource(
                        tre_tol_id=toolId,
                        tre_resource_name=func.get("name", ""),
                        tre_resource_description=func.get("description", ""),
                        created_by=username,
                        last_updated_by=username
                    )
                    db.add(db_resource)
                    created_resources.append(db_resource)
                
                logger.info(f"Added {len(functions)} resources for tool {toolId}")
            
            # Update tool function count
            logger.info(f"Updating tool function count to {function_count}")
            setattr(db_tool, 'tol_mcp_function_count', function_count)
            setattr(db_tool, 'last_updated_by', username)
            
            db.commit()
            logger.info(f"Successfully committed {len(created_resources)} resources to database")
            
            # Refresh all created resources
            for resource in created_resources:
                db.refresh(resource)
            
            logger.info(f"Resource population completed for tool {toolId}")
            return [ToolResourceSchema.from_db_model(resource) for resource in created_resources]
            
        else:
            logger.warning(f"MCP configuration test failed for tool {toolId}: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP configuration test failed: {error_message or 'Unknown error'}"
            )
            
    except HTTPException:
        logger.error(f"HTTP exception when connecting to MCP server for tool {toolId}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MCP server for tool {toolId}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test MCP configuration: {str(e)}"
        )
