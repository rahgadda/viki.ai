import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class LookupTypes(Base):
    __tablename__ = "lookup_types"

    lkt_type = Column(String(80), primary_key=True)
    lkt_description = Column(String(240))
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to lookup details
    lookup_details = relationship("LookupDetails", back_populates="lookup_type", cascade="all, delete-orphan")

    # Property mappings for Pydantic schema compatibility
    @property
    def lookupType(self):
        return self.lkt_type
    
    @property
    def lookupDescription(self):
        return self.lkt_description
    
    @property
    def createdBy(self):
        return self.created_by
    
    @property
    def lastUpdatedBy(self):
        return self.last_updated_by
    
    @property
    def creationDt(self):
        return self.creation_dt
    
    @property
    def lastUpdatedDt(self):
        return self.last_updated_dt

    @property
    def lookupDetails(self):
        return self.lookup_details


class LookupDetails(Base):
    __tablename__ = "lookup_details"

    lkd_lkt_type = Column(String(80), ForeignKey("lookup_types.lkt_type", ondelete="CASCADE"), primary_key=True)
    lkd_code = Column(String(80), primary_key=True)
    lkd_description = Column(String(240))
    lkd_sub_code = Column(String(80))
    lkd_sort = Column(Integer)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to lookup type
    lookup_type = relationship("LookupTypes", back_populates="lookup_details")

    # Property mappings for Pydantic schema compatibility
    @property
    def lookupType(self):
        return self.lkd_lkt_type
    
    @property
    def lookupDetailCode(self):
        return self.lkd_code
    
    @property
    def lookupDetailDescription(self):
        return self.lkd_description
    
    @property
    def lookupDetailSubCode(self):
        return self.lkd_sub_code
    
    @property
    def lookupDetailSort(self):
        return self.lkd_sort
    
    @property
    def createdBy(self):
        return self.created_by
    
    @property
    def lastUpdatedBy(self):
        return self.last_updated_by
    
    @property
    def creationDt(self):
        return self.creation_dt
    
    @property
    def lastUpdatedDt(self):
        return self.last_updated_dt
