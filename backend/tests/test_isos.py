import pytest
from fastapi.testclient import TestClient

from tests.test_iso_fixture import VALID_ISO_CONTENT


def test_upload_iso(client: TestClient):
    file_content = VALID_ISO_CONTENT
    files = {"file": ("test.iso", file_content, "application/octet-stream")}
    response = client.post("/api/v1/isos", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.iso"
    assert data["size_bytes"] == len(file_content)
    assert len(data["sha256"]) == 64


def test_upload_duplicate_iso(client: TestClient):
    file_content = VALID_ISO_CONTENT
    files = {"file": ("dup.iso", file_content, "application/octet-stream")}
    r1 = client.post("/api/v1/isos", files=files)
    assert r1.status_code == 201

    files2 = {"file": ("dup2.iso", file_content, "application/octet-stream")}
    r2 = client.post("/api/v1/isos", files=files2)
    assert r2.status_code == 201
    assert r2.json()["id"] == r1.json()["id"]


def test_list_isos(client: TestClient):
    file_content = VALID_ISO_CONTENT
    files = {"file": ("list.iso", file_content, "application/octet-stream")}
    client.post("/api/v1/isos", files=files)

    response = client.get("/api/v1/isos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_get_iso(client: TestClient):
    file_content = VALID_ISO_CONTENT
    files = {"file": ("get.iso", file_content, "application/octet-stream")}
    create_resp = client.post("/api/v1/isos", files=files)
    iso_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/isos/{iso_id}")
    assert response.status_code == 200
    assert response.json()["id"] == iso_id


def test_delete_iso(client: TestClient):
    file_content = VALID_ISO_CONTENT
    files = {"file": ("delete.iso", file_content, "application/octet-stream")}
    create_resp = client.post("/api/v1/isos", files=files)
    iso_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/isos/{iso_id}")
    assert response.status_code == 204

    get_resp = client.get(f"/api/v1/isos/{iso_id}")
    assert get_resp.status_code == 404


def test_upload_invalid_iso(client: TestClient):
    """Test that invalid ISO files are rejected."""
    file_content = b"not a valid iso file"
    files = {"file": ("invalid.iso", file_content, "application/octet-stream")}
    response = client.post("/api/v1/isos", files=files)
    assert response.status_code == 400
    assert "Invalid ISO file" in response.json()["detail"]
