import pytest
from fastapi.testclient import TestClient


def test_get_current_user(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "demo-user"
    assert data["email"] == "demo@local"
    assert data["name"] == "Demo User"
    assert "admin" in data["roles"]


def test_update_current_user(client: TestClient):
    response = client.patch("/api/v1/users/me", json={"name": "Updated Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"