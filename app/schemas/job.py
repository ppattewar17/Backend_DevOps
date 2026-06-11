from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class JobUploadResponse(BaseModel):
    """Response for job upload"""
    job_id: UUID
    status: str


class JobStatusResponse(BaseModel):
    """Response for job status"""
    job_id: UUID
    status: str
    progress: int
    summary: Optional[Dict[str, Any]] = None


class JobListItem(BaseModel):
    """Job list item"""
    id: UUID
    filename: str
    status: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionDetail(BaseModel):
    """Transaction detail"""
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


class MerchantStat(BaseModel):
    """Merchant statistics"""
    merchant: str
    count: int
    total_amount: float


class JobSummaryDetail(BaseModel):
    """Job summary detail"""
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: List[MerchantStat]
    anomaly_count: int
    narrative: Optional[str] = None
    risk_level: Optional[str] = None


class JobResultsResponse(BaseModel):
    """Complete job results"""
    job: JobListItem
    cleaned_transactions: List[TransactionDetail]
    anomalies: List[TransactionDetail]
    category_breakdown: Dict[str, int]
    llm_summary: JobSummaryDetail
