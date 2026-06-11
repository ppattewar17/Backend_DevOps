import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Job, Transaction, JobSummary, JobStatus
from app.services.data_cleaner import DataCleaner
from app.services.anomaly_detector import AnomalyDetector
from app.services.llm_service import LLMService
from app.core.config import get_settings

settings = get_settings()


@celery_app.task(bind=True, name="app.workers.tasks.process_transaction_file")
def process_transaction_file(self, job_id: str, file_path: str):
    """
    Process transaction CSV file asynchronously with progress tracking
    
    Args:
        job_id: UUID of the job
        file_path: Path to uploaded CSV file
    """
    db: Session = SessionLocal()
    
    try:
        # Update job status to PROCESSING
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = JobStatus.PROCESSING
        job.progress = 10
        db.commit()
        
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Step 1: Data Cleaning (20% progress)
        job.progress = 20
        db.commit()
        
        cleaner = DataCleaner()
        df_cleaned, raw_count, clean_count = cleaner.clean_data(df)
        
        job.row_count_raw = raw_count
        job.row_count_clean = clean_count
        job.progress = 30
        db.commit()
        
        # Step 2: Anomaly Detection (40% progress)
        job.progress = 40
        db.commit()
        
        detector = AnomalyDetector()
        df_with_anomalies = detector.detect_anomalies(df_cleaned)
        
        # Step 3: Save transactions to database (50% progress)
        job.progress = 50
        db.commit()
        
        transactions = []
        for _, row in df_with_anomalies.iterrows():
            transaction = Transaction(
                job_id=job_id,
                txn_id=row['txn_id'],
                date=row['date'],
                merchant=row['merchant'],
                amount=row['amount'],
                currency=row['currency'],
                status=row['status'],
                category=row.get('category'),
                account_id=row['account_id'],
                notes=row.get('notes', ''),
                is_anomaly=row.get('is_anomaly', False),
                anomaly_reason=row.get('anomaly_reason', None)
            )
            transactions.append(transaction)
            db.add(transaction)
        
        db.commit()
        
        # Step 4: LLM Classification for missing categories (70% progress)
        job.progress = 70
        db.commit()
        
        llm_service = LLMService()
        transactions_without_category = [
            t for t in transactions 
            if not t.category or t.category.lower() == 'uncategorised'
        ]
        
        if transactions_without_category:
            try:
                categories = llm_service.classify_transactions_batch(
                    transactions_without_category
                )
                
                for transaction, category_data in zip(transactions_without_category, categories):
                    transaction.llm_category = category_data.get('category', 'Other')
                    transaction.llm_raw_response = str(category_data)
                    transaction.llm_failed = False
                
                db.commit()
            except Exception as e:
                print(f"LLM Classification failed after retries: {e}")
                for transaction in transactions_without_category:
                    transaction.llm_failed = True
                db.commit()
        
        # Step 5: Generate Summary (80% progress)
        job.progress = 80
        db.commit()
        
        summary_data = _generate_summary(db, job_id, transactions)
        
        # Step 6: LLM Narrative Generation (90% progress)
        job.progress = 90
        db.commit()
        
        try:
            narrative_data = llm_service.generate_summary(summary_data, transactions)
            summary_data.update(narrative_data)
        except Exception as e:
            print(f"LLM Narrative generation failed after retries: {e}")
            summary_data['narrative'] = "Unable to generate narrative due to LLM failure"
            summary_data['risk_level'] = "unknown"
        
        # Save summary
        job_summary = JobSummary(
            job_id=job_id,
            total_spend_inr=summary_data['total_spend_inr'],
            total_spend_usd=summary_data['total_spend_usd'],
            top_merchants=summary_data['top_merchants'],
            anomaly_count=summary_data['anomaly_count'],
            narrative=summary_data.get('narrative'),
            risk_level=summary_data.get('risk_level')
        )
        db.add(job_summary)
        
        # Update job status to COMPLETED (100% progress)
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.completed_at = datetime.utcnow()
        db.commit()
        
        return {"status": "success", "job_id": job_id}
    
    except Exception as e:
        # Update job status to FAILED
        if db.query(Job).filter(Job.id == job_id).first():
            job = db.query(Job).filter(Job.id == job_id).first()
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise e
    
    finally:
        db.close()
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)


def _generate_summary(db: Session, job_id: str, transactions: list) -> dict:
    """Generate summary statistics from transactions"""
    
    # Calculate total spend by currency
    total_inr = sum(
        t.amount for t in transactions 
        if t.currency.upper() == 'INR'
    )
    total_usd = sum(
        t.amount for t in transactions 
        if t.currency.upper() == 'USD'
    )
    
    # Get top 3 merchants
    merchant_stats = {}
    for t in transactions:
        if t.merchant not in merchant_stats:
            merchant_stats[t.merchant] = {'count': 0, 'total_amount': 0}
        merchant_stats[t.merchant]['count'] += 1
        merchant_stats[t.merchant]['total_amount'] += t.amount
    
    top_merchants = sorted(
        [
            {
                'merchant': merchant,
                'count': stats['count'],
                'total_amount': round(stats['total_amount'], 2)
            }
            for merchant, stats in merchant_stats.items()
        ],
        key=lambda x: x['count'],
        reverse=True
    )[:3]
    
    # Count anomalies
    anomaly_count = sum(1 for t in transactions if t.is_anomaly)
    
    return {
        'total_spend_inr': round(total_inr, 2),
        'total_spend_usd': round(total_usd, 2),
        'top_merchants': top_merchants,
        'anomaly_count': anomaly_count
    }
