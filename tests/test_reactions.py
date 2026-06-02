import uuid


def create_route(client, token):
    return client.post(
        "/routes",
        json={
            "title": "Route",
            "description": "",
            "is_private": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_create_like_for_route(client, regular_user):
    route = create_route(client, regular_user["token"])

    response = client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert response.status_code == 200
    assert response.json()["type"] == "like"


def test_create_reaction_unauthorized(client, regular_user):
    route = create_route(client, regular_user["token"])

    response = client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
    )

    assert response.status_code == 401


def test_same_reaction_twice_returns_existing(client, regular_user):
    route = create_route(client, regular_user["token"])

    payload = {
        "target_id": route["id"],
        "target_type": "route",
        "type": "like",
    }

    first = client.post(
        "/reactions",
        json=payload,
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    second = client.post(
        "/reactions",
        json=payload,
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["id"] == second.json()["id"]


def test_change_like_to_dislike(client, regular_user):
    route = create_route(client, regular_user["token"])

    client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    response = client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "dislike",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert response.status_code == 200
    assert response.json()["type"] == "dislike"


def test_delete_reaction(client, regular_user):
    route = create_route(client, regular_user["token"])

    reaction = client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    ).json()

    response = client.delete(
        f"/reactions/{reaction['id']}",
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert response.status_code == 204


def test_delete_reaction_forbidden(client, regular_user, route_creator):
    route = create_route(client, regular_user["token"])

    reaction = client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    ).json()

    response = client.delete(
        f"/reactions/{reaction['id']}",
        headers={"Authorization": f"Bearer {route_creator['token']}"},
    )

    assert response.status_code == 403


def test_delete_reaction_not_found(client, regular_user):
    response = client.delete(
        f"/reactions/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert response.status_code == 404


def test_get_route_reactions(client, regular_user, route_creator):
    route = create_route(client, regular_user["token"])

    client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "dislike",
        },
        headers={"Authorization": f"Bearer {route_creator['token']}"},
    )

    response = client.get(f"/routes/{route['id']}/reactions")

    assert response.status_code == 200
    assert response.json()["likes"] == 1
    assert response.json()["dislikes"] == 1
    assert len(response.json()["reactions"]) == 2


def test_get_route_reactions_empty(client, regular_user):
    route = create_route(client, regular_user["token"])

    response = client.get(f"/routes/{route['id']}/reactions")

    assert response.status_code == 200
    assert response.json()["likes"] == 0
    assert response.json()["dislikes"] == 0
    assert response.json()["reactions"] == []


def test_get_route_reactions_route_not_found(client):
    response = client.get(f"/routes/{uuid.uuid4()}/reactions")

    assert response.status_code == 404


def test_create_reaction_target_not_found(client, regular_user):
    response = client.post(
        "/reactions",
        json={
            "target_id": str(uuid.uuid4()),
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert response.status_code == 404


def test_create_reaction_for_missing_impression(
    client,
    regular_user,
):
    response = client.post(
        "/reactions",
        json={
            "target_id": str(uuid.uuid4()),
            "target_type": "impression",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert response.status_code == 404


def test_route_like_counter_updated(client, regular_user):
    route = create_route(client, regular_user["token"])

    client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    route_response = client.get(
        f"/routes/{route['id']}",
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert route_response.status_code == 200
    assert route_response.json()["likes_count"] == 1
    assert route_response.json()["dislikes_count"] == 0


def test_route_counters_after_reaction_change(client, regular_user):
    route = create_route(client, regular_user["token"])

    client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "dislike",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    route_response = client.get(
        f"/routes/{route['id']}",
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert route_response.json()["likes_count"] == 0
    assert route_response.json()["dislikes_count"] == 1


def test_delete_reaction_updates_route_counters(client, regular_user):
    route = create_route(client, regular_user["token"])

    reaction = client.post(
        "/reactions",
        json={
            "target_id": route["id"],
            "target_type": "route",
            "type": "like",
        },
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    ).json()

    client.delete(
        f"/reactions/{reaction['id']}",
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    route_response = client.get(
        f"/routes/{route['id']}",
        headers={"Authorization": f"Bearer {regular_user['token']}"},
    )

    assert route_response.json()["likes_count"] == 0
    assert route_response.json()["dislikes_count"] == 0
