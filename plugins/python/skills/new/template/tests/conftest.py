import pytest


@pytest.fixture
def anyio_backend() -> str:
    # 설치되지 않은 trio로 돌리지 않도록 asyncio 하나로 고정한다.
    return "asyncio"
