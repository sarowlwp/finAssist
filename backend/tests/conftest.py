import pytest
import httpx
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile

from main import app
from config import config


@pytest.fixture(scope="function")
def test_app():
    """Create a test client with temporary data directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config.DATA_DIR = Path(temp_dir)
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def sample_portfolio_item():
    """Sample portfolio item for testing"""
    return {
        "ticker": "AAPL",
        "quantity": 100,
        "avg_price": 150.0,
        "purchase_date": "2026-04-04"
    }


@pytest.fixture
def sample_model_config():
    """Sample model configuration"""
    return {
        "provider": "openrouter",
        "api_key": "test-api-key",
        "model": "anthropic/claude-3.5-sonnet",
        "base_url": "https://openrouter.ai/api/v1"
    }
