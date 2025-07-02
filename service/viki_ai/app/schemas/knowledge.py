from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class KnowledgeBaseDetailsBase(BaseModel):
    knowledgeBaseName: str = Field(..., max_length=240, description="Knowledge base name", alias="knb_name")
    knowledgeBaseDescription: Optional[str] = Field(None, max_length=4000, description="Knowledge base description", alias="knb_description")

    class Config:
        populate_by_name = True


class KnowledgeBaseDetailsCreate(KnowledgeBaseDetailsBase):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID", alias="knb_id")


class KnowledgeBaseDetailsUpdate(BaseModel):
    knowledgeBaseName: Optional[str] = Field(None, max_length=240, description="Knowledge base name", alias="knb_name")
    knowledgeBaseDescription: Optional[str] = Field(None, max_length=4000, description="Knowledge base description", alias="knb_description")

    class Config:
        populate_by_name = True


class KnowledgeBaseDetails(KnowledgeBaseDetailsBase):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID", alias="knb_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


class KnowledgeBaseDocumentsBase(BaseModel):
    knowledgeBaseId: str = Field(..., max_length=80, description="Knowledge base ID", alias="kbd_knb_id")
    fileStoreId: str = Field(..., max_length=80, description="File store ID", alias="kbd_fls_id")

    class Config:
        populate_by_name = True


class KnowledgeBaseDocumentsCreate(KnowledgeBaseDocumentsBase):
    pass


class KnowledgeBaseDocumentsUpdate(BaseModel):
    pass


class KnowledgeBaseDocuments(KnowledgeBaseDocumentsBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
        


# Response models with relationships
class KnowledgeBaseDetailsWithDocuments(KnowledgeBaseDetails):
    documents: List[KnowledgeBaseDocuments] = Field(default_factory=list, description="Associated documents")


class KnowledgeBaseDocumentsWithDetails(KnowledgeBaseDocuments):
    knowledgeBase: Optional[KnowledgeBaseDetails] = Field(None, description="Associated knowledge base", alias="knowledge_base")
