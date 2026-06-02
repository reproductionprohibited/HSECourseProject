import uuid
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def route(client: TestClient, regular_user: dict) -> dict:
    token = regular_user["token"]
    response = client.post(
        "/routes",
        json={"title": "Test route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()


@pytest.fixture
def impression(client: TestClient, regular_user: dict, route: dict) -> dict:
    token = regular_user["token"]
    response = client.post(
        "/impressions",
        json={"route_id": route["id"], "title": "Great!", "content": "Loved it"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()


def test_create_impression(client: TestClient, regular_user: dict, route: dict):
    token = regular_user["token"]
    response = client.post(
        "/impressions",
        json={"route_id": route["id"], "title": "Great!", "content": "Loved it"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Great!"
    assert data["content"] == "Loved it"
    assert data["route_id"] == route["id"]
    assert data["likes_count"] == 0
    assert data["dislikes_count"] == 0


def test_create_impression_unauthorized(client: TestClient, route: dict):
    response = client.post(
        "/impressions",
        json={"route_id": route["id"], "title": "Great!", "content": "Loved it"},
    )
    assert response.status_code == 401


def test_create_impression_route_not_found(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    response = client.post(
        "/impressions",
        json={"route_id": str(uuid.uuid4()), "title": "Great!", "content": "Loved it"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_get_impression(client: TestClient, impression: dict):
    response = client.get(f"/impressions/{impression['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == impression["id"]


def test_get_impression_not_found(client: TestClient):
    response = client.get(f"/impressions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_impression(client: TestClient, regular_user: dict, impression: dict):
    token = regular_user["token"]
    response = client.put(
        f"/impressions/{impression['id']}",
        json={"title": "Updated title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    assert response.json()["content"] == impression["content"]


def test_update_impression_forbidden_for_other(
    client: TestClient, route_creator: dict, impression: dict
):
    token = route_creator["token"]
    response = client.put(
        f"/impressions/{impression['id']}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_update_impression_not_found(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    response = client.put(
        f"/impressions/{uuid.uuid4()}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_delete_impression(client: TestClient, regular_user: dict, impression: dict):
    token = regular_user["token"]
    response = client.delete(
        f"/impressions/{impression['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204
    get_response = client.get(f"/impressions/{impression['id']}")
    assert get_response.status_code == 404


def test_delete_impression_forbidden_for_other(
    client: TestClient, route_creator: dict, impression: dict
):
    token = route_creator["token"]
    response = client.delete(
        f"/impressions/{impression['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_get_route_impressions(
    client: TestClient, regular_user: dict, route: dict, impression: dict
):
    response = client.get(f"/routes/{route['id']}/impressions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == impression["id"]


def test_get_route_impressions_empty(
    client: TestClient, regular_user: dict, route: dict
):
    response = client.get(f"/routes/{route['id']}/impressions")
    assert response.status_code == 200
    assert response.json() == []


def test_get_route_impressions_pagination(
    client: TestClient, regular_user: dict, route: dict
):
    token = regular_user["token"]
    for i in range(5):
        client.post(
            "/impressions",
            json={
                "route_id": route["id"],
                "title": f"Impression {i}",
                "content": "content",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get(f"/routes/{route['id']}/impressions?offset=0&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_route_impressions_route_not_found(client: TestClient):
    response = client.get(f"/routes/{uuid.uuid4()}/impressions")
    assert response.status_code == 404
