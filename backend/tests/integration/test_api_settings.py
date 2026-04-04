import pytest
from fastapi.testclient import TestClient
from main import app


def test_get_settings(test_app: TestClient):
    """Test getting user settings"""
    response = test_app.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "investment_style" in data
    assert "llm_config" in data
    assert data["investment_style"] == "balanced"
    assert data["llm_config"]["provider"] == "openrouter"


def test_update_investment_style(test_app: TestClient):
    """Test updating investment style"""
    # Test valid investment style
    response = test_app.put("/api/settings/investment-style",
                           json={"investment_style": "conservative"})
    assert response.status_code == 200
    assert response.json()["investment_style"] == "conservative"

    # Test another valid style
    response = test_app.put("/api/settings/investment-style",
                           json={"investment_style": "aggressive"})
    assert response.status_code == 200
    assert response.json()["investment_style"] == "aggressive"

    # Reset to balanced
    response = test_app.put("/api/settings/investment-style",
                           json={"investment_style": "balanced"})
    assert response.status_code == 200
    assert response.json()["investment_style"] == "balanced"


def test_update_invalid_investment_style(test_app: TestClient):
    """Test updating with invalid investment style"""
    response = test_app.put("/api/settings/investment-style",
                           json={"investment_style": "invalid"})
    assert response.status_code == 400


def test_update_model_config(test_app: TestClient):
    """Test updating model configuration"""
    update_data = {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.5,
        "max_tokens": 3000
    }

    response = test_app.put("/api/settings/model-config", json=update_data)
    assert response.status_code == 200
    data = response.json()

    assert data["llm_config"]["provider"] == "openai"
    assert data["llm_config"]["model"] == "gpt-4"
    assert data["llm_config"]["temperature"] == 0.5
    assert data["llm_config"]["max_tokens"] == 3000

    # Reset to default
    default_data = {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "temperature": 0.7,
        "max_tokens": 2000
    }
    response = test_app.put("/api/settings/model-config", json=default_data)
    assert response.status_code == 200


def test_get_providers(test_app: TestClient):
    """Test getting providers list"""
    response = test_app.get("/api/settings/providers")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_invalid_provider_validation(test_app: TestClient):
    """Test getting invalid provider validation"""
    response = test_app.get("/api/settings/providers/invalid/validate")
    assert response.status_code == 400
