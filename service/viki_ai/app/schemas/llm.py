from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LLMBase(BaseModel):
    llmProviderTypeCd: str = Field(
        ..., 
        max_length=80, 
        description="Provider type code"
    )
    llmModelCd: str = Field(
        ..., 
        max_length=240, 
        description="Model code"
    )
    llmEndpointUrl: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Endpoint URL"
    )
    llmApiKey: Optional[str] = Field(
        None, 
        max_length=240, 
        description="API key"
    )
    llmFileStoreId: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Configuration file ID"
    )
    llmProxyRequired: Optional[bool] = Field(
        False, 
        description="Whether proxy is required for this LLM"
    )
    llmStreaming: Optional[bool] = Field(
        False, 
        description="Whether this LLM supports streaming responses"
    )
    llmSendHistory: Optional[bool] = Field(
        False, 
        description="Whether to send conversation history to this LLM"
    )

    class Config:
        populate_by_name = True


class LLMCreate(LLMBase):
    pass


class LLMUpdate(BaseModel):
    llmProviderTypeCd: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Provider type code"
    )
    llmModelCd: Optional[str] = Field(
        None, 
        max_length=240, 
        description="Model code"
    )
    llmEndpointUrl: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Endpoint URL"
    )
    llmApiKey: Optional[str] = Field(
        None, 
        max_length=240, 
        description="API key"
    )
    llmFileStoreId: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Configuration file ID"
    )
    llmProxyRequired: Optional[bool] = Field(
        None, 
        description="Whether proxy is required for this LLM"
    )
    llmStreaming: Optional[bool] = Field(
        None, 
        description="Whether this LLM supports streaming responses"
    )
    llmSendHistory: Optional[bool] = Field(
        None, 
        description="Whether to send conversation history to this LLM"
    )

    class Config:
        populate_by_name = True


class LLM(LLMBase):
    llmId: str = Field(
        ..., 
        max_length=80, 
        description="LLM configuration ID"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp"
    )

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            llmId=db_model.llc_id,
            llmProviderTypeCd=db_model.llc_provider_type_cd,
            llmModelCd=db_model.llc_model_cd,
            llmEndpointUrl=db_model.llc_endpoint_url,
            llmApiKey=db_model.llc_api_key,
            llmFileStoreId=db_model.llc_fls_id,
            llmProxyRequired=db_model.llc_proxy_required,
            llmStreaming=db_model.llc_streaming,
            llmSendHistory=db_model.llc_send_history,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )

# For security purposes, we might want to exclude sensitive information like API keys
class LLMPublic(BaseModel):
    llmId: str = Field(
        ..., 
        max_length=80, 
        description="LLM configuration ID"
    )
    llmProviderTypeCd: str = Field(
        ..., 
        max_length=80, 
        description="Provider type code"
    )
    llmModelCd: str = Field(
        ..., 
        max_length=240, 
        description="Model code"
    )
    llmEndpointUrl: Optional[str] = Field(
        None, 
        max_length=4000, 
        description="Endpoint URL"
    )
    llmFileStoreId: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Configuration file ID"
    )
    llmProxyRequired: Optional[bool] = Field(
        False, 
        description="Whether proxy is required for this LLM"
    )
    llmStreaming: Optional[bool] = Field(
        False, 
        description="Whether this LLM supports streaming responses"
    )
    llmSendHistory: Optional[bool] = Field(
        False, 
        description="Whether to send conversation history to this LLM"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp"
    )

    class Config:
        from_attributes = True
        populate_by_name = True
        
