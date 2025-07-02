from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LLMBase(BaseModel):
    llc_provider_type_cd: str = Field(..., max_length=80, description="Provider type code")
    llc_model_cd: str = Field(..., max_length=240, description="Model code")
    llc_endpoint_url: Optional[str] = Field(None, max_length=4000, description="Endpoint URL")
    llc_api_key: Optional[str] = Field(None, max_length=240, description="API key")
    llc_fls_id: Optional[str] = Field(None, max_length=80, description="Configuration file ID")


class LLMCreate(LLMBase):
    llc_id: str = Field(..., max_length=80, description="LLM configuration ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class LLMUpdate(BaseModel):
    llc_provider_type_cd: Optional[str] = Field(None, max_length=80, description="Provider type code")
    llc_model_cd: Optional[str] = Field(None, max_length=240, description="Model code")
    llc_endpoint_url: Optional[str] = Field(None, max_length=4000, description="Endpoint URL")
    llc_api_key: Optional[str] = Field(None, max_length=240, description="API key")
    llc_fls_id: Optional[str] = Field(None, max_length=80, description="Configuration file ID")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class LLM(LLMBase):
    llc_id: str = Field(..., max_length=80, description="LLM configuration ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True


# For security purposes, we might want to exclude sensitive information like API keys
class LLMPublic(BaseModel):
    llc_id: str = Field(..., max_length=80, description="LLM configuration ID")
    llc_provider_type_cd: str = Field(..., max_length=80, description="Provider type code")
    llc_model_cd: str = Field(..., max_length=240, description="Model code")
    llc_endpoint_url: Optional[str] = Field(None, max_length=4000, description="Endpoint URL")
    llc_fls_id: Optional[str] = Field(None, max_length=80, description="Configuration file ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True
