from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)
    role = Column(String, default="user")

    # Relación uno a muchos con los registros de planificación
    planning_logs = relationship("PlanningLog", back_populates="user")

class PlanningLog(Base):
    __tablename__ = "planning_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    oa_codigo = Column(String, index=True)
    cost = Column(Float)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    thought_tokens = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Campos para almacenar el contexto completo de la planificación
    plan_request_data = Column(JSON)
    plan_markdown = Column(Text)

    # Relación muchos a uno con el usuario
    user = relationship("User", back_populates="planning_logs")