"""서버 시작(lifespan) 테스트. .env 대신 가짜 설정을 넣고 서버를 켰다 끈다."""

import pytest
from fastapi.testclient import TestClient

from main import app
from tests.fakes import fake_settings


def test_서버가_켜지고_꺼질_때_env를_읽지_않고_연결_창구를_만들고_닫는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: .env 대신 가짜 설정. 로컬 창구를 만들지만 LLM은 부르지 않는다.
    # main.py가 부르는 Settings()를 가짜 설정을 만드는 함수로 바꾼다.
    monkeypatch.setattr("main.Settings", fake_settings)

    # When: with로 열어야 lifespan이 돈다. 엔드포인트 테스트에서는 with를 쓰지 않는다.
    with TestClient(app) as client:
        response = client.get("/health")

    # Then
    assert response.status_code == 200
