from sqlalchemy import Column, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    cht_id = Column(String(80), primary_key=True)
    cht_name = Column(String(240), nullable=False)
    cht_agt_id = Column(String(80), ForeignKey("agents.agt_id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan", order_by="ChatMessage.creation_dt")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    msg_id = Column(String(80), primary_key=True)
    msg_cht_id = Column(String(80), ForeignKey("chat_sessions.cht_id", ondelete="CASCADE"), nullable=False)
    msg_agent_name = Column(String(240), nullable=False)
    msg_role = Column(String(30), nullable=False)
    msg_content = Column(Text, nullable=False)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Check constraint for role values
    __table_args__ = (
        CheckConstraint("msg_role IN ('system', 'user', 'assistant', 'tool_input', 'tool_response')", name='check_msg_role'),
    )

    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")