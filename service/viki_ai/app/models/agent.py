from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class Agent(Base):
    __tablename__ = "agents"

    agt_id = Column(String(80), primary_key=True)
    agt_name = Column(String(240), nullable=False)
    agt_description = Column(String(4000))
    agt_llc_id = Column(String(80), ForeignKey("llm.llc_id", ondelete="CASCADE"), nullable=False)
    agt_system_prompt = Column(String(4000))
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    llm_config = relationship("LLM", back_populates="agents")
    agent_tools = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    agent_knowledge_bases = relationship("AgentKnowledgeBase", back_populates="agent", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="agent")



class AgentTool(Base):
    __tablename__ = "agent_tools"

    ato_agt_id = Column(String(80), ForeignKey("agents.agt_id", ondelete="CASCADE"), primary_key=True)
    ato_tol_id = Column(String(80), ForeignKey("tools.tol_id", ondelete="CASCADE"), primary_key=True)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="agent_tools")
    tool = relationship("Tool", back_populates="agent_tools")


class AgentKnowledgeBase(Base):
    __tablename__ = "agent_knowledge_bases"

    akb_agt_id = Column(String(80), ForeignKey("agents.agt_id", ondelete="CASCADE"), primary_key=True)
    akb_knb_id = Column(String(80), ForeignKey("knowledge_base_details.knb_id", ondelete="CASCADE"), primary_key=True)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="agent_knowledge_bases")
    knowledge_base = relationship("KnowledgeBaseDetails", back_populates="agent_knowledge_bases")