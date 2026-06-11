from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base


class Transaction(Base):
    """Transaction model for storing processed transactions"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    
    # Original data
    txn_id = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    merchant = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String, nullable=False)
    category = Column(String, nullable=True)
    account_id = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Anomaly detection
    is_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(Text, nullable=True)
    
    # LLM processing
    llm_category = Column(String, nullable=True)
    llm_raw_response = Column(Text, nullable=True)
    llm_failed = Column(Boolean, default=False)
    
    # Relationships
    job = relationship("Job", back_populates="transactions")
