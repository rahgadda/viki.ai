from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.utils.database import get_db
from app.utils.config import settings
from app.models.lookup import LookupTypes, LookupDetails
from app.schemas.lookup import (
    LookupTypes as LookupTypesSchema,
    LookupTypesCreate,
    LookupTypesUpdate,
    LookupTypesWithDetails,
    LookupDetails as LookupDetailsSchema,
    LookupDetailsCreate,
    LookupDetailsUpdate,
    LookupDetailsWithType
)

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "anonymous"

# Lookup Types endpoints
@router.get("/lookupTypes", response_model=List[LookupTypesSchema])
def get_lookupTypes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all lookup types with pagination"""
    lookupTypes = db.query(LookupTypes).offset(skip).limit(limit).all()
    return lookupTypes


@router.get("/lookupTypes/{lookupType}", response_model=LookupTypesWithDetails)
def get_lookupType(
    lookupType: str,
    db: Session = Depends(get_db)
):
    """Get a specific lookup type with its lookupDetails"""
    db_lookupType = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType).first()
    if db_lookupType is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup type '{lookupType}' not found"
        )
    return db_lookupType


@router.post("/lookupTypes", response_model=LookupTypesSchema, status_code=status.HTTP_201_CREATED)
def create_lookupType(
    lookupType: LookupTypesCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new lookup type"""
    # Check if lookup type already exists
    existing_type = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType.lkt_type).first()
    if existing_type:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lookup type '{lookupType.lkt_type}' already exists"
        )
    
    # Set the created_by field from the username header
    lookupType_data = lookupType.dict()
    lookupType_data['created_by'] = username
    
    db_lookupType = LookupTypes(**lookupType_data)
    db.add(db_lookupType)
    db.commit()
    db.refresh(db_lookupType)
    return db_lookupType


@router.put("/lookupTypes/{lookupType}", response_model=LookupTypesSchema)
def update_lookupType(
    lookupType: str,
    lookupType_update: LookupTypesUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a lookup type"""
    db_lookupType = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType).first()
    if db_lookupType is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup type '{lookupType}' not found"
        )
    
    # Update only provided fields and set last_updated_by
    update_data = lookupType_update.dict(exclude_unset=True)
    update_data['last_updated_by'] = username
    
    for field, value in update_data.items():
        setattr(db_lookupType, field, value)
    
    db.commit()
    db.refresh(db_lookupType)
    return db_lookupType


@router.delete("/lookupTypes/{lookupType}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lookupType(
    lookupType: str,
    db: Session = Depends(get_db)
):
    """Delete a lookup type and all its lookupDetails"""
    db_lookupType = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType).first()
    if db_lookupType is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup type '{lookupType}' not found"
        )
    
    db.delete(db_lookupType)
    db.commit()


# Lookup lookupDetails endpoints
@router.get("/lookupTypes/{lookupType}/lookupDetails", response_model=List[LookupDetailsSchema])
def get_lookup_lookupDetails(
    lookupType: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all lookup lookupDetails for a specific lookup type"""
    # Check if lookup type exists
    db_lookupType = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType).first()
    if db_lookupType is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup type '{lookupType}' not found"
        )
    
    lookup_lookupDetails = db.query(LookupDetails).filter(
        LookupDetails.lkd_lkt_type == lookupType
    ).offset(skip).limit(limit).all()
    return lookup_lookupDetails


@router.get("/lookupTypes/{lookupType}/lookupDetails/{code}", response_model=LookupDetailsWithType)
def get_lookup_detail(
    lookupType: str,
    code: str,
    db: Session = Depends(get_db)
):
    """Get a specific lookup detail"""
    db_lookup_detail = db.query(LookupDetails).filter(
        LookupDetails.lkd_lkt_type == lookupType,
        LookupDetails.lkd_code == code
    ).first()
    if db_lookup_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup detail '{code}' not found for type '{lookupType}'"
        )
    return db_lookup_detail


@router.post("/lookupTypes/{lookupType}/lookupDetails", response_model=LookupDetailsSchema, status_code=status.HTTP_201_CREATED)
def create_lookup_detail(
    lookupType: str,
    lookup_detail: LookupDetailsCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new lookup detail"""
    # Check if lookup type exists
    db_lookupType = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType).first()
    if db_lookupType is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup type '{lookupType}' not found"
        )
    
    # Ensure the lookup detail is for the correct type
    if lookup_detail.lkd_lkt_type != lookupType:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lookup detail type '{lookup_detail.lkd_lkt_type}' does not match URL parameter '{lookupType}'"
        )
    
    # Check if lookup detail already exists
    existing_detail = db.query(LookupDetails).filter(
        LookupDetails.lkd_lkt_type == lookupType,
        LookupDetails.lkd_code == lookup_detail.lkd_code
    ).first()
    if existing_detail:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lookup detail '{lookup_detail.lkd_code}' already exists for type '{lookupType}'"
        )
    
    # Set the created_by field from the username header
    lookup_detail_data = lookup_detail.dict()
    lookup_detail_data['created_by'] = username
    
    db_lookup_detail = LookupDetails(**lookup_detail_data)
    db.add(db_lookup_detail)
    db.commit()
    db.refresh(db_lookup_detail)
    return db_lookup_detail


@router.put("/lookupTypes/{lookupType}/lookupDetails/{code}", response_model=LookupDetailsSchema)
def update_lookup_detail(
    lookupType: str,
    code: str,
    lookup_detail_update: LookupDetailsUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a lookup detail"""
    db_lookup_detail = db.query(LookupDetails).filter(
        LookupDetails.lkd_lkt_type == lookupType,
        LookupDetails.lkd_code == code
    ).first()
    if db_lookup_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup detail '{code}' not found for type '{lookupType}'"
        )
    
    # Update only provided fields and set last_updated_by
    update_data = lookup_detail_update.dict(exclude_unset=True)
    update_data['last_updated_by'] = username
    
    for field, value in update_data.items():
        setattr(db_lookup_detail, field, value)
    
    db.commit()
    db.refresh(db_lookup_detail)
    return db_lookup_detail


@router.delete("/lookupTypes/{lookupType}/lookupDetails/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lookup_detail(
    lookupType: str,
    code: str,
    db: Session = Depends(get_db)
):
    """Delete a lookup detail"""
    db_lookup_detail = db.query(LookupDetails).filter(
        LookupDetails.lkd_lkt_type == lookupType,
        LookupDetails.lkd_code == code
    ).first()
    if db_lookup_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup detail '{code}' not found for type '{lookupType}'"
        )
    
    db.delete(db_lookup_detail)
    db.commit()


# Bulk operations
@router.get("/lookupDetails", response_model=List[LookupDetailsSchema])
def get_all_lookup_lookupDetails(
    lookupType: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all lookup lookupDetails across all types or filter by type"""
    query = db.query(LookupDetails)
    
    if lookupType:
        query = query.filter(LookupDetails.lkd_lkt_type == lookupType)
    
    lookup_lookupDetails = query.offset(skip).limit(limit).all()
    return lookup_lookupDetails


@router.post("/lookupTypes/{lookupType}/lookupDetails/bulk", response_model=List[LookupDetailsSchema])
def create_lookup_lookupDetails_bulk(
    lookupType: str,
    lookup_lookupDetails: List[LookupDetailsCreate],
    db: Session = Depends(get_db)
):
    """Create multiple lookup lookupDetails at once"""
    # Check if lookup type exists
    db_lookupType = db.query(LookupTypes).filter(LookupTypes.lkt_type == lookupType).first()
    if db_lookupType is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lookup type '{lookupType}' not found"
        )
    
    created_lookupDetails = []
    for lookup_detail in lookup_lookupDetails:
        # Ensure the lookup detail is for the correct type
        if lookup_detail.lkd_lkt_type != lookupType:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lookup detail type '{lookup_detail.lkd_lkt_type}' does not match URL parameter '{lookupType}'"
            )
        
        # Check if lookup detail already exists
        existing_detail = db.query(LookupDetails).filter(
            LookupDetails.lkd_lkt_type == lookupType,
            LookupDetails.lkd_code == lookup_detail.lkd_code
        ).first()
        if existing_detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Lookup detail '{lookup_detail.lkd_code}' already exists for type '{lookupType}'"
            )
        
        db_lookup_detail = LookupDetails(**lookup_detail.dict())
        db.add(db_lookup_detail)
        created_lookupDetails.append(db_lookup_detail)
    
    db.commit()
    for detail in created_lookupDetails:
        db.refresh(detail)
    
    return created_lookupDetails
