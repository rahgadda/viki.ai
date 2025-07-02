from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LookupTypesBase(BaseModel):
    lookupDescription: Optional[str] = Field(None, max_length=240, description="Lookup type description")


class LookupTypesCreate(LookupTypesBase):
    lookupType: str = Field(..., max_length=80, description="Lookup type")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")


class LookupTypesUpdate(BaseModel):
    lookupDescription: Optional[str] = Field(None, max_length=240, description="Lookup type description")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class LookupTypes(LookupTypesBase):
    lookupType: str = Field(..., max_length=80, description="Lookup type")
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True


class LookupDetailsBase(BaseModel):
    lookupType: str = Field(..., max_length=80, description="Lookup type")
    lookupDetailCode: str = Field(..., max_length=80, description="LookupDetails code")
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order")


class LookupDetailsCreate(LookupDetailsBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")


class LookupDetailsUpdate(BaseModel):
    lookupDetailDescription: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lookupDetailSubCode: Optional[str] = Field(None, max_length=80, description="Lookup Subcode")
    lookupDetailSort: Optional[int] = Field(None, description="Sort order")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class LookupDetails(LookupDetailsBase):
    createdBy: Optional[str] = Field(None, max_length=80, description="Created by user")
    lastUpdatedBy: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creationDt: datetime = Field(..., description="Creation timestamp")
    lastUpdatedDt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True

# Response models with relationships
class LookupTypesWithDetails(LookupTypes):
    lookupDetails: List[LookupDetails] = Field(default_factory=list, description="Associated lookup details")


class LookupDetailsWithType(LookupDetails):
    lookupType: Optional[LookupTypes] = Field(None, description="Associated lookup type")
