from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class JobCreate(BaseModel):
    """Schema for job creation response"""
    job_id: UUID
    status: str
    message: str


class JobResponse(BaseModel):
    """Schema for job status response"""
    id: UUID
    filename: str
    status: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class MerchantStat(BaseModel):
    """Schema for merchant statistics"""
    merchant: str
    count: int
    total_amount: float


class JobSummaryResponse(BaseModel):
    """Schema for job summary response"""
    job_id: UUID
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: List[MerchantStat]
    anomaly_count: int
    narrative: Optional[str] = None
    risk_level: Optional[str] = None
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    id: UUID
    txn_id: str
    date: datetime
    merchant: str
    amount: float
    currency: str
    status: str
    category: Optional[str] = None
    account_id: str
    is_anomaly: bool
    anomaly_reason: Optional[str] = None
    llm_category: Optional[str] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
