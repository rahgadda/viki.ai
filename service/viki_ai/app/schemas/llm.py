from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LLMBase(BaseModel):
    llmProviderTypeCd: str = Field(..., max_length=80, description="Provider type code", alias="llc_provider_type_cd")
    llmModelCd: str = Field(..., max_length=240, description="Model code", alias="llc_model_cd")
    llmEndpointUrl: Optional[str] = Field(None, max_length=4000, description="Endpoint URL", alias="llc_endpoint_url")
    llmApiKey: Optional[str] = Field(None, max_length=240, description="API key", alias="llc_api_key")
    llmFileStoreId: Optional[str] = Field(None, max_length=80, description="Configuration file ID", alias="llc_fls_id")
    llmProxyRequired: Optional[bool] = Field(False, description="Whether proxy is required for this LLM", alias="llc_proxy_required")

    class Config:
        populate_by_name = True


class LLMCreate(LLMBase):
    pass


class LLMUpdate(BaseModel):
    llmProviderTypeCd: Optional[str] = Field(None, max_length=80, description="Provider type code", alias="llc_provider_type_cd")
    llmModelCd: Optional[str] = Field(None, max_length=240, description="Model code", alias="llc_model_cd")
    llmEndpointUrl: Optional[str] = Field(None, max_length=4000, description="Endpoint URL", alias="llc_endpoint_url")
    llmApiKey: Optional[str] = Field(None, max_length=240, description="API key", alias="llc_api_key")
    llmFileStoreId: Optional[str] = Field(None, max_length=80, description="Configuration file ID", alias="llc_fls_id")
    llmProxyRequired: Optional[bool] = Field(None, description="Whether proxy is required for this LLM", alias="llc_proxy_required")

    class Config:
        populate_by_name = True


class LLM(LLMBase):
    llmId: str = Field(..., max_length=80, description="LLM configuration ID", alias="llc_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True

# For security purposes, we might want to exclude sensitive information like API keys
class LLMPublic(BaseModel):
    llmId: str = Field(..., max_length=80, description="LLM configuration ID", alias="llc_id")
    llmProviderTypeCd: str = Field(..., max_length=80, description="Provider type code", alias="llc_provider_type_cd")
    llmModelCd: str = Field(..., max_length=240, description="Model code", alias="llc_model_cd")
    llmEndpointUrl: Optional[str] = Field(None, max_length=4000, description="Endpoint URL", alias="llc_endpoint_url")
    llmFileStoreId: Optional[str] = Field(None, max_length=80, description="Configuration file ID", alias="llc_fls_id")
    llmProxyRequired: Optional[bool] = Field(False, description="Whether proxy is required for this LLM", alias="llc_proxy_required")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        
