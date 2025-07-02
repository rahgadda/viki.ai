from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class KnowledgeBaseDetailsBase(BaseModel):
    knb_name: str = Field(..., max_length=240, description="Knowledge base name")
    knb_description: Optional[str] = Field(None, max_length=4000, description="Knowledge base description")


class KnowledgeBaseDetailsCreate(KnowledgeBaseDetailsBase):
    knb_id: str = Field(..., max_length=80, description="Knowledge base ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class KnowledgeBaseDetailsUpdate(BaseModel):
    knb_name: Optional[str] = Field(None, max_length=240, description="Knowledge base name")
    knb_description: Optional[str] = Field(None, max_length=4000, description="Knowledge base description")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class KnowledgeBaseDetails(KnowledgeBaseDetailsBase):
    knb_id: str = Field(..., max_length=80, description="Knowledge base ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        


class KnowledgeBaseDocumentsBase(BaseModel):
    kbd_knb_id: str = Field(..., max_length=80, description="Knowledge base ID")
    kbd_fls_id: str = Field(..., max_length=80, description="File store ID")


class KnowledgeBaseDocumentsCreate(KnowledgeBaseDocumentsBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class KnowledgeBaseDocumentsUpdate(BaseModel):
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class KnowledgeBaseDocuments(KnowledgeBaseDocumentsBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        


# Response models with relationships
class KnowledgeBaseDetailsWithDocuments(KnowledgeBaseDetails):
    documents: List[KnowledgeBaseDocuments] = Field(default_factory=list, description="Associated documents")


class KnowledgeBaseDocumentsWithDetails(KnowledgeBaseDocuments):
    knowledge_base: Optional[KnowledgeBaseDetails] = Field(None, description="Associated knowledge base")
