import pytest
from fastapi.testclient import TestClient
from main import app


def test_health_endpoint(test_app: TestClient):
    """Test health check endpoint"""
    response = test_app.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(test_app: TestClient):
    """Test root endpoint"""
    response = test_app.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["version"] == "0.1.0"
