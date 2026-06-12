import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def other_user(client: TestClient) -> dict:
    response = client.post(
        "/auth/signup", json={"username": "other", "password": "password123"}
    )
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"token": token, "user_id": me.json()["id"]}


def test_get_user_routes_own(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    client.post(
        "/routes",
        json={"title": "Private", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get(
        f"/user/{regular_user['user_id']}/routes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_user_routes_other_sees_only_public(
    client: TestClient, regular_user: dict, other_user: dict, route_creator: dict
):
    creator_token = route_creator["token"]
    # route_creator создаёт публичный и приватный маршруты
    client.post(
        "/routes",
        json={"title": "Public", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    client.post(
        "/routes",
        json={"title": "Private", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    response = client.get(
        f"/user/{route_creator['user_id']}/routes",
        headers={"Authorization": f"Bearer {other_user['token']}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Public"


def test_get_user_routes_admin_sees_private(
    client: TestClient, regular_user: dict, admin_user: dict
):
    token = regular_user["token"]
    client.post(
        "/routes",
        json={"title": "Private", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get(
        f"/user/{regular_user['user_id']}/routes",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_user_routes_pagination(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    for i in range(5):
        client.post(
            "/routes",
            json={"title": f"Route {i}", "description": "", "is_private": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get(
        f"/user/{regular_user['user_id']}/routes?offset=0&limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_user_impressions(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    route = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    client.post(
        "/impressions",
        json={"route_id": route["id"], "title": "Wow", "content": "Amazing"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get(f"/user/{regular_user['user_id']}/impressions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Wow"


def test_get_user_impressions_empty(client: TestClient, regular_user: dict):
    response = client.get(f"/user/{regular_user['user_id']}/impressions")
    assert response.status_code == 200
    assert response.json() == []


def test_get_user_impressions_pagination(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    route = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
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
    response = client.get(
        f"/user/{regular_user['user_id']}/impressions?offset=0&limit=2"
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_user_impressions_invalid_uuid(client: TestClient):
    response = client.get("/user/not-a-uuid/impressions")
    assert response.status_code == 422
