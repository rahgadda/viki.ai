from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileStoreBase(BaseModel):
    fileStoreSourceTypeCd: str = Field(..., max_length=80, description="Source type code")
    fileStoreSourceId: str = Field(..., max_length=80, description="UUID of Source ID")
    fileStoreFileName: str = Field(..., max_length=240, description="File name")
    fileStoreFileContent: bytes = Field(..., description="File content as binary data")


class FileStoreCreate(FileStoreBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")


class FileStoreUpdate(BaseModel):
    fileStoreSourceTypeCd: Optional[str] = Field(None, max_length=80, description="Source type code")
    fileStoreSourceId: Optional[str] = Field(None, max_length=80, description="UUID of Source ID")
    fileStoreFileName: Optional[str] = Field(None, max_length=240, description="File name")
    fileStoreFileContent: Optional[bytes] = Field(None, description="File content as binary data")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class FileStore(FileStoreBase):
    fileStoreId: str = Field(..., max_length=80, description="UUID of File Store")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True


# For API responses, we might want to exclude binary content or provide metadata only
class FileStoreMetadata(BaseModel):
    fileStoreId: str = Field(..., max_length=80, description="UUID of File Store")
    fileStoreSourceTypeCd: str = Field(..., max_length=80, description="Source type code")
    fileStoreSourceId: str = Field(..., max_length=80, description="UUID of Source ID")
    fileStoreFileName: str = Field(..., max_length=240, description="File name")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
