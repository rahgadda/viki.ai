from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class LookupTypesBase(BaseModel):
    lkt_description: Optional[str] = Field(None, max_length=240, description="Lookup type description")


class LookupTypesCreate(LookupTypesBase):
    lkt_type: str = Field(..., max_length=80, description="Lookup type")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class LookupTypesUpdate(BaseModel):
    lkt_description: Optional[str] = Field(None, max_length=240, description="Lookup type description")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class LookupTypes(LookupTypesBase):
    lkt_type: str = Field(..., max_length=80, description="Lookup type")
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True


class LookupDetailsBase(BaseModel):
    lkd_lkt_type: str = Field(..., max_length=80, description="Lookup type")
    lkd_code: str = Field(..., max_length=80, description="Lookup code")
    lkd_description: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lkd_sub_code: Optional[str] = Field(None, max_length=80, description="Lookup sub code")
    lkd_sort: Optional[int] = Field(None, description="Sort order")


class LookupDetailsCreate(LookupDetailsBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")


class LookupDetailsUpdate(BaseModel):
    lkd_description: Optional[str] = Field(None, max_length=240, description="Lookup description")
    lkd_sub_code: Optional[str] = Field(None, max_length=80, description="Lookup sub code")
    lkd_sort: Optional[int] = Field(None, description="Sort order")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")


class LookupDetails(LookupDetailsBase):
    created_by: Optional[str] = Field(None, max_length=80, description="Created by user")
    last_updated_by: Optional[str] = Field(None, max_length=80, description="Last updated by user")
    creation_dt: datetime = Field(..., description="Creation timestamp")
    last_updated_dt: datetime = Field(..., description="Last updated timestamp")

    class Config:
        from_attributes = True
        orm_mode = True


# Response models with relationships
class LookupTypesWithDetails(LookupTypes):
    lookup_details: List[LookupDetails] = Field(default_factory=list, description="Associated lookup details")


class LookupDetailsWithType(LookupDetails):
    lookup_type: Optional[LookupTypes] = Field(None, description="Associated lookup type")
