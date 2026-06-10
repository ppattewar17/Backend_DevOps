#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Transaction Processing API Test Script${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if API is running
echo -e "${YELLOW}Checking API health...${NC}"
HEALTH=$(curl -s $API_URL/)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API is not running!${NC}"
    echo "Please start the application with: docker compose up"
    exit 1
fi
echo -e "${GREEN}✓ API is healthy${NC}"
echo ""

# Check if transactions.csv exists
if [ ! -f "transactions.csv" ]; then
    echo -e "${RED}❌ transactions.csv not found!${NC}"
    echo "Please ensure transactions.csv is in the current directory."
    exit 1
fi

# Upload CSV
echo -e "${YELLOW}Uploading transactions.csv...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST $API_URL/jobs \
  -F "file=@transactions.csv")

echo "$UPLOAD_RESPONSE" | jq '.'

# Extract job ID
JOB_ID=$(echo $UPLOAD_RESPONSE | jq -r '.job_id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo -e "${RED}❌ Failed to create job!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Job created: $JOB_ID${NC}"
echo ""

# Poll for completion
echo -e "${YELLOW}Waiting for job to complete...${NC}"
COMPLETED=false
ATTEMPTS=0
MAX_ATTEMPTS=60  # 5 minutes (60 * 5 seconds)

while [ $COMPLETED = false ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    sleep 5
    ATTEMPTS=$((ATTEMPTS + 1))
    
    STATUS_RESPONSE=$(curl -s $API_URL/jobs/$JOB_ID)
    STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
    ROW_COUNT_RAW=$(echo $STATUS_RESPONSE | jq -r '.row_count_raw // "N/A"')
    ROW_COUNT_CLEAN=$(echo $STATUS_RESPONSE | jq -r '.row_count_clean // "N/A"')
    
    echo -e "${BLUE}Status: $STATUS | Raw: $ROW_COUNT_RAW | Clean: $ROW_COUNT_CLEAN${NC}"
    
    if [ "$STATUS" = "COMPLETED" ]; then
        COMPLETED=true
        echo -e "${GREEN}✓ Job completed successfully!${NC}"
    elif [ "$STATUS" = "FAILED" ]; then
        echo -e "${RED}❌ Job failed!${NC}"
        ERROR=$(echo $STATUS_RESPONSE | jq -r '.error_message')
        echo "Error: $ERROR"
        exit 1
    fi
done

if [ $COMPLETED = false ]; then
    echo -e "${RED}❌ Job did not complete within timeout${NC}"
    exit 1
fi

echo ""

# Get full job details
echo -e "${YELLOW}Job Details:${NC}"
curl -s $API_URL/jobs/$JOB_ID | jq '.'
echo ""

# Get summary
echo -e "${YELLOW}Fetching summary...${NC}"
SUMMARY=$(curl -s $API_URL/jobs/$JOB_ID/summary)

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to fetch summary${NC}"
    exit 1
fi

echo "$SUMMARY" | jq '.'
echo ""

# Display key metrics
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Summary Highlights${NC}"
echo -e "${BLUE}=========================================${NC}"

TOTAL_INR=$(echo $SUMMARY | jq -r '.total_spend_inr')
TOTAL_USD=$(echo $SUMMARY | jq -r '.total_spend_usd')
ANOMALY_COUNT=$(echo $SUMMARY | jq -r '.anomaly_count')
RISK_LEVEL=$(echo $SUMMARY | jq -r '.risk_level')
NARRATIVE=$(echo $SUMMARY | jq -r '.narrative')

echo -e "${GREEN}Total Spend (INR):${NC} ₹$TOTAL_INR"
echo -e "${GREEN}Total Spend (USD):${NC} \$$TOTAL_USD"
echo -e "${GREEN}Anomalies Detected:${NC} $ANOMALY_COUNT"
echo -e "${GREEN}Risk Level:${NC} $RISK_LEVEL"
echo ""
echo -e "${GREEN}Narrative:${NC}"
echo "$NARRATIVE"
echo ""

# Display top merchants
echo -e "${BLUE}Top Merchants:${NC}"
echo $SUMMARY | jq -r '.top_merchants[] | "  \(.merchant): \(.count) transactions, ₹\(.total_amount)"'
echo ""

# List all jobs
echo -e "${YELLOW}Listing all jobs...${NC}"
curl -s "$API_URL/jobs" | jq -r '.[] | "[\(.status)] \(.filename) - Created: \(.created_at)"'
echo ""

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✓ Test completed successfully!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Job ID: $JOB_ID"
echo "Summary URL: $API_URL/jobs/$JOB_ID/summary"
echo "API Docs: $API_URL/docs"
echo ""
