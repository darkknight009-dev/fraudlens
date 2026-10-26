from fastapi.testclient import TestClient

from app.main import app


def test_application_starts() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["service"] == "fraudlens-api"
