from pytest_mock import MockerFixture
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_db_fail(mocker: MockerFixture):
    class FakeSession:
        def exec(self, *args, **kwargs):
            raise Exception("DB down")

    class FakeCM:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, *args):
            pass

    mocker.patch("app.observability.healthchecks.sync_session", lambda: FakeCM())

    response = client.get("/ready")
    assert response.status_code == 503
