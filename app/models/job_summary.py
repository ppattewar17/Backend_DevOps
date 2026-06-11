from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class JobSummary(Base):
    """Job summary model for storing aggregated results"""
    __tablename__ = "job_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, unique=True)
    
    # Spending totals
    total_spend_inr = Column(Float, default=0.0)
    total_spend_usd = Column(Float, default=0.0)
    
    # Top merchants (JSON array)
    top_merchants = Column(JSON, nullable=True)
    
    # Anomaly count
    anomaly_count = Column(Integer, default=0)
    
    # LLM generated fields
    narrative = Column(Text, nullable=True)
    risk_level = Column(String, nullable=True)  # low/medium/high
    
    # Relationships
    job = relationship("Job", back_populates="summary")
