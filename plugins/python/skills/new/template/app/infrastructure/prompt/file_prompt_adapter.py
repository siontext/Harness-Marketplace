"""로컬 개발용 프롬프트 창구 구현. app/prompts의 파일을 읽는다."""

from pathlib import Path

from typing_extensions import override

from app.infrastructure.prompt.port import PromptStore

# 이 파일(app/infrastructure/prompt/)에서 두 단계 위가 app이다.
PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"


class PromptNotFoundError(LookupError):
    """요청한 이름의 프롬프트 파일이 없을 때.

    Attributes:
        file_name: 찾지 못한 파일 이름.
    """

    def __init__(self, file_name: str) -> None:
        super().__init__(f"프롬프트 파일이 없다: {file_name}")
        self.file_name = file_name


class FilePromptAdapter(PromptStore):
    """app/prompts/<이름>.md 파일에서 프롬프트를 읽는다."""

    def __init__(self, prompt_dir: Path = PROMPT_DIR) -> None:
        self._prompt_dir = prompt_dir

    @override
    def get(self, name: str) -> str:
        path = self._prompt_dir / f"{name}.md"
        if not path.is_file():
            raise PromptNotFoundError(path.name)
        return path.read_text(encoding="utf-8")
