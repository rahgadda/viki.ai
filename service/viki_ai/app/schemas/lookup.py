from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LookupTypesBase(BaseModel):
    lookupDescription: Optional[str] = Field(None, max_length=240, description="Lookup type description", alias="lkt_description")

    class Config:
        populate_by_name = True


class LookupTypesCreate(LookupTypesBase):
    lookupType: str = Field(..., max_length=80, description="Lookup type", alias="lkt_type")


class LookupTypesUpdate(BaseModel):
    lookupDescription: Optional[str] = Field(None, max_length=240, description="Lookup type description", alias="lkt_description")

    class Config:
        populate_by_name = True


class LookupTypes(LookupTypesBase):
    lookupType: str = Field(..., max_length=80, description="Lookup type", alias="lkt_type")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True


class LookupDetailsBase(BaseModel):
    lookupType: str = Field(..., max_length=80, description="Lookup type", alias="lkd_lkt_type")
    lookupDetailCode: str = Field(..., max_length=80, description="LookupDetails code", alias="lkd_code")
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description", alias="lkd_description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode", alias="lkd_sub_code")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order", alias="lkd_sort")

    class Config:
        populate_by_name = True


class LookupDetailsCreate(LookupDetailsBase):
    pass


class LookupDetailsUpdate(BaseModel):
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description", alias="lkd_description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode", alias="lkd_sub_code")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order", alias="lkd_sort")

    class Config:
        populate_by_name = True


class LookupDetails(LookupDetailsBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user", alias="created_by")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user", alias="last_updated_by")
    creationDt: datetime = Field(..., description="Creation timestamp", alias="creation_dt")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp", alias="last_updated_dt")

    class Config:
        from_attributes = True
        populate_by_name = True

# Response models with relationships
class LookupTypesWithDetails(LookupTypes):
    lookupDetails: List[LookupDetails] = Field(default_factory=list, description="Associated lookup details", alias="lookup_details")


class LookupDetailsWithType(LookupDetails):
    lookupType: Optional[LookupTypes] = Field(None, description="Associated lookup type")
