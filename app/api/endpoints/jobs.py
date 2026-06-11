import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models import Job, JobSummary, Transaction, JobStatus
from app.schemas.job import (
    JobUploadResponse,
    JobStatusResponse,
    JobListItem,
    JobResultsResponse,
    TransactionDetail,
    JobSummaryDetail,
    MerchantStat
)
from app.workers.tasks import process_transaction_file
from app.core.config import get_settings

settings = get_settings()

router = APIRouter()


@router.post("/upload", response_model=JobUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    POST /jobs/upload
    
    Upload CSV file and create processing job
    - Validates file format
    - Creates job record
    - Queues processing task
    - Returns job_id and status
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are accepted."
        )
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    try:
        # Create job record
        job = Job(filename=file.filename, status=JobStatus.PENDING)
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Create uploads directory if not exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{job.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Queue processing task
        process_transaction_file.delay(str(job.id), file_path)
        
        return JobUploadResponse(
            job_id=job.id,
            status=job.status.value
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    GET /jobs/{job_id}/status
    
    Get job status and progress
    - Returns status, progress percentage
    - Includes summary if completed
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress
    )
    
    # Include summary if completed
    if job.status == JobStatus.COMPLETED:
        summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
        if summary:
            response.summary = {
                "total_spend_inr": summary.total_spend_inr,
                "total_spend_usd": summary.total_spend_usd,
                "top_merchants": summary.top_merchants,
                "anomaly_count": summary.anomaly_count,
                "narrative": summary.narrative,
                "risk_level": summary.risk_level
            }
    
    return response


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    GET /jobs/{job_id}/results
    
    Get complete job results including:
    - Job details
    - All cleaned transactions
    - Anomalies list
    - Category breakdown
    - LLM summary
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job.status.value}"
        )
    
    # Get all transactions
    transactions = db.query(Transaction).filter(Transaction.job_id == job_id).all()
    
    # Get anomalies
    anomalies = [t for t in transactions if t.is_anomaly]
    
    # Calculate category breakdown
    category_breakdown = {}
    for t in transactions:
        category = t.llm_category or t.category or 'Uncategorised'
        category_breakdown[category] = category_breakdown.get(category, 0) + 1
    
    # Get summary
    summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Job summary not found")
    
    # Format top merchants
    top_merchants = [MerchantStat(**m) for m in summary.top_merchants]
    
    return JobResultsResponse(
        job=JobListItem.model_validate(job),
        cleaned_transactions=[TransactionDetail.model_validate(t) for t in transactions],
        anomalies=[TransactionDetail.model_validate(t) for t in anomalies],
        category_breakdown=category_breakdown,
        llm_summary=JobSummaryDetail(
            total_spend_inr=summary.total_spend_inr,
            total_spend_usd=summary.total_spend_usd,
            top_merchants=top_merchants,
            anomaly_count=summary.anomaly_count,
            narrative=summary.narrative,
            risk_level=summary.risk_level
        )
    )


@router.get("", response_model=List[JobListItem])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status: pending, processing, completed, failed"),
    db: Session = Depends(get_db)
):
    """
    GET /jobs
    
    List all jobs with optional status filtering
    - Supports ?status=pending
    - Supports ?status=completed
    - Supports ?status=failed
    """
    query = db.query(Job)
    
    # Apply status filter if provided
    if status:
        try:
            status_enum = JobStatus[status.upper()]
            query = query.filter(Job.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid values: pending, processing, completed, failed"
            )
    
    # Order by creation date (newest first)
    jobs = query.order_by(Job.created_at.desc()).all()
    
    return [JobListItem.model_validate(job) for job in jobs]
