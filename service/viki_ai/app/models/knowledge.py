from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class KnowledgeBaseDetails(Base):
    __tablename__ = "knowledge_base_details"

    knb_id = Column(String(80), primary_key=True)
    knb_name = Column(String(240), nullable=False)
    knb_description = Column(String(4000))
    knb_llc_id = Column(String(80), ForeignKey("llm.llc_id", ondelete="SET NULL"))
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    llm = relationship("LLM", back_populates="knowledge_bases")
    documents = relationship("KnowledgeBaseDocuments", back_populates="knowledge_base", cascade="all, delete-orphan")
    agent_knowledge_bases = relationship("AgentKnowledgeBase", back_populates="knowledge_base")


class KnowledgeBaseDocuments(Base):
    __tablename__ = "knowledge_base_documents"

    kbd_knb_id = Column(String(80), ForeignKey("knowledge_base_details.knb_id", ondelete="CASCADE"), primary_key=True)
    kbd_fls_id = Column(String(80), ForeignKey("file_store.fls_id", ondelete="CASCADE"), primary_key=True)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    knowledge_base = relationship("KnowledgeBaseDetails", back_populates="documents")
    # file = relationship("FileStore", back_populates="knowledge_base_documents")

