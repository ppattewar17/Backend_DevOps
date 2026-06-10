import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db, init_db
from app.models import Job, JobSummary, JobStatus
from app.schemas import (
    JobCreate,
    JobResponse,
    JobSummaryResponse,
    ErrorResponse,
    MerchantStat
)
from app.tasks import process_transaction_file
from app.config import get_settings

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Transaction Processing Pipeline API",
    description="AI-powered transaction processing and anomaly detection",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    
    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Transaction Processing Pipeline API",
        "version": "1.0.0"
    }


@app.post("/jobs", response_model=JobCreate, tags=["Jobs"])
async def create_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file and create processing job
    
    - **file**: CSV file containing transaction data
    
    Returns job ID and status
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are accepted."
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    try:
        # Create job record
        job = Job(filename=file.filename)
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Save uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, f"{job.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Queue processing task
        process_transaction_file.delay(str(job.id), file_path)
        
        return JobCreate(
            job_id=job.id,
            status=job.status.value,
            message="Job created successfully. Processing started."
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get job status and details
    
    - **job_id**: UUID of the job
    
    Returns job information including status, row counts, and timestamps
    """
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(
            id=job.id,
            filename=job.filename,
            status=job.status.value,
            row_count_raw=job.row_count_raw,
            row_count_clean=job.row_count_clean,
            created_at=job.created_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}/summary", response_model=JobSummaryResponse, tags=["Jobs"])
async def get_job_summary(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processed job summary with insights
    
    - **job_id**: UUID of the job
    
    Returns aggregated statistics, top merchants, anomaly count, and AI-generated narrative
    """
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed yet. Current status: {job.status.value}"
            )
        
        summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
        
        if not summary:
            raise HTTPException(status_code=404, detail="Job summary not found")
        
        # Format top merchants
        top_merchants = [
            MerchantStat(**merchant)
            for merchant in summary.top_merchants
        ]
        
        return JobSummaryResponse(
            job_id=summary.job_id,
            total_spend_inr=summary.total_spend_inr,
            total_spend_usd=summary.total_spend_usd,
            top_merchants=top_merchants,
            anomaly_count=summary.anomaly_count,
            narrative=summary.narrative,
            risk_level=summary.risk_level
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs", response_model=List[JobResponse], tags=["Jobs"])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, PROCESSING, COMPLETED, FAILED"),
    db: Session = Depends(get_db)
):
    """
    List all jobs with optional status filtering
    
    - **status**: Optional filter by job status
    
    Returns list of jobs with their details
    """
    try:
        query = db.query(Job)
        
        # Apply status filter if provided
        if status:
            try:
                status_enum = JobStatus[status.upper()]
                query = query.filter(Job.status == status_enum)
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Valid values: {', '.join([s.value for s in JobStatus])}"
                )
        
        # Order by creation date (newest first)
        jobs = query.order_by(Job.created_at.desc()).all()
        
        return [
            JobResponse(
                id=job.id,
                filename=job.filename,
                status=job.status.value,
                row_count_raw=job.row_count_raw,
                row_count_clean=job.row_count_clean,
                created_at=job.created_at,
                completed_at=job.completed_at,
                error_message=job.error_message
            )
            for job in jobs
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": str(exc.detail)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )
