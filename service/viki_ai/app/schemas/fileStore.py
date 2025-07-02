from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileStoreBase(BaseModel):
    fls_source_type_cd: str = Field(..., max_length=80, description="Source type code")
    fls_source_id: str = Field(..., max_length=80, description="Source ID")
    fls_file_name: str = Field(..., max_length=240, description="File name")
    fls_file_content: bytes = Field(..., description="File content as binary data")


class FileStoreCreate(FileStoreBase):
    fls_id: str = Field(..., max_length=80, description="File store ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class FileStoreUpdate(BaseModel):
    fls_source_type_cd: Optional[str] = Field(None, max_length=80, description="Source type code")
    fls_source_id: Optional[str] = Field(None, max_length=80, description="Source ID")
    fls_file_name: Optional[str] = Field(None, max_length=240, description="File name")
    fls_file_content: Optional[bytes] = Field(None, description="File content as binary data")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class FileStore(FileStoreBase):
    fls_id: str = Field(..., max_length=80, description="File store ID")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True


# For API responses, we might want to exclude binary content or provide metadata only
class FileStoreMetadata(BaseModel):
    fls_id: str = Field(..., max_length=80, description="File store ID")
    fls_source_type_cd: str = Field(..., max_length=80, description="Source type code")
    fls_source_id: str = Field(..., max_length=80, description="Source ID")
    fls_file_name: str = Field(..., max_length=240, description="File name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True
