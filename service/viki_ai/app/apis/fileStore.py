from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from app.utils.database import get_db
from app.utils.config import settings
from app.models.fileStore import FileStore
from app.schemas.fileStore import (
    FileStore as FileStoreSchema,
    FileStoreCreate,
    FileStoreUpdate,
    FileStoreMetadata
)

# Create router with version prefix
router = APIRouter(prefix=f"/api/v{settings.VERSION}")


def get_username(x_username: str = Header(None, alias="x-username")) -> str:
    """
    Dependency to extract username from x-username header
    """
    return x_username or "SYSTEM"


# FileStore endpoints
@router.get("/fileStore", response_model=List[FileStoreMetadata])
def get_file_stores(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all file stores with pagination and optional filtering"""
    query = db.query(FileStore)
    
    if source_type:
        query = query.filter(FileStore.fls_source_type_cd == source_type)
    if source_id:
        query = query.filter(FileStore.fls_source_id == source_id)
    
    file_stores = query.offset(skip).limit(limit).all()
    return file_stores


@router.get("/fileStore/{fileStoreId}", response_model=FileStoreSchema)
def get_file_store(
    fileStoreId: str,
    db: Session = Depends(get_db)
):
    """Get a specific file store by ID"""
    db_file_store = db.query(FileStore).filter(FileStore.fls_id == fileStoreId).first()
    if db_file_store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File store '{fileStoreId}' not found"
        )
    return db_file_store


@router.get("/fileStore/{fileStoreId}/metadata", response_model=FileStoreMetadata)
def get_file_store_metadata(
    fileStoreId: str,
    db: Session = Depends(get_db)
):
    """Get file store metadata without binary content"""
    db_file_store = db.query(FileStore).filter(FileStore.fls_id == fileStoreId).first()
    if db_file_store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File store '{fileStoreId}' not found"
        )
    return db_file_store

@router.post("/fileStore/upload", response_model=FileStoreMetadata, status_code=status.HTTP_201_CREATED)
def upload_file(
    source_type_cd: str,
    source_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Upload a file and create a file store record"""
    # Generate UUID for the file store
    fileStoreId = str(uuid.uuid4())

    # Read file content
    file_content = file.file.read()
    
    # Create file store record
    db_data = {
        'fls_id': fileStoreId,
        'fls_source_type_cd': source_type_cd,
        'fls_source_id': source_id,
        'fls_file_name': file.filename,
        'fls_file_content': file_content,
        'created_by': username,
        'last_updated_by': username
    }
    
    db_file_store = FileStore(**db_data)
    db.add(db_file_store)
    db.commit()
    db.refresh(db_file_store)
    return db_file_store


@router.put("/fileStore/{fileStoreId}", response_model=FileStoreMetadata)
def update_file_store(
    fileStoreId: str,
    file_store_update: FileStoreUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Update a file store"""
    db_file_store = db.query(FileStore).filter(FileStore.fls_id == fileStoreId).first()
    if db_file_store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File store '{fileStoreId}' not found"
        )
    
    # Update only provided fields and set last_updated_by
    update_data = file_store_update.dict(exclude_unset=True)
    update_data['lastUpdatedBy'] = username
    
    # Map schema fields to database fields
    field_mapping = {
        'fileStoreSourceTypeCd': 'fls_source_type_cd',
        'fileStoreSourceId': 'fls_source_id',
        'fileStoreFileName': 'fls_file_name',
        'fileStoreFileContent': 'fls_file_content',
        'lastUpdatedBy': 'last_updated_by'
    }
    
    for schema_field, value in update_data.items():
        db_field = field_mapping.get(schema_field, schema_field)
        setattr(db_file_store, db_field, value)
    
    db.commit()
    db.refresh(db_file_store)
    return db_file_store


@router.delete("/fileStore/{fileStoreId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_store(
    fileStoreId: str,
    db: Session = Depends(get_db)
):
    """Delete a file store"""
    db_file_store = db.query(FileStore).filter(FileStore.fls_id == fileStoreId).first()
    if db_file_store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File store '{fileStoreId}' not found"
        )
    
    db.delete(db_file_store)
    db.commit()


@router.get("/fileStore/{fileStoreId}/download")
def download_file(
    fileStoreId: str,
    db: Session = Depends(get_db)
):
    """Download file content"""
    from fastapi.responses import Response
    
    db_file_store = db.query(FileStore).filter(FileStore.fls_id == fileStoreId).first()
    if db_file_store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File store '{fileStoreId}' not found"
        )
    
    # Use application/octet-stream as default content type for now
    return Response(
        content=db_file_store.fls_file_content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=file"
        }
    )

@router.post("/fileStore", response_model=FileStoreMetadata, status_code=status.HTTP_201_CREATED)
def create_file_store(
    file_store: FileStoreCreate,
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Create a new file store"""
    # Generate UUID for the file store
    fileStoreId = str(uuid.uuid4())
    
    # Set the createdBy field from the username header
    file_store_data = file_store.dict()
    file_store_data['createdBy'] = username
    
    # Map schema fields to database fields
    db_data = {
        'fls_id': fileStoreId,
        'fls_source_type_cd': file_store_data['fileStoreSourceTypeCd'],
        'fls_source_id': file_store_data['fileStoreSourceId'],
        'fls_file_name': file_store_data['fileStoreFileName'],
        'fls_file_content': file_store_data['fileStoreFileContent'],
        'created_by': file_store_data['createdBy'],
        'last_updated_by': username  # Set lastUpdatedBy to same user for creation
    }
    
    db_file_store = FileStore(**db_data)
    db.add(db_file_store)
    db.commit()
    db.refresh(db_file_store)
    return db_file_store
