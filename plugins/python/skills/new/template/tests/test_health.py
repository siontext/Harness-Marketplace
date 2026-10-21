from fastapi.testclient import TestClient

from main import app


def test_health는_ok를_돌려준다() -> None:
    # Given
    client = TestClient(app)

    # When
    response = client.get("/health")

    # Then
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
