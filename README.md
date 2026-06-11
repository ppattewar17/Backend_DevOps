# AI-Powered Transaction Processing Pipeline

A production-ready backend API that processes financial transaction CSV files asynchronously using AI/LLM for intelligent classification and anomaly detection.

## 🎯 Overview
This system accepts CSV files containing financial transactions, processes them through an automated pipeline that cleans data, detects anomalies, classifies transactions using AI, and generates intelligent narrative summaries with risk assessments.

## 🏗️ Architecture
- **API Server**: FastAPI-based REST API for job management
- **Database**: PostgreSQL for persistent data storage
- **Queue**: Redis + Celery for distributed async processing
- **Worker**: Background workers for CSV processing pipeline
- **AI/LLM**: OpenAI GPT-4o-mini for classification and insights
- **Mock LLM**: Use `llm_service_mock.py` for testing without API key (rename to `llm_service.py`)

## ✨ Features
- ✅ **POST /jobs/upload** - CSV file upload with validation
- ✅ **GET /jobs/{job_id}/status** - Job polling with progress tracking
- ✅ **GET /jobs/{job_id}/results** - Full structured results
- ✅ **GET /jobs** - List all jobs with status filtering
- ✅ Data cleaning and normalization
- ✅ Statistical anomaly detection
- ✅ AI-powered transaction classification (batched)
- ✅ Intelligent narrative summary generation
- ✅ Retry logic with exponential backoff (1s, 2s, 4s)
- ✅ Graceful LLM failure handling
- ✅ One-command Docker Compose deployment

## Prerequisites
- Docker and Docker Compose
- OpenAI API Key

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Backend_DevOps_Assignment
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:password@db:5432/transactions_db
REDIS_URL=redis://redis:6379/0
```

### 3. Start the Application
```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Upload CSV and Create Job
```bash
curl -X POST http://localhost:8000/jobs/upload \
  -F "file=@transactions.csv"
```

**Response:**
```json
{
  "job_id": "f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",
  "status": "pending"
}
```

### 2. Get Job Status
```bash
curl http://localhost:8000/jobs/{job_id}/status
```

**Response:**
```json
{
  "job_id": "f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",
  "status": "processing",
  "progress": 45,
  "summary": null
}
```

When completed:
```json
{
  "job_id": "f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",
  "status": "completed",
  "progress": 100,
  "summary": {
    "total_spend_inr": 250000.50,
    "total_spend_usd": 3500.25,
    "top_merchants": [
      {"merchant": "Amazon", "count": 25, "total_amount": 45000.0},
      {"merchant": "Swiggy", "count": 18, "total_amount": 12500.0}
    ],
    "anomaly_count": 12,
    "narrative": "High spending observed on shopping platforms...",
    "risk_level": "medium"
  }
}
```

### 3. Get Job Results (Full Details)
```bash
curl http://localhost:8000/jobs/{job_id}/results
```

**Response:**
```json
{
  "job": {
    "id": "uuid",
    "filename": "transactions.csv",
    "status": "completed",
    "row_count_raw": 90,
    "row_count_clean": 85,
    "created_at": "2024-06-10T10:30:00Z",
    "completed_at": "2024-06-10T10:32:15Z"
  },
  "cleaned_transactions": [...],
  "anomalies": [...],
  "category_breakdown": {
    "Food": 25000.00,
    "Shopping": 45000.00,
    "Travel": 15000.00
  },
  "llm_summary": {
    "narrative": "...",
    "risk_level": "medium"
  }
}
```

### 4. List All Jobs
```bash
# All jobs
curl http://localhost:8000/jobs

# Filter by status
curl "http://localhost:8000/jobs?status=completed"
curl "http://localhost:8000/jobs?status=pending"
curl "http://localhost:8000/jobs?status=processing"
curl "http://localhost:8000/jobs?status=failed"
```

**Response:**
```json
[
  {
    "id": "uuid",
    "filename": "transactions.csv",
    "status": "completed",
    "row_count_raw": 90,
    "row_count_clean": 85,
    "created_at": "2024-06-10T10:30:00Z"
  }
]
```

## Processing Pipeline

### 1. Data Cleaning
- Normalize dates to ISO 8601 format
- Strip currency symbols ($, ₹, etc.)
- Uppercase status values
- Fill missing categories with 'Uncategorised'
- Remove exact duplicate rows

### 2. Anomaly Detection
- Flag transactions exceeding 3x account median
- Flag USD currency with domestic-only merchants (Swiggy, Ola, IRCTC)

### 3. LLM Classification
- Batch classification for missing categories
- Categories: Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other

### 4. LLM Narrative Summary
- Total spend by currency
- Top 3 merchants
- Anomaly analysis
- Spending narrative (2-3 sentences)
- Risk level assessment (low/medium/high)

### 5. Retry Logic
- 3 retries with exponential backoff
- Failed batches marked as `llm_failed`
- Graceful degradation (job continues on LLM failure)

## Database Schema

### Jobs Table
```sql
- id (UUID, PK)
- filename (VARCHAR)
- status (ENUM: PENDING, PROCESSING, COMPLETED, FAILED)
- row_count_raw (INTEGER)
- row_count_clean (INTEGER)
- created_at (TIMESTAMP)
- completed_at (TIMESTAMP)
- error_message (TEXT)
```

### Transactions Table
```sql
- id (UUID, PK)
- job_id (UUID, FK)
- txn_id (VARCHAR)
- date (DATE)
- merchant (VARCHAR)
- amount (DECIMAL)
- currency (VARCHAR)
- status (VARCHAR)
- category (VARCHAR)
- account_id (VARCHAR)
- is_anomaly (BOOLEAN)
- anomaly_reason (TEXT)
- llm_category (VARCHAR)
- llm_raw_response (TEXT)
- llm_failed (BOOLEAN)
```

### JobSummary Table
```sql
- id (UUID, PK)
- job_id (UUID, FK)
- total_spend_inr (DECIMAL)
- total_spend_usd (DECIMAL)
- top_merchants (JSON)
- anomaly_count (INTEGER)
- narrative (TEXT)
- risk_level (VARCHAR)
```

## Tech Stack
- **API**: FastAPI (Python)
- **Database**: PostgreSQL
- **Queue**: Redis + Celery
- **LLM**: OpenAI GPT-4o-mini
- **ORM**: SQLAlchemy
- **Containerization**: Docker + Docker Compose

## Development

### Run Tests
```bash
docker compose exec api pytest tests/
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f worker
```

### Database Migrations
```bash
docker compose exec api alembic upgrade head
```

## Scalability Considerations

### Current Bottlenecks (at 100x scale):
1. **Database connections**: Limited connection pool
2. **LLM API rate limits**: OpenAI API throttling
3. **Memory**: In-memory CSV processing
4. **Single worker**: Sequential job processing

### Production Improvements:
1. **Database**: Read replicas, connection pooling (PgBouncer)
2. **LLM**: Rate limiting, caching, fallback to smaller models
3. **File Storage**: S3/MinIO for CSV files
4. **Workers**: Horizontal scaling with Kubernetes
5. **Queue**: Separate queues for priority jobs
6. **Caching**: Redis caching for summary data
7. **Monitoring**: Prometheus + Grafana
8. **Load Balancer**: Nginx for API distribution

## License
MIT

## Author
[Your Name]
