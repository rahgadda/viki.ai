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
@router.get("/fileStores", response_model=List[FileStoreMetadata])
def get_file_stores(
    skip: int = 0,
    limit: int = 100,
    sourceType: Optional[str] = None,
    sourceId: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all file stores with pagination and optional filtering"""
    query = db.query(FileStore)
    
    if sourceType:
        query = query.filter(FileStore.fls_source_type_cd == sourceType)
    if sourceId:
        query = query.filter(FileStore.fls_source_id == sourceId)
    
    file_stores = query.offset(skip).limit(limit).all()
    return [FileStoreMetadata.from_db_model(fs) for fs in file_stores]


@router.get("/fileStores/{fileStoreId}", response_model=FileStoreSchema)
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
    return FileStoreSchema.from_db_model(db_file_store)


@router.get("/fileStores/{fileStoreId}/metadata", response_model=FileStoreMetadata)
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
    return FileStoreMetadata.from_db_model(db_file_store)

@router.post("/fileStores/upload", response_model=FileStoreMetadata, status_code=status.HTTP_201_CREATED)
def upload_file(
    fileStoreSourceTypeCd: str,
    fileStoreSourceId: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    username: str = Depends(get_username)
):
    """Upload a file and create a file store record"""
    # Generate UUID for the file store
    fileStoreId = str(uuid.uuid4())

    # Read file content
    file_content = file.file.read()
    
    # Handle case where filename might be None
    filename = file.filename or "uploaded_file"
    
    # Create file store using schema with camelCase field names (Pydantic will handle DB mapping)
    file_store_create = FileStoreCreate(
        fileStoreSourceTypeCd=fileStoreSourceTypeCd,
        fileStoreSourceId=fileStoreSourceId,
        fileStoreFileName=filename,
        fileStoreFileContent=file_content
    )
    
    # Create database record - Pydantic will handle the field mapping via validation_alias
    db_file_store = FileStore(
        fls_id=fileStoreId,
        fls_source_type_cd=file_store_create.fileStoreSourceTypeCd,
        fls_source_id=file_store_create.fileStoreSourceId,
        fls_file_name=file_store_create.fileStoreFileName,
        fls_file_content=file_store_create.fileStoreFileContent,
        created_by=username,
        last_updated_by=username
    )
    db.add(db_file_store)
    db.commit()
    db.refresh(db_file_store)
    return FileStoreMetadata.from_db_model(db_file_store)


@router.put("/fileStores/{fileStoreId}", response_model=FileStoreMetadata)
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
    if file_store_update.fileStoreSourceTypeCd is not None:
        setattr(db_file_store, 'fls_source_type_cd', file_store_update.fileStoreSourceTypeCd)
    if file_store_update.fileStoreSourceId is not None:
        setattr(db_file_store, 'fls_source_id', file_store_update.fileStoreSourceId)
    if file_store_update.fileStoreFileName is not None:
        setattr(db_file_store, 'fls_file_name', file_store_update.fileStoreFileName)
    if file_store_update.fileStoreFileContent is not None:
        setattr(db_file_store, 'fls_file_content', file_store_update.fileStoreFileContent)
    
    setattr(db_file_store, 'last_updated_by', username)
    
    db.commit()
    db.refresh(db_file_store)
    return FileStoreMetadata.from_db_model(db_file_store)


@router.delete("/fileStores/{fileStoreId}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.get("/fileStores/{fileStoreId}/download")
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
            "Content-Disposition": f"attachment; filename={db_file_store.fls_file_name}"
        }
    )
