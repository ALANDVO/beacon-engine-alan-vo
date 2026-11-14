import pytest
from fastapi.testclient import TestClient


def test_get_current_user(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "demo-user"
    assert data["email"] == "demo@local"
    assert "admin" in data["roles"]


def test_update_current_user(client: TestClient):
    response = client.patch("/api/v1/users/me", json={"name": "Updated Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_login(client: TestClient):
    # Login sets a cookie
    response = client.post("/api/v1/users/login")
    assert response.status_code == 200
    # Check that cookie is set
    # TestClient stores cookies in .cookies dict
    assert "access_token" in client.cookies
    token = client.cookies["access_token"]
    # Verify token is present (non-empty)
    assert token != ""


def test_logout(client: TestClient):
    # Logout should clear cookie
    response = client.post("/api/v1/users/logout")
    assert response.status_code == 200
    # After logout, cookie should be removed
    assert "access_token" not in client.cookies


def test_login_then_get_user(client: TestClient):
    # First login
    response_login = client.post("/api/v1/users/login")
    assert response_login.status_code == 200
    # Then get current user
    response_get = client.get("/api/v1/users/me")
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["id"] == "demo-user"
    assert data["email"] == "demo@local"
