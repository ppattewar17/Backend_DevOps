#!/bin/bash

echo "========================================="
echo "Transaction Processing Pipeline"
echo "Quick Start Script"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OPENAI_API_KEY"
    echo ""
    echo "Run this script again after adding your API key."
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OPENAI_API_KEY not configured in .env file"
    echo ""
    echo "Please edit .env and add your OpenAI API key:"
    echo "OPENAI_API_KEY=sk-your-api-key-here"
    echo ""
    exit 1
fi

echo "✓ Environment configured"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

echo "Starting services with Docker Compose..."
echo ""

docker compose up --build -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "========================================="
echo "✓ Application Started Successfully!"
echo "========================================="
echo ""
echo "📌 API Endpoint: http://localhost:8000"
echo "📌 API Docs: http://localhost:8000/docs"
echo "📌 ReDoc: http://localhost:8000/redoc"
echo ""
echo "========================================="
echo "Quick Test"
echo "========================================="
echo ""

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8000/ | jq '.' || echo "Waiting for API to be ready..."

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Upload a CSV file:"
echo "   curl -X POST http://localhost:8000/jobs -F \"file=@transactions.csv\""
echo ""
echo "2. Check job status:"
echo "   curl http://localhost:8000/jobs/{job_id}"
echo ""
echo "3. Get summary (after completion):"
echo "   curl http://localhost:8000/jobs/{job_id}/summary"
echo ""
echo "4. View logs:"
echo "   docker compose logs -f"
echo ""
echo "5. Stop services:"
echo "   docker compose down"
echo ""
echo "See EXAMPLES.md for more usage examples."
echo ""
