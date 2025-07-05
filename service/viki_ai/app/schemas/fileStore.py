from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileStoreBase(BaseModel):
    fileStoreSourceTypeCd: str = Field(..., max_length=80, description="Source type code")
    fileStoreSourceId: str = Field(..., max_length=80, description="UUID of Source ID")
    fileStoreFileName: str = Field(..., max_length=240, description="File name")
    fileStoreFileContent: bytes = Field(..., description="File content as binary data")

    class Config:
        populate_by_name = True


class FileStoreCreate(FileStoreBase):
    pass


class FileStoreUpdate(BaseModel):
    fileStoreSourceTypeCd: Optional[str] = Field(None, max_length=80, description="Source type code")
    fileStoreSourceId: Optional[str] = Field(None, max_length=80, description="UUID of Source ID")
    fileStoreFileName: Optional[str] = Field(None, max_length=240, description="File name")
    fileStoreFileContent: Optional[bytes] = Field(None, description="File content as binary data")

    class Config:
        populate_by_name = True


class FileStore(FileStoreBase):
    fileStoreId: str = Field(..., max_length=80, description="UUID of File Store")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls.model_validate({
            'fileStoreId': db_model.fis_id,
            'fileStoreSourceTypeCd': db_model.fis_source_type_cd,
            'fileStoreSourceId': db_model.fis_source_id,
            'fileStoreFileName': db_model.fis_file_name,
            'fileStoreFileContent': db_model.fis_file_content,
            'createdBy': db_model.created_by,
            'lastUpdatedBy': db_model.last_updated_by,
            'creationDt': db_model.creation_dt,
            'lastUpdatedDt': db_model.last_updated_dt
        })


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
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls.model_validate({
            'fileStoreId': db_model.fis_id,
            'fileStoreSourceTypeCd': db_model.fis_source_type_cd,
            'fileStoreSourceId': db_model.fis_source_id,
            'fileStoreFileName': db_model.fis_file_name,
            'createdBy': db_model.created_by,
            'lastUpdatedBy': db_model.last_updated_by,
            'creationDt': db_model.creation_dt,
            'lastUpdatedDt': db_model.last_updated_dt
        })
