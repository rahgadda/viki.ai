from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class KnowledgeBaseDetailsBase(BaseModel):
    knowledgeBaseName: str = Field(..., max_length=240, description="Knowledge base name")
    knowledgeBaseDescription: Optional[str] = Field(None, max_length=4000, description="Knowledge base description")
    llmConfigId: Optional[str] = Field(None, max_length=80, description="LLM configuration ID")

    class Config:
        populate_by_name = True


class KnowledgeBaseDetailsCreate(KnowledgeBaseDetailsBase):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID")


class KnowledgeBaseDetailsUpdate(BaseModel):
    knowledgeBaseName: Optional[str] = Field(None, max_length=240, description="Knowledge base name")
    knowledgeBaseDescription: Optional[str] = Field(None, max_length=4000, description="Knowledge base description")
    llmConfigId: Optional[str] = Field(None, max_length=80, description="LLM configuration ID")

    class Config:
        populate_by_name = True


class KnowledgeBaseDetails(KnowledgeBaseDetailsBase):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            knowledgeBaseId=db_model.knb_id,
            knowledgeBaseName=db_model.knb_name,
            knowledgeBaseDescription=db_model.knb_description,
            llmConfigId=db_model.knb_llc_id,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
        


class KnowledgeBaseDocumentsBase(BaseModel):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID")
    fileStoreId: str = Field(..., max_length=80, description="File store ID")

    class Config:
        populate_by_name = True


class KnowledgeBaseDocumentsCreate(KnowledgeBaseDocumentsBase):
    pass


class KnowledgeBaseDocumentsUpdate(BaseModel):
    pass


class KnowledgeBaseDocuments(KnowledgeBaseDocumentsBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            knowledgeBaseId=db_model.kbd_knb_id,
            fileStoreId=db_model.kbd_fls_id,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
        


# Response models with relationships
class KnowledgeBaseDetailsWithDocuments(KnowledgeBaseDetails):
    documents: List[KnowledgeBaseDocuments] = Field(default_factory=list, description="Associated documents")


class KnowledgeBaseDocumentsWithDetails(KnowledgeBaseDocuments):
    knowledgeBase: Optional[KnowledgeBaseDetails] = Field(None, description="Associated knowledge base")
