import pytest
from fastapi.testclient import TestClient
from main import app


def test_portfolio_crud(test_app: TestClient):
    """Test portfolio CRUD operations"""
    # Test get empty portfolio - first clear any existing items
    # Get all items first and delete them
    get_response = test_app.get("/api/portfolio")
    assert get_response.status_code == 200

    # Clear any existing items
    for item in get_response.json():
        test_app.delete(f"/api/portfolio/{item['ticker']}")

    # Test get all portfolio is now empty
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Test add item
    item_data = {
        "ticker": "AAPL",
        "quantity": 100,
        "cost_price": 150.0,
        "note": "Test note"
    }
    response = test_app.post("/api/portfolio", json=item_data)
    assert response.status_code == 201

    # Test get all items has one item
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ticker"] == "AAPL"

    # Test get single item
    response = test_app.get("/api/portfolio/AAPL")
    assert response.status_code == 200
    assert response.json()["ticker"] == "AAPL"
    assert response.json()["quantity"] == 100

    # Test update item
    update_data = {
        "quantity": 150,
        "note": "Updated note"
    }
    response = test_app.put("/api/portfolio/AAPL", json=update_data)
    assert response.status_code == 200
    assert response.json()["quantity"] == 150
    assert response.json()["note"] == "Updated note"

    # Test delete item
    response = test_app.delete("/api/portfolio/AAPL")
    assert response.status_code == 204

    # Test portfolio is now empty
    response = test_app.get("/api/portfolio")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_portfolio_summary(test_app: TestClient):
    """Test portfolio summary endpoint"""
    # Clear any existing items
    get_response = test_app.get("/api/portfolio")
    for item in get_response.json():
        test_app.delete(f"/api/portfolio/{item['ticker']}")

    # Test empty portfolio summary
    response = test_app.get("/api/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_market_value"] == 0.0
    assert data["total_cost"] == 0.0
    assert data["total_profit_loss"] == 0.0
    assert data["total_profit_loss_percent"] == 0.0
    assert data["holdings_count"] == 0


def test_update_nonexistent_portfolio_item(test_app: TestClient):
    """Test updating a nonexistent portfolio item"""
    response = test_app.put("/api/portfolio/INVALID", json={"quantity": 50})
    assert response.status_code == 404


def test_delete_nonexistent_portfolio_item(test_app: TestClient):
    """Test deleting a nonexistent portfolio item"""
    response = test_app.delete("/api/portfolio/INVALID")
    assert response.status_code == 404
