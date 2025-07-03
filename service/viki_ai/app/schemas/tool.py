from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ToolBase(BaseModel):
    toolName: str = Field(..., max_length=240, description="Tool name", alias="tol_name")
    toolDescription: Optional[str] = Field(None, max_length=4000, description="Tool description", alias="tol_description")
    toolMcpCommand: str = Field(..., max_length=240, description="MCP command", alias="tol_mcp_command")
    toolMcpFunctionCount: int = Field(default=0, description="MCP function count", alias="tol_mcp_function_count")
    toolProxyRequired: Optional[bool] = Field(False, description="Whether proxy is required for this tool", alias="tol_proxy_required")

    class Config:
        populate_by_name = True


class ToolCreate(ToolBase):
    toolId: str = Field(..., max_length=80, description="Tool ID", alias="tol_id")


class ToolUpdate(BaseModel):
    toolName: Optional[str] = Field(None, max_length=240, description="Tool name", alias="tol_name")
    toolDescription: Optional[str] = Field(None, max_length=4000, description="Tool description", alias="tol_description")
    toolMcpCommand: Optional[str] = Field(None, max_length=240, description="MCP command", alias="tol_mcp_command")
    toolMcpFunctionCount: Optional[int] = Field(None, description="MCP function count", alias="tol_mcp_function_count")
    toolProxyRequired: Optional[bool] = Field(None, description="Whether proxy is required for this tool", alias="tol_proxy_required")

    class Config:
        populate_by_name = True


class Tool(ToolBase):
    toolId: str = Field(..., max_length=80, description="Tool ID", alias="tol_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ToolEnvironmentVariableBase(BaseModel):
    toolId: str = Field(..., max_length=80, description="Tool ID", alias="tev_tol_id")
    envVarKey: str = Field(..., max_length=240, description="Environment variable key", alias="tev_key")
    envVarValue: Optional[str] = Field(None, max_length=4000, description="Environment variable value", alias="tev_value")

    class Config:
        populate_by_name = True


class ToolEnvironmentVariableCreate(ToolEnvironmentVariableBase):
    pass


class ToolEnvironmentVariableUpdate(BaseModel):
    envVarValue: Optional[str] = Field(None, max_length=4000, description="Environment variable value", alias="tev_value")

    class Config:
        populate_by_name = True


class ToolEnvironmentVariable(ToolEnvironmentVariableBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


class ToolResourceBase(BaseModel):
    toolId: str = Field(..., max_length=80, description="Tool ID", alias="tre_tol_id")
    resourceName: str = Field(..., max_length=240, description="Resource name", alias="tre_resource_name")
    resourceDescription: Optional[str] = Field(None, max_length=4000, description="Resource description", alias="tre_resource_description")

    class Config:
        populate_by_name = True


class ToolResource(ToolResourceBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


# Response models with relationships
class ToolWithDetails(Tool):
    environmentVariables: List[ToolEnvironmentVariable] = Field(default_factory=list, description="Environment variables", alias="environment_variables")
    resources: List[ToolResource] = Field(default_factory=list, description="Tool resources")


class ToolEnvironmentVariableWithTool(ToolEnvironmentVariable):
    tool: Optional[Tool] = Field(None, description="Associated tool")
