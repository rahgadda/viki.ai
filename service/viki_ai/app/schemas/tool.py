from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ToolBase(BaseModel):
    toolName: str = Field(
        ..., 
        max_length=240, 
        description="Tool name",
        validation_alias="toolName",
        serialization_alias="toolName"
    )
    toolDescription: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Tool description",
        validation_alias="toolDescription",
        serialization_alias="toolDescription"
    )
    toolMcpCommand: str = Field(
        ..., 
        max_length=240, 
        description="MCP command",
        validation_alias="toolMcpCommand",
        serialization_alias="toolMcpCommand"
    )
    toolMcpFunctionCount: int = Field(
        default=0, 
        description="MCP function count",
        validation_alias="toolMcpFunctionCount",
        serialization_alias="toolMcpFunctionCount"
    )
    toolProxyRequired: Optional[bool] = Field(
        False, 
        description="Whether proxy is required for this tool",
        validation_alias="toolProxyRequired",
        serialization_alias="toolProxyRequired"
    )

    class Config:
        populate_by_name = True


class ToolCreate(BaseModel):
    toolName: str = Field(
        ..., 
        max_length=240, 
        description="Tool name",
        validation_alias="toolName",
        serialization_alias="toolName"
    )
    toolDescription: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Tool description",
        validation_alias="toolDescription",
        serialization_alias="toolDescription"
    )
    toolMcpCommand: str = Field(
        ..., 
        max_length=240, 
        description="MCP command",
        validation_alias="toolMcpCommand",
        serialization_alias="toolMcpCommand"
    )
    toolProxyRequired: Optional[bool] = Field(
        False, 
        description="Whether proxy is required for this tool",
        validation_alias="toolProxyRequired",
        serialization_alias="toolProxyRequired"
    )

    class Config:
        populate_by_name = True


class ToolUpdate(BaseModel):
    toolName: Optional[str] = Field(
        None, 
        max_length=240, 
        description="Tool name",
        validation_alias="toolName",
        serialization_alias="toolName"
    )
    toolDescription: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Tool description",
        validation_alias="toolDescription",
        serialization_alias="toolDescription"
    )
    toolMcpCommand: Optional[str] = Field(
        None, 
        max_length=240, 
        description="MCP command",
        validation_alias="toolMcpCommand",
        serialization_alias="toolMcpCommand"
    )
    toolProxyRequired: Optional[bool] = Field(
        None, 
        description="Whether proxy is required for this tool",
        validation_alias="toolProxyRequired",
        serialization_alias="toolProxyRequired"
    )

    class Config:
        populate_by_name = True


class Tool(ToolBase):
    toolId: str = Field(
        ..., 
        max_length=80, 
        description="Tool ID",
        validation_alias="toolId",
        serialization_alias="toolId"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user",
        validation_alias="createdBy",
        serialization_alias="createdBy"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user",
        validation_alias="lastUpdatedBy",
        serialization_alias="lastUpdatedBy"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp",
        validation_alias="creationDt",
        serialization_alias="creationDt"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp",
        validation_alias="lastUpdatedDt",
        serialization_alias="lastUpdatedDt"
    )

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            toolId=db_model.tol_id,
            toolName=db_model.tol_name,
            toolDescription=db_model.tol_description,
            toolMcpCommand=db_model.tol_mcp_command,
            toolMcpFunctionCount=db_model.tol_mcp_function_count,
            toolProxyRequired=db_model.tol_proxy_required,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )


class ToolEnvironmentVariableBase(BaseModel):
    toolId: str = Field(
        ..., 
        max_length=80, 
        description="Tool ID",
        validation_alias="toolId",
        serialization_alias="toolId"
    )
    envVarKey: str = Field(
        ..., 
        max_length=240, 
        description="Environment variable key",
        validation_alias="envVarKey",
        serialization_alias="envVarKey"
    )
    envVarValue: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Environment variable value",
        validation_alias="envVarValue",
        serialization_alias="envVarValue"
    )

    class Config:
        populate_by_name = True


class ToolEnvironmentVariableCreate(ToolEnvironmentVariableBase):
    pass


# For bulk creation - no toolId needed since it's in the path
class ToolEnvironmentVariableBulkItem(BaseModel):
    envVarKey: str = Field(
        ..., 
        max_length=240, 
        description="Environment variable key",
        validation_alias="envVarKey",
        serialization_alias="envVarKey"
    )
    envVarValue: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Environment variable value",
        validation_alias="envVarValue",
        serialization_alias="envVarValue"
    )

    class Config:
        populate_by_name = True


class ToolEnvironmentVariableUpdate(BaseModel):
    envVarValue: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Environment variable value",
        validation_alias="envVarValue",
        serialization_alias="envVarValue"
    )

    class Config:
        populate_by_name = True


class ToolEnvironmentVariable(ToolEnvironmentVariableBase):
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user",
        validation_alias="createdBy",
        serialization_alias="createdBy"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user",
        validation_alias="lastUpdatedBy",
        serialization_alias="lastUpdatedBy"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp",
        validation_alias="creationDt",
        serialization_alias="creationDt"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp",
        validation_alias="lastUpdatedDt",
        serialization_alias="lastUpdatedDt"
    )

    class Config:
        from_attributes = True
        populate_by_name = True
        
    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            toolId=db_model.tev_tol_id,
            envVarKey=db_model.tev_key,
            envVarValue=db_model.tev_value,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
        

class ToolResourceBase(BaseModel):
    toolId: str = Field(
        ..., 
        max_length=80, 
        description="Tool ID",
        validation_alias="toolId",
        serialization_alias="toolId"
    )
    resourceName: str = Field(
        ..., 
        max_length=240, 
        description="Resource name",
        validation_alias="resourceName",
        serialization_alias="resourceName"
    )
    resourceDescription: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Resource description",
        validation_alias="resourceDescription",
        serialization_alias="resourceDescription"
    )

    class Config:
        populate_by_name = True


class ToolResource(ToolResourceBase):
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user",
        validation_alias="createdBy",
        serialization_alias="createdBy"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user",
        validation_alias="lastUpdatedBy",
        serialization_alias="lastUpdatedBy"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp",
        validation_alias="creationDt",
        serialization_alias="creationDt"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp",
        validation_alias="lastUpdatedDt",
        serialization_alias="lastUpdatedDt"
    )

    class Config:
        from_attributes = True
        populate_by_name = True
        
    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            toolId=db_model.tre_tol_id,
            resourceName=db_model.tre_resource_name,
            resourceDescription=db_model.tre_resource_description,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
        

# Response models with relationships
class ToolWithDetails(Tool):
    environmentVariables: List[ToolEnvironmentVariable] = Field(
        default_factory=list, 
        description="Environment variables",
        validation_alias="environmentVariables",
        serialization_alias="environmentVariables"
    )
    resources: List[ToolResource] = Field(
        default_factory=list, 
        description="Tool resources",
        validation_alias="resources",
        serialization_alias="resources"
    )


class ToolEnvironmentVariableWithTool(ToolEnvironmentVariable):
    tool: Optional[Tool] = Field(
        None, 
        description="Associated tool",
        validation_alias="tool",
        serialization_alias="tool"
    )
