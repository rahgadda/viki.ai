from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LookupTypesBase(BaseModel):
    lookupDescription: Optional[str] = Field(None, max_length=240, description="Lookup type description")

    class Config:
        populate_by_name = True


class LookupTypesCreate(LookupTypesBase):
    lookupType: str = Field(..., max_length=80, description="Lookup type")


class LookupTypesUpdate(BaseModel):
    lookupDescription: Optional[str] = Field(None, max_length=240, description="Lookup type description")

    class Config:
        populate_by_name = True


class LookupTypes(LookupTypesBase):
    lookupType: str = Field(..., max_length=80, description="Lookup type")
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
        return cls(
            lookupType=db_model.lkt_type,
            lookupDescription=db_model.lkt_description,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )


class LookupDetailsBase(BaseModel):
    lookupType: str = Field(..., max_length=80, description="Lookup type")
    lookupDetailCode: str = Field(..., max_length=80, description="LookupDetails code")
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order")

    class Config:
        populate_by_name = True


class LookupDetailsCreate(BaseModel):
    lookupDetailCode: str = Field(..., max_length=80, description="LookupDetails code")
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order")

    class Config:
        populate_by_name = True


class LookupDetailsUpdate(BaseModel):
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order")

    class Config:
        populate_by_name = True


class LookupDetails(LookupDetailsBase):
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
        return cls(
            lookupType=db_model.lkd_lkt_type,
            lookupDetailCode=db_model.lkd_code,
            lookupDetailDescription=db_model.lkd_description,
            lookupDetailSubCode=db_model.lkd_sub_code,
            lookupDetailSort=db_model.lkd_sort,
            createdBy=db_model.created_by,
            lastUpdatedBy=db_model.last_updated_by,
            creationDt=db_model.creation_dt,
            lastUpdatedDt=db_model.last_updated_dt
        )

# Response models with relationships
class LookupTypesWithDetails(LookupTypes):
    lookupDetails: List[LookupDetails] = Field(default_factory=list, description="Associated lookup details")


class LookupDetailsWithType(LookupDetails):
    lookupType: Optional[LookupTypes] = Field(None, description="Associated lookup type")
