import uuid

from fastapi.testclient import TestClient


def test_get_routes_empty(client: TestClient):
    response = client.get("/routes")
    assert response.status_code == 200
    assert response.json() == []


def test_get_routes_returns_only_public(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    client.post(
        "/routes",
        json={"title": "Public", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/routes",
        json={"title": "Private", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/routes")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Public"


def test_get_routes_filter_by_title(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    client.post(
        "/routes",
        json={"title": "Mountain trail", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/routes",
        json={"title": "City walk", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/routes?title=mountain")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Mountain trail"


def test_get_routes_filter_by_created_by(
    client: TestClient, route_creator: dict, regular_user: dict
):
    creator_token = route_creator["token"]
    regular_token = regular_user["token"]
    client.post(
        "/routes",
        json={"title": "Route 1", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    client.post(
        "/routes",
        json={"title": "Route 2", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    response = client.get(f"/routes?created_by={route_creator['user_id']}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Route 1"


def test_get_routes_pagination(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    for i in range(5):
        client.post(
            "/routes",
            json={"title": f"Route {i}", "description": "", "is_private": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get("/routes?offset=0&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_route_private(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    response = client.post(
        "/routes",
        json={"title": "My route", "description": "desc", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "My route"
    assert response.json()["is_private"] is True
    assert response.json()["points"] == []


def test_create_route_public_as_creator(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    response = client.post(
        "/routes",
        json={"title": "Public route", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["is_private"] is False


def test_create_route_public_forbidden_for_regular(
    client: TestClient, regular_user: dict
):
    token = regular_user["token"]
    response = client.post(
        "/routes",
        json={"title": "Public route", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_create_route_unauthorized(client: TestClient):
    response = client.post(
        "/routes", json={"title": "Route", "description": "", "is_private": True}
    )
    assert response.status_code == 401


def test_get_route_by_id(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "My route", "description": "desc", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.get(
        f"/routes/{created['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_private_route_forbidden_for_other(
    client: TestClient, regular_user: dict, route_creator: dict
):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Private", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.get(
        f"/routes/{created['id']}",
        headers={"Authorization": f"Bearer {route_creator['token']}"},
    )
    assert response.status_code == 403


def test_get_public_route_without_auth(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    created = client.post(
        "/routes",
        json={"title": "Public", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.get(f"/routes/{created['id']}")
    assert response.status_code == 200


def test_get_route_not_found(client: TestClient):
    response = client.get(f"/routes/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_route(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Old title", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.put(
        f"/routes/{created['id']}",
        json={"title": "New title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_update_route_forbidden_for_other(
    client: TestClient, regular_user: dict, route_creator: dict
):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.put(
        f"/routes/{created['id']}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {route_creator['token']}"},
    )
    assert response.status_code == 403


def test_delete_route(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.delete(
        f"/routes/{created['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    get_response = client.get(
        f"/routes/{created['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


def test_delete_route_forbidden_for_other(
    client: TestClient, regular_user: dict, route_creator: dict
):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.delete(
        f"/routes/{created['id']}",
        headers={"Authorization": f"Bearer {route_creator['token']}"},
    )
    assert response.status_code == 403


def test_change_privacy(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.patch(
        f"/routes/{created['id']}/privacy",
        json={"is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_private"] is False


def test_change_privacy_forbidden_for_regular(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.patch(
        f"/routes/{created['id']}/privacy",
        json={"is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_add_point(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.post(
        f"/routes/{created['id']}/points",
        json={"latitude": 55.75, "longitude": 37.61},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["latitude"] == 55.75


def test_update_point(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    point = client.post(
        f"/routes/{created['id']}/points",
        json={"latitude": 55.75, "longitude": 37.61},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.put(
        f"/routes/{created['id']}/points/{point['id']}",
        json={"latitude": 56.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["latitude"] == 56.0


def test_delete_point(client: TestClient, regular_user: dict):
    token = regular_user["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": True},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    point = client.post(
        f"/routes/{created['id']}/points",
        json={"latitude": 55.75, "longitude": 37.61},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.delete(
        f"/routes/{created['id']}/points/{point['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_search_by_point(client: TestClient, route_creator: dict):
    token = route_creator["token"]
    created = client.post(
        "/routes",
        json={"title": "Route", "description": "", "is_private": False},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    client.post(
        f"/routes/{created['id']}/points",
        json={"latitude": 55.75, "longitude": 37.61},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/routes/search/by-point?lat=55.75&lng=37.61")
    assert response.status_code == 200
    assert len(response.json()) == 1
