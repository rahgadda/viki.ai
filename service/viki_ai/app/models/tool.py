from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime


class Tool(Base):
    __tablename__ = "tools"

    tol_id = Column(String(80), primary_key=True)
    tol_name = Column(String(240), nullable=False)
    tol_description = Column(String(4000))
    tol_mcp_command = Column(String(240), nullable=False)
    tol_mcp_function_count = Column(Integer, default=0)
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    environment_variables = relationship("ToolEnvironmentVariable", back_populates="tool", cascade="all, delete-orphan")
    resources = relationship("ToolResource", back_populates="tool", cascade="all, delete-orphan")
    agent_tools = relationship("AgentTool", back_populates="tool")


class ToolEnvironmentVariable(Base):
    __tablename__ = "tool_environment_variables"

    tev_tol_id = Column(String(80), ForeignKey("tools.tol_id", ondelete="CASCADE"), primary_key=True)
    tev_key = Column(String(240), primary_key=True)
    tev_value = Column(String(4000))
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    tool = relationship("Tool", back_populates="environment_variables")


class ToolResource(Base):
    __tablename__ = "tool_resources"

    tre_tol_id = Column(String(80), ForeignKey("tools.tol_id", ondelete="CASCADE"), primary_key=True)
    tre_resource_name = Column(String(240), primary_key=True)
    tre_resource_description = Column(String(4000))
    created_by = Column(String(80))
    last_updated_by = Column(String(80))
    creation_dt = Column(DateTime, default=datetime.utcnow)
    last_updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    tool = relationship("Tool", back_populates="resources")