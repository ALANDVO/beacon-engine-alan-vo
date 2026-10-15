import pytest
import json
from fastapi.testclient import TestClient


VALID_RECIPE = {
    "components": ["Notepad", "Calculator"],
    "removals": ["Cortana", "OneDrive"],
    "registry_tweaks": [
        {"path": "HKCU\\Software\\Test", "name": "Value", "type": "DWORD", "data": 1}
    ],
    "unattend_snippets": ['<Settings pass="specialize">...</Settings>'],
}


def test_create_recipe(client: TestClient):
    response = client.post(
        "/api/v1/recipes",
        json={"name": "Test Recipe", "description": "A test recipe", "recipe_json": json.dumps(VALID_RECIPE)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Recipe"
    assert data["version"] == 1


def test_create_duplicate_recipe_name(client: TestClient):
    recipe_json = json.dumps(VALID_RECIPE)
    client.post("/api/v1/recipes", json={"name": "Duplicate", "recipe_json": recipe_json})
    response = client.post("/api/v1/recipes", json={"name": "Duplicate", "recipe_json": recipe_json})
    assert response.status_code == 409


def test_list_recipes(client: TestClient):
    recipe_json = json.dumps(VALID_RECIPE)
    client.post("/api/v1/recipes", json={"name": "Recipe 1", "recipe_json": recipe_json})
    client.post("/api/v1/recipes", json={"name": "Recipe 2", "recipe_json": recipe_json})

    response = client.get("/api/v1/recipes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2


def test_get_recipe(client: TestClient):
    recipe_json = json.dumps(VALID_RECIPE)
    create_resp = client.post("/api/v1/recipes", json={"name": "Get Recipe", "recipe_json": recipe_json})
    recipe_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id


def test_update_recipe(client: TestClient):
    recipe_json = json.dumps(VALID_RECIPE)
    create_resp = client.post("/api/v1/recipes", json={"name": "Update Recipe", "recipe_json": recipe_json})
    recipe_id = create_resp.json()["id"]

    new_json = {**VALID_RECIPE, "components": ["Paint"]}
    response = client.patch(
        f"/api/v1/recipes/{recipe_id}",
        json={"name": "Updated Recipe", "recipe_json": json.dumps(new_json)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Recipe"
    assert data["version"] == 2


def test_delete_recipe(client: TestClient):
    recipe_json = json.dumps(VALID_RECIPE)
    create_resp = client.post("/api/v1/recipes", json={"name": "Delete Recipe", "recipe_json": recipe_json})
    recipe_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/recipes/{recipe_id}")
    assert response.status_code == 204

    get_resp = client.get(f"/api/v1/recipes/{recipe_id}")
    assert get_resp.status_code == 404


def test_clone_recipe(client: TestClient):
    recipe_json = json.dumps(VALID_RECIPE)
    create_resp = client.post("/api/v1/recipes", json={"name": "Clone Source", "recipe_json": recipe_json})
    recipe_id = create_resp.json()["id"]

    response = client.post(f"/api/v1/recipes/{recipe_id}/clone")
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Clone Source (copy)"
    assert data["recipe_json"] == create_resp.json()["recipe_json"]