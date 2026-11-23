from dataclasses import replace
from pathlib import Path

import pytest

from app.infrastructure import Platform, PlatformLoadError
from app.infrastructure.guardrail.pass_through import PassThroughGuardrail
from app.infrastructure.llm.openai_compatible import OpenAiCompatibleLlm
from app.infrastructure.prompt.file_prompt_store import (
    FilePromptStore,
    PromptNotFoundError,
)
from app.infrastructure.settings import DEFAULT_AGENT_TIMEOUT_SECONDS, Settings
from tests.fakes import fake_settings


def test_env_파일_값을_읽고_환경_변수가_우선한다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    env_file = tmp_path / ".env"
    env_file.write_text("# 주석\nLLM_MODEL=from-file\nLLM_API_KEY='fkey'\n")
    monkeypatch.setenv("LLM_MODEL", "from-env")

    # When
    settings = Settings.from_env(env_file)

    # Then
    assert settings.llm_model == "from-env"
    assert settings.llm_api_key == "fkey"


def test_env_파일이_없으면_환경_변수만_쓴다(tmp_path: Path) -> None:
    # When
    settings = Settings.from_env(tmp_path / "없는파일")

    # Then
    assert isinstance(settings, Settings)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("", DEFAULT_AGENT_TIMEOUT_SECONDS), ("12.5", 12.5)],
    ids=["비우면_기본값", "적은_값"],
)
def test_시간_제한을_읽는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str, expected: float
) -> None:
    # Given
    monkeypatch.setenv("AGENT_TIMEOUT_SECONDS", raw)

    # When
    settings = Settings.from_env(tmp_path / "없는파일")

    # Then
    assert settings.agent_timeout_seconds == expected


@pytest.mark.parametrize("raw", ["abc", "0", "-1"])
def test_시간_제한이_숫자가_아니거나_0_이하면_서버가_뜨지_않게_오류를_낸다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    # Given
    monkeypatch.setenv("AGENT_TIMEOUT_SECONDS", raw)

    # When / Then
    with pytest.raises(ValueError):
        Settings.from_env(tmp_path / "없는파일")


def test_PLATFORM이_비어_있으면_로컬_창구를_만든다() -> None:
    # When
    platform = Platform.from_settings(fake_settings(platform=""))

    # Then
    assert isinstance(platform, Platform)
    assert isinstance(platform.guardrail, PassThroughGuardrail)


def test_없는_PLATFORM이면_로컬로_바꾸지_않고_오류를_낸다() -> None:
    # When / Then
    with pytest.raises(PlatformLoadError):
        Platform.from_settings(fake_settings(platform="nowhere"))


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
    model = OpenAiCompatibleLlm(fake_settings()).chat_model()

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

    # 칸 이름으로 바꿔 만든다. Platform에 업무 저장소 칸이 늘어도 깨지지 않는다.
    platform = replace(Platform.from_settings(fake_settings()), closers=(close,))

    # When
    await platform.aclose()

    # Then
    assert closed == ["done"]
