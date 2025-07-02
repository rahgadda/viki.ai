from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.llm import LLM
from app.schemas.llm import (
    LLM as LLMSchema,
    LLMCreate,
    LLMUpdate
)

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


# LLM endpoints
@router.get("/llm", response_model=List[LLMSchema])
def get_llms(
    skip: int = 0,
    limit: int = 100,
    providerTypeCd: Optional[str] = None,
    modelCd: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all LLM configurations with pagination and optional filtering"""
    query = db.query(LLM)
    
    if providerTypeCd:
        query = query.filter(LLM.llc_provider_type_cd == providerTypeCd)
    if modelCd:
        query = query.filter(LLM.llc_model_cd == modelCd)
    
    llms = query.offset(skip).limit(limit).all()
    return llms


@router.get("/llm/{llmId}", response_model=LLMSchema)
def get_llm(
    llmId: str,
    db: Session = Depends(get_db)
):
    """Get a specific LLM configuration by ID"""
    db_llm = db.query(LLM).filter(LLM.llc_id == llmId).first()
    if db_llm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM configuration '{llmId}' not found"
        )
    return db_llm


@router.post("/llm", response_model=LLMSchema, status_code=status.HTTP_201_CREATED)
def create_llm(
    llm_create: LLMCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new LLM configuration"""
    # Generate UUID for the LLM configuration
    llmId = str(uuid.uuid4())

    # Create LLM record using schema data with aliases
    create_data = llm_create.dict(by_alias=True)
    create_data['llc_id'] = llmId
    create_data['created_by'] = username
    create_data['last_updated_by'] = username
    
    db_llm = LLM(**create_data)
    db.add(db_llm)
    db.commit()
    db.refresh(db_llm)
    return db_llm


@router.put("/llm/{llmId}", response_model=LLMSchema)
def update_llm(
    llmId: str,
    llm_update: LLMUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update an LLM configuration"""
    db_llm = db.query(LLM).filter(LLM.llc_id == llmId).first()
    if db_llm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM configuration '{llmId}' not found"
        )
    
    # Update only provided fields and set last_updated_by
    update_data = llm_update.dict(exclude_unset=True, by_alias=True)
    update_data['last_updated_by'] = username
    
    for field, value in update_data.items():
        setattr(db_llm, field, value)
    
    db.commit()
    db.refresh(db_llm)
    return db_llm


@router.delete("/llm/{llmId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_llm(
    llmId: str,
    db: Session = Depends(get_db)
):
    """Delete an LLM configuration"""
    db_llm = db.query(LLM).filter(LLM.llc_id == llmId).first()
    if db_llm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LLM configuration '{llmId}' not found"
        )
    
    db.delete(db_llm)
    db.commit()


@router.get("/llm/provider/{providerTypeCd}", response_model=List[LLMSchema])
def get_llms_by_provider(
    providerTypeCd: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all LLM configurations for a specific provider"""
    llms = db.query(LLM).filter(
        LLM.llc_provider_type_cd == providerTypeCd
    ).offset(skip).limit(limit).all()
    return llms


@router.get("/llm/model/{modelCd}", response_model=List[LLMSchema])
def get_llms_by_model(
    modelCd: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all LLM configurations for a specific model"""
    llms = db.query(LLM).filter(
        LLM.llc_model_cd == modelCd
    ).offset(skip).limit(limit).all()
    return llms