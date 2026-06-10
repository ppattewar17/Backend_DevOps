import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_job_no_file():
    """Test job creation without file"""
    response = client.post("/jobs")
    assert response.status_code == 422  # Validation error


def test_list_jobs():
    """Test listing jobs"""
    response = client.get("/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_jobs_with_filter():
    """Test listing jobs with status filter"""
    response = client.get("/jobs?status=COMPLETED")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_job():
    """Test getting non-existent job"""
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
