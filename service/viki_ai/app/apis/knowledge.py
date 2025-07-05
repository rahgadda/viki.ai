from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.knowledge import KnowledgeBaseDetails, KnowledgeBaseDocuments
from app.schemas.knowledge import (
    KnowledgeBaseDetails as KnowledgeBaseDetailsSchema,
    KnowledgeBaseDetailsCreate,
    KnowledgeBaseDetailsUpdate,
    KnowledgeBaseDetailsWithDocuments,
    KnowledgeBaseDocuments as KnowledgeBaseDocumentsSchema,
    KnowledgeBaseDocumentsCreate,
    KnowledgeBaseDocumentsUpdate
)

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


# Knowledge Base Details endpoints
@router.get("/knowledge", response_model=List[KnowledgeBaseDetailsSchema])
def get_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    llmConfigId: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all knowledge base configurations with pagination and optional filtering"""
    query = db.query(KnowledgeBaseDetails)
    
    if name:
        query = query.filter(KnowledgeBaseDetails.knb_name.ilike(f"%{name}%"))
    if llmConfigId:
        query = query.filter(KnowledgeBaseDetails.knb_llc_id == llmConfigId)
    
    knowledge_bases = query.offset(skip).limit(limit).all()
    return [KnowledgeBaseDetailsSchema.from_db_model(kb) for kb in knowledge_bases]


@router.get("/knowledge/{knowledgeBaseId}", response_model=KnowledgeBaseDetailsSchema)
def get_knowledge_base(
    knowledgeBaseId: str,
    db: Session = Depends(get_db)
):
    """Get a specific knowledge base configuration by ID"""
    db_kb = db.query(KnowledgeBaseDetails).filter(KnowledgeBaseDetails.knb_id == knowledgeBaseId).first()
    if db_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{knowledgeBaseId}' not found"
        )
    return KnowledgeBaseDetailsSchema.from_db_model(db_kb)


@router.get("/knowledge/{knowledgeBaseId}/with-documents", response_model=KnowledgeBaseDetailsWithDocuments)
def get_knowledge_base_with_documents(
    knowledgeBaseId: str,
    db: Session = Depends(get_db)
):
    """Get a specific knowledge base configuration with its documents"""
    db_kb = db.query(KnowledgeBaseDetails).filter(KnowledgeBaseDetails.knb_id == knowledgeBaseId).first()
    if db_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{knowledgeBaseId}' not found"
        )
    
    # Get associated documents
    documents = db.query(KnowledgeBaseDocuments).filter(
        KnowledgeBaseDocuments.kbd_knb_id == knowledgeBaseId
    ).all()
    
    kb_schema = KnowledgeBaseDetailsSchema.from_db_model(db_kb)
    documents_schema = [KnowledgeBaseDocumentsSchema.from_db_model(doc) for doc in documents]
    
    return KnowledgeBaseDetailsWithDocuments(
        **kb_schema.dict(),
        documents=documents_schema
    )


@router.post("/knowledge", response_model=KnowledgeBaseDetailsSchema, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    kb_create: KnowledgeBaseDetailsCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new knowledge base configuration"""
    # Check if knowledge base ID already exists
    existing_kb = db.query(KnowledgeBaseDetails).filter(
        KnowledgeBaseDetails.knb_id == kb_create.knowledgeBaseId
    ).first()
    if existing_kb:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Knowledge base with ID '{kb_create.knowledgeBaseId}' already exists"
        )

    # Create knowledge base record
    db_kb = KnowledgeBaseDetails(
        knb_id=kb_create.knowledgeBaseId,
        knb_name=kb_create.knowledgeBaseName,
        knb_description=kb_create.knowledgeBaseDescription,
        knb_llc_id=kb_create.llmConfigId,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)
    return KnowledgeBaseDetailsSchema.from_db_model(db_kb)


@router.put("/knowledge/{knowledgeBaseId}", response_model=KnowledgeBaseDetailsSchema)
def update_knowledge_base(
    knowledgeBaseId: str,
    kb_update: KnowledgeBaseDetailsUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a knowledge base configuration"""
    db_kb = db.query(KnowledgeBaseDetails).filter(KnowledgeBaseDetails.knb_id == knowledgeBaseId).first()
    if db_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{knowledgeBaseId}' not found"
        )
    
    # Update only provided fields and set last_updated_by
    if kb_update.knowledgeBaseName is not None:
        setattr(db_kb, 'knb_name', kb_update.knowledgeBaseName)
    if kb_update.knowledgeBaseDescription is not None:
        setattr(db_kb, 'knb_description', kb_update.knowledgeBaseDescription)
    if kb_update.llmConfigId is not None:
        setattr(db_kb, 'knb_llc_id', kb_update.llmConfigId)
    
    setattr(db_kb, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_kb)
    return KnowledgeBaseDetailsSchema.from_db_model(db_kb)


@router.delete("/knowledge/{knowledgeBaseId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    knowledgeBaseId: str,
    db: Session = Depends(get_db)
):
    """Delete a knowledge base configuration"""
    db_kb = db.query(KnowledgeBaseDetails).filter(KnowledgeBaseDetails.knb_id == knowledgeBaseId).first()
    if db_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{knowledgeBaseId}' not found"
        )
    
    db.delete(db_kb)
    db.commit()


# Knowledge Base Documents endpoints
@router.get("/knowledge/{knowledgeBaseId}/documents", response_model=List[KnowledgeBaseDocumentsSchema])
def get_knowledge_base_documents(
    knowledgeBaseId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all documents for a specific knowledge base"""
    # Verify knowledge base exists
    db_kb = db.query(KnowledgeBaseDetails).filter(KnowledgeBaseDetails.knb_id == knowledgeBaseId).first()
    if db_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{knowledgeBaseId}' not found"
        )
    
    documents = db.query(KnowledgeBaseDocuments).filter(
        KnowledgeBaseDocuments.kbd_knb_id == knowledgeBaseId
    ).offset(skip).limit(limit).all()
    
    return [KnowledgeBaseDocumentsSchema.from_db_model(doc) for doc in documents]


@router.post("/knowledge/{knowledgeBaseId}/documents", response_model=KnowledgeBaseDocumentsSchema, status_code=status.HTTP_201_CREATED)
def add_document_to_knowledge_base(
    knowledgeBaseId: str,
    doc_create: KnowledgeBaseDocumentsCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Add a document to a knowledge base"""
    # Verify knowledge base exists
    db_kb = db.query(KnowledgeBaseDetails).filter(KnowledgeBaseDetails.knb_id == knowledgeBaseId).first()
    if db_kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base '{knowledgeBaseId}' not found"
        )
    
    # Check if document already exists in this knowledge base
    existing_doc = db.query(KnowledgeBaseDocuments).filter(
        KnowledgeBaseDocuments.kbd_knb_id == knowledgeBaseId,
        KnowledgeBaseDocuments.kbd_fls_id == doc_create.fileStoreId
    ).first()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document '{doc_create.fileStoreId}' already exists in knowledge base '{knowledgeBaseId}'"
        )

    # Create document record
    db_doc = KnowledgeBaseDocuments(
        kbd_knb_id=knowledgeBaseId,
        kbd_fls_id=doc_create.fileStoreId,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return KnowledgeBaseDocumentsSchema.from_db_model(db_doc)


@router.delete("/knowledge/{knowledgeBaseId}/documents/{fileStoreId}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document_from_knowledge_base(
    knowledgeBaseId: str,
    fileStoreId: str,
    db: Session = Depends(get_db)
):
    """Remove a document from a knowledge base"""
    db_doc = db.query(KnowledgeBaseDocuments).filter(
        KnowledgeBaseDocuments.kbd_knb_id == knowledgeBaseId,
        KnowledgeBaseDocuments.kbd_fls_id == fileStoreId
    ).first()
    if db_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{fileStoreId}' not found in knowledge base '{knowledgeBaseId}'"
        )
    
    db.delete(db_doc)
    db.commit()


@router.put("/knowledge/{knowledgeBaseId}/documents/{fileStoreId}", response_model=KnowledgeBaseDocumentsSchema)
def update_document_in_knowledge_base(
    knowledgeBaseId: str,
    fileStoreId: str,
    doc_update: KnowledgeBaseDocumentsUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a document in a knowledge base"""
    # Verify the document exists in the knowledge base
    db_doc = db.query(KnowledgeBaseDocuments).filter(
        KnowledgeBaseDocuments.kbd_knb_id == knowledgeBaseId,
        KnowledgeBaseDocuments.kbd_fls_id == fileStoreId
    ).first()
    if db_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{fileStoreId}' not found in knowledge base '{knowledgeBaseId}'"
        )
    
    # Currently no updateable fields for documents, but update last_updated_by for audit trail
    setattr(db_doc, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_doc)
    return KnowledgeBaseDocumentsSchema.from_db_model(db_doc)


# Additional convenience endpoints
@router.get("/knowledge/by-llm/{llmConfigId}", response_model=List[KnowledgeBaseDetailsSchema])
def get_knowledge_bases_by_llm(
    llmConfigId: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all knowledge bases for a specific LLM configuration"""
    knowledge_bases = db.query(KnowledgeBaseDetails).filter(
        KnowledgeBaseDetails.knb_llc_id == llmConfigId
    ).offset(skip).limit(limit).all()
    return [KnowledgeBaseDetailsSchema.from_db_model(kb) for kb in knowledge_bases]


@router.get("/knowledge/search", response_model=List[KnowledgeBaseDetailsSchema])
def search_knowledge_bases(
    q: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search knowledge bases by name or description"""
    knowledge_bases = db.query(KnowledgeBaseDetails).filter(
        or_(
            KnowledgeBaseDetails.knb_name.ilike(f"%{q}%"),
            KnowledgeBaseDetails.knb_description.ilike(f"%{q}%")
        )
    ).offset(skip).limit(limit).all()
    return [KnowledgeBaseDetailsSchema.from_db_model(kb) for kb in knowledge_bases]
