from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileStoreBase(BaseModel):
    fileStoreSourceTypeCd: str = Field(
        ..., 
        max_length=80, 
        description="Source type code",
        validation_alias="fileStoreSourceTypeCd",
        serialization_alias="fileStoreSourceTypeCd"
    )
    fileStoreSourceId: str = Field(
        ..., 
        max_length=80, 
        description="UUID of Source ID",
        validation_alias="fileStoreSourceId",
        serialization_alias="fileStoreSourceId"
    )
    fileStoreFileName: str = Field(
        ..., 
        max_length=240, 
        description="File name",
        validation_alias="fileStoreFileName",
        serialization_alias="fileStoreFileName"
    )
    fileStoreFileContent: bytes = Field(
        ..., 
        description="File content as binary data",
        validation_alias="fileStoreFileContent",
        serialization_alias="fileStoreFileContent"
    )

    class Config:
        populate_by_name = True


class FileStoreCreate(FileStoreBase):
    pass


class FileStoreUpdate(BaseModel):
    fileStoreSourceTypeCd: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Source type code",
        validation_alias="fileStoreSourceTypeCd",
        serialization_alias="fileStoreSourceTypeCd"
    )
    fileStoreSourceId: Optional[str] = Field(
        None, 
        max_length=80, 
        description="UUID of Source ID",
        validation_alias="fileStoreSourceId",
        serialization_alias="fileStoreSourceId"
    )
    fileStoreFileName: Optional[str] = Field(
        None, 
        max_length=240, 
        description="File name",
        validation_alias="fileStoreFileName",
        serialization_alias="fileStoreFileName"
    )
    fileStoreFileContent: Optional[bytes] = Field(
        None, 
        description="File content as binary data",
        validation_alias="fileStoreFileContent",
        serialization_alias="fileStoreFileContent"
    )

    class Config:
        populate_by_name = True


class FileStore(FileStoreBase):
    fileStoreId: str = Field(
        ..., 
        max_length=80, 
        description="UUID of File Store",
        validation_alias="fileStoreId",
        serialization_alias="fileStoreId"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user",
        validation_alias="createdBy",
        serialization_alias="createdBy"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user",
        validation_alias="lastUpdatedBy",
        serialization_alias="lastUpdatedBy"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp",
        validation_alias="creationDt",
        serialization_alias="creationDt"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp",
        validation_alias="lastUpdatedDt",
        serialization_alias="lastUpdatedDt"
    )

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            fileStoreId=db_model.fis_id,
            fileStoreSourceTypeCd=db_model.fis_source_type_cd,
            fileStoreSourceId=db_model.fis_source_id,
            fileStoreFileName=db_model.fis_file_name,
            fileStoreFileContent=db_model.fis_file_content,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )


# For API responses, we might want to exclude binary content or provide metadata only
class FileStoreMetadata(BaseModel):
    fileStoreId: str = Field(
        ..., 
        max_length=80, 
        description="UUID of File Store",
        validation_alias="fileStoreId",
        serialization_alias="fileStoreId"
    )
    fileStoreSourceTypeCd: str = Field(
        ..., 
        max_length=80, 
        description="Source type code",
        validation_alias="fileStoreSourceTypeCd",
        serialization_alias="fileStoreSourceTypeCd"
    )
    fileStoreSourceId: str = Field(
        ..., 
        max_length=80, 
        description="UUID of Source ID",
        validation_alias="fileStoreSourceId",
        serialization_alias="fileStoreSourceId"
    )
    fileStoreFileName: str = Field(
        ..., 
        max_length=240, 
        description="File name",
        validation_alias="fileStoreFileName",
        serialization_alias="fileStoreFileName"
    )
    createdBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Created by user",
        validation_alias="createdBy",
        serialization_alias="createdBy"
    )
    lastUpdatedBy: Optional[str] = Field(
        None, 
        max_length=80, 
        description="Last updated by user",
        validation_alias="lastUpdatedBy",
        serialization_alias="lastUpdatedBy"
    )
    creationDt: datetime = Field(
        ..., 
        description="Creation timestamp",
        validation_alias="creationDt",
        serialization_alias="creationDt"
    )
    lastUpdatedDt: datetime = Field(
        ..., 
        description="Last updated timestamp",
        validation_alias="lastUpdatedDt",
        serialization_alias="lastUpdatedDt"
    )

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to Pydantic schema"""
        return cls(
            fileStoreId=db_model.fis_id,
            fileStoreSourceTypeCd=db_model.fis_source_type_cd,
            fileStoreSourceId=db_model.fis_source_id,
            fileStoreFileName=db_model.fis_file_name,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )
