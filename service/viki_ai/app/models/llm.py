from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class LLM(Base):
    __tablename__ = "llm"

    llc_id = Column(String(80), primary_key=True)
    llc_provider_type_cd = Column(String(80), nullable=False)
    llc_model_cd = Column(String(240), nullable=False)
    llc_endpoint_url = Column(String(4000))
    llc_api_key = Column(String(240))
    llc_fls_id = Column(String(80), ForeignKey("file_store.fls_id", ondelete="SET NULL"))
    llc_proxy_required = Column(Boolean, default=False)
    llc_streaming = Column(Boolean, default=False)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # config_file = relationship("FileStore", back_populates="llm_configs")
    agents = relationship("Agent", back_populates="llm_config")
    knowledge_bases = relationship("KnowledgeBaseDetails", back_populates="llm")