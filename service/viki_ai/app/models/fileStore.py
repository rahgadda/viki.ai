from sqlalchemy import Column, String, LargeBinary, DateTime
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class FileStore(Base):
    __tablename__ = "file_store"

    fls_id = Column(String(80), primary_key=True)
    fls_source_type_cd = Column(String(80), nullable=False)
    fls_source_id = Column(String(80), nullable=False)
    fls_file_name = Column(String(240), nullable=False)
    fls_file_content = Column(LargeBinary, nullable=False)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    llm_configs = relationship("LLM", back_populates="config_file")
    knowledge_base_documents = relationship("KnowledgeBaseDocuments", back_populates="file")