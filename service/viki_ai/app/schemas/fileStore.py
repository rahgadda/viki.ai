from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileStoreBase(BaseModel):
    fileStoreSourceTypeCd: str = Field(..., max_length=80, description="Source type code", alias="fls_source_type_cd")
    fileStoreSourceId: str = Field(..., max_length=80, description="UUID of Source ID", alias="fls_source_id")
    fileStoreFileName: str = Field(..., max_length=240, description="File name", alias="fls_file_name")
    fileStoreFileContent: bytes = Field(..., description="File content as binary data", alias="fls_file_content")

    class Config:
        populate_by_name = True


class FileStoreCreate(FileStoreBase):
    pass


class FileStoreUpdate(BaseModel):
    fileStoreSourceTypeCd: Optional[str] = Field(None, max_length=80, description="Source type code", alias="fls_source_type_cd")
    fileStoreSourceId: Optional[str] = Field(None, max_length=80, description="UUID of Source ID", alias="fls_source_id")
    fileStoreFileName: Optional[str] = Field(None, max_length=240, description="File name", alias="fls_file_name")
    fileStoreFileContent: Optional[bytes] = Field(None, description="File content as binary data", alias="fls_file_content")

    class Config:
        populate_by_name = True


class FileStore(FileStoreBase):
    fileStoreId: str = Field(..., max_length=80, description="UUID of File Store", alias="fls_id")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True


# For API responses, we might want to exclude binary content or provide metadata only
class FileStoreMetadata(BaseModel):
    fileStoreId: str = Field(..., max_length=80, description="UUID of File Store", alias="fls_id")
    fileStoreSourceTypeCd: str = Field(..., max_length=80, description="Source type code", alias="fls_source_type_cd")
    fileStoreSourceId: str = Field(..., max_length=80, description="UUID of Source ID", alias="fls_source_id")
    fileStoreFileName: str = Field(..., max_length=240, description="File name", alias="fls_file_name")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True
