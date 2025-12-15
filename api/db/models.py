from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .session import Base

class BatchJobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some items completed, some failed
    FAILED = "failed"
    CANCELLED = "cancelled"

class ServiceClient(Base):
    __tablename__ = "service_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, unique=True, index=True, nullable=False)  # e.g., "colegio-alas-prod"
    api_key_hash = Column(String, nullable=False)  # Hashed API key
    permissions = Column(JSON, default=list)  # List of allowed endpoints/operations
    rate_limit = Column(Integer, default=100)  # Requests per minute
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    webhook_url = Column(String, nullable=True)  # For async notifications

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

class BatchJob(Base):
    __tablename__ = "batch_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(Integer, ForeignKey("service_clients.id"), nullable=False)
    
    # Job configuration
    job_type = Column(String, nullable=False)  # quiz, activity, exam, reinforcement, lesson
    total_items = Column(Integer, nullable=False)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # Status
    status = Column(SQLAlchemyEnum(BatchJobStatus), default=BatchJobStatus.PENDING)
    progress_percent = Column(Float, default=0.0)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    results = Column(JSON, default=list)  # List of {item_id, status, result_or_error}
    
    # Webhook
    webhook_url = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)
    webhook_last_sent = Column(DateTime, nullable=True)
    
    # Metadata
    job_metadata = Column(JSON, default=dict)