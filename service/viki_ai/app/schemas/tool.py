from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ToolBase(BaseModel):
    tol_name: str = Field(..., max_length=240, description="Tool name")
    tol_description: Optional[str] = Field(None, max_length=4000, description="Tool description")
    tol_mcp_command: str = Field(..., max_length=240, description="MCP command")
    tol_mcp_function_count: int = Field(default=0, description="MCP function count")


class ToolCreate(ToolBase):
    tol_id: str = Field(..., max_length=80, description="Tool ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class ToolUpdate(BaseModel):
    tol_name: Optional[str] = Field(None, max_length=240, description="Tool name")
    tol_description: Optional[str] = Field(None, max_length=4000, description="Tool description")
    tol_mcp_command: Optional[str] = Field(None, max_length=240, description="MCP command")
    tol_mcp_function_count: Optional[int] = Field(None, description="MCP function count")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class Tool(ToolBase):
    tol_id: str = Field(..., max_length=80, description="Tool ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True


class ToolEnvironmentVariableBase(BaseModel):
    tev_tol_id: str = Field(..., max_length=80, description="Tool ID")
    tev_key: str = Field(..., max_length=240, description="Environment variable key")
    tev_value: Optional[str] = Field(None, max_length=4000, description="Environment variable value")


class ToolEnvironmentVariableCreate(ToolEnvironmentVariableBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class ToolEnvironmentVariableUpdate(BaseModel):
    tev_value: Optional[str] = Field(None, max_length=4000, description="Environment variable value")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class ToolEnvironmentVariable(ToolEnvironmentVariableBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True


class ToolResourceBase(BaseModel):
    tre_tol_id: str = Field(..., max_length=80, description="Tool ID")
    tre_resource_name: str = Field(..., max_length=240, description="Resource name")
    tre_resource_description: Optional[str] = Field(None, max_length=4000, description="Resource description")


class ToolResourceCreate(ToolResourceBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class ToolResourceUpdate(BaseModel):
    tre_resource_description: Optional[str] = Field(None, max_length=4000, description="Resource description")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class ToolResource(ToolResourceBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True


# Response models with relationships
class ToolWithDetails(Tool):
    environment_variables: List[ToolEnvironmentVariable] = Field(default_factory=list, description="Environment variables")
    resources: List[ToolResource] = Field(default_factory=list, description="Tool resources")


class ToolEnvironmentVariableWithTool(ToolEnvironmentVariable):
    tool: Optional[Tool] = Field(None, description="Associated tool")


class ToolResourceWithTool(ToolResource):
    tool: Optional[Tool] = Field(None, description="Associated tool")
