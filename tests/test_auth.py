from fastapi.testclient import TestClient


def test_signup_success(client: TestClient):
    response = client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_signup_duplicate_username(client: TestClient):
    client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    response = client.post(
        "/auth/signup", json={"username": "testuser", "password": "password456"}
    )
    assert response.status_code == 409


def test_login_success(client: TestClient):
    client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client: TestClient):
    client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_unknown_user(client: TestClient):
    response = client.post(
        "/auth/login", json={"username": "nobody", "password": "password123"}
    )
    assert response.status_code == 401


def test_logout_success(client: TestClient):
    signup = client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    token = signup.json()["access_token"]
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_logout_invalidates_token(client: TestClient):
    signup = client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    token = signup.json()["access_token"]
    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_me_success(client: TestClient):
    signup = client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    token = signup.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_update_me_username(client: TestClient):
    signup = client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    token = signup.json()["access_token"]
    response = client.patch(
        "/auth/me",
        json={"username": "newusername"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "newusername"


def test_update_me_password(client: TestClient):
    client.post(
        "/auth/signup", json={"username": "testuser", "password": "password123"}
    )
    login = client.post(
        "/auth/login", json={"username": "testuser", "password": "password123"}
    )
    token = login.json()["access_token"]
    client.patch(
        "/auth/me",
        json={"password": "newpassword"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "newpassword"}
    )
    assert response.status_code == 200


def test_update_me_duplicate_username(client: TestClient):
    client.post("/auth/signup", json={"username": "user1", "password": "password123"})
    signup2 = client.post(
        "/auth/signup", json={"username": "user2", "password": "password123"}
    )
    token = signup2.json()["access_token"]
    response = client.patch(
        "/auth/me",
        json={"username": "user1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
