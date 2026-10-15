import pytest
from fastapi.testclient import TestClient


VALID_RECIPE = {
    "components": ["Notepad"],
    "removals": [],
    "registry_tweaks": [],
    "unattend_snippets": [],
}


@pytest.fixture
def iso_and_recipe(client: TestClient):
    file_content = b"iso for build"
    files = {"file": ("build.iso", file_content, "application/octet-stream")}
    iso_resp = client.post("/api/v1/isos", files=files)
    iso_id = iso_resp.json()["id"]

    recipe_json = str(VALID_RECIPE).replace("'", '"')
    recipe_resp = client.post("/api/v1/recipes", json={"name": "Build Recipe", "recipe_json": recipe_json})
    recipe_id = recipe_resp.json()["id"]

    return iso_id, recipe_id


def test_create_build(client: TestClient, iso_and_recipe):
    iso_id, recipe_id = iso_and_recipe
    response = client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})
    assert response.status_code == 201
    data = response.json()
    assert data["iso_id"] == iso_id
    assert data["recipe_id"] == recipe_id
    assert data["stage"] == "pending"
    assert data["progress"] == 0


def test_create_build_invalid_iso(client: TestClient, iso_and_recipe):
    _, recipe_id = iso_and_recipe
    response = client.post("/api/v1/builds", json={"iso_id": "invalid-id", "recipe_id": recipe_id})
    assert response.status_code == 404


def test_create_build_invalid_recipe(client: TestClient, iso_and_recipe):
    iso_id, _ = iso_and_recipe
    response = client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": "invalid-id"})
    assert response.status_code == 404


def test_list_builds(client: TestClient, iso_and_recipe):
    iso_id, recipe_id = iso_and_recipe
    client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})
    client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})

    response = client.get("/api/v1/builds")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2


def test_get_build(client: TestClient, iso_and_recipe):
    iso_id, recipe_id = iso_and_recipe
    create_resp = client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})
    build_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/builds/{build_id}")
    assert response.status_code == 200
    assert response.json()["id"] == build_id


def test_get_build_logs(client: TestClient, iso_and_recipe):
    iso_id, recipe_id = iso_and_recipe
    create_resp = client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})
    build_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/builds/{build_id}/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["logs"] == []


def test_delete_build(client: TestClient, iso_and_recipe):
    iso_id, recipe_id = iso_and_recipe
    create_resp = client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})
    build_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/builds/{build_id}")
    assert response.status_code == 204

    get_resp = client.get(f"/api/v1/builds/{build_id}")
    assert get_resp.status_code == 404


def test_filter_builds_by_stage(client: TestClient, iso_and_recipe):
    iso_id, recipe_id = iso_and_recipe
    client.post("/api/v1/builds", json={"iso_id": iso_id, "recipe_id": recipe_id})

    response = client.get("/api/v1/builds?stage=pending")
    assert response.status_code == 200
    data = response.json()
    assert all(b["stage"] == "pending" for b in data["items"])