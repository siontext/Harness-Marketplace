from pathlib import Path

import pytest

from app.platform import Platform, PlatformLoadError, build_platform
from app.platform.local import (
    FilePromptStore,
    OpenAiCompatibleLlm,
    PassThroughGuardrail,
    PromptNotFoundError,
)
from app.platform.settings import Settings, load_settings


def _settings(**overrides: str) -> Settings:
    values = {
        "platform": "",
        "llm_base_url": "http://localhost:9999/v1",
        "llm_api_key": "test-key",
        "llm_model": "test-model",
    }
    return Settings(**{**values, **overrides})


def test_env_파일_값을_읽고_환경_변수가_우선한다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    env_file = tmp_path / ".env"
    env_file.write_text("# 주석\nLLM_MODEL=from-file\nLLM_API_KEY='fkey'\n")
    monkeypatch.setenv("LLM_MODEL", "from-env")

    # When
    settings = load_settings(env_file)

    # Then
    assert settings.llm_model == "from-env"
    assert settings.llm_api_key == "fkey"


def test_env_파일이_없으면_환경_변수만_쓴다(tmp_path: Path) -> None:
    # When
    settings = load_settings(tmp_path / "없는파일")

    # Then
    assert isinstance(settings, Settings)


def test_PLATFORM이_비어_있으면_로컬_창구를_만든다() -> None:
    # When
    platform = build_platform(_settings(platform=""))

    # Then
    assert isinstance(platform, Platform)
    assert isinstance(platform.guardrail, PassThroughGuardrail)


def test_없는_PLATFORM이면_로컬로_바꾸지_않고_오류를_낸다() -> None:
    # When / Then
    with pytest.raises(PlatformLoadError):
        build_platform(_settings(platform="nowhere"))


def test_프롬프트_파일을_이름으로_읽는다(tmp_path: Path) -> None:
    # Given
    (tmp_path / "system.md").write_text("역할 지시", encoding="utf-8")

    # When
    text = FilePromptStore(tmp_path).get("system")

    # Then
    assert text == "역할 지시"


def test_없는_프롬프트를_찾으면_오류를_낸다(tmp_path: Path) -> None:
    # When / Then
    with pytest.raises(PromptNotFoundError):
        FilePromptStore(tmp_path).get("없음")


def test_LLM_창구는_설정의_모델_이름으로_채팅_모델을_만든다() -> None:
    # When
    model = OpenAiCompatibleLlm(_settings()).chat_model()

    # Then
    assert getattr(model, "model_name", None) == "test-model"


@pytest.mark.anyio
async def test_로컬_가드레일은_입력과_출력을_그대로_통과시킨다() -> None:
    # Given
    guardrail = PassThroughGuardrail()

    # When
    checked_in = await guardrail.check_input("질문")
    checked_out = await guardrail.check_output("답")

    # Then
    assert (checked_in.text, checked_in.blocked) == ("질문", False)
    assert (checked_out.text, checked_out.blocked) == ("답", False)


@pytest.mark.anyio
async def test_창구를_닫으면_등록한_닫기_함수를_모두_부른다() -> None:
    # Given
    closed: list[str] = []

    async def close() -> None:
        closed.append("done")

    base = build_platform(_settings())
    platform = Platform(base.llm, base.prompts, base.guardrail, closers=(close,))

    # When
    await platform.aclose()

    # Then
    assert closed == ["done"]
