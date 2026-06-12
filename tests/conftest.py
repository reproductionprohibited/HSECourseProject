import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.db.engine import get_engine, sync_session
from app.db.models import Role, UserRoleLink
from app.main import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    SQLModel.metadata.drop_all(get_engine())
    SQLModel.metadata.create_all(get_engine())
    yield
    SQLModel.metadata.drop_all(get_engine())


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db():
    yield
    with sync_session() as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def regular_user(client: TestClient) -> dict:
    """Обычный юзер — возвращает dict с token и user_id."""
    response = client.post(
        "/auth/signup", json={"username": "regular", "password": "password123"}
    )
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return {"token": token, "user_id": me.json()["id"]}


@pytest.fixture
def route_creator(client: TestClient) -> dict:
    """Юзер с ролью route_creator."""
    response = client.post(
        "/auth/signup", json={"username": "creator", "password": "password123"}
    )
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = uuid.UUID(me.json()["id"])

    with sync_session() as session:
        role = Role(name="route_creator")
        session.add(role)
        session.flush()
        link = UserRoleLink(user_id=user_id, role_id=role.id)
        session.add(link)
        session.commit()

    return {"token": token, "user_id": str(user_id)}


@pytest.fixture
def admin_user(client: TestClient) -> dict:
    response = client.post(
        "/auth/signup", json={"username": "admin", "password": "password123"}
    )
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = uuid.UUID(me.json()["id"])

    with sync_session() as session:
        role = Role(name="admin")
        session.add(role)
        session.flush()
        link = UserRoleLink(user_id=user_id, role_id=role.id)
        session.add(link)
        session.commit()

    return {"token": token, "user_id": str(user_id)}
