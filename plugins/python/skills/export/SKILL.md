---
name: export
description: 반출용 압축 파일을 만든다 — 테스트·커버리지 80%·Ruff·Pyrefly·키 섞임 검사를 모두 통과해야 압축하고, .git·.env·.venv·캐시·커버리지·평가 결과는 뺀다. 사용자가 /python:export를 직접 칠 때만 실행한다.
disable-model-invocation: true
argument-hint: "[프로젝트 경로]"
---

# 반출용 압축 만들기

검사와 압축은 스크립트가 정해진 순서대로 한다. Claude가 검사를 건너뛰거나 결과를 판단해 바꾸지 않는다.

**압축 파일 만들기는 사용자가 이 명령을 부를 때만 한다.** 예외: python-reviewer가 `--check-only`(압축 없이 키 검사와 반출 목록만)로 스크립트를 실행하는 것은 허용한다.

인자: `$ARGUMENTS` — 프로젝트 경로. 없으면 현재 폴더.

## 절차

### 1. 실행

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/export.py" <프로젝트 경로>
```

`${CLAUDE_PLUGIN_ROOT}`가 비어 있으면 `~/.claude/plugins/marketplaces/team-harness/plugins/python/scripts/export.py`를 쓴다.

스크립트가 하는 일:

| 순서 | 검사 | 실패하면 |
|---|---|---|
| 1 | 필수 파일 (`main.py`, `pyproject.toml`, `app/`) | 멈춤 |
| 2 | Ruff 검사 → Ruff 포맷 → Pyrefly | 멈춤 |
| 3 | pytest + 커버리지 80% | 멈춤 |
| 4 | 키 섞임 (흔한 키 모양, `.env`의 실제 키·주소 값) | 멈춤 |
| 5 | 압축 — `<프로젝트 상위 폴더>/<이름>_<날짜>_<시간>.zip` | — |

제외 목록은 `python-project` 스킬의 "반출 제외 목록"과 같다. `tests/`는 포함한다.

### 2. 결과 알리기

- **통과:** 압축 파일 경로, 파일 수, 크기를 알린다.
- **실패:** 어느 검사에서 멈췄는지와 출력의 핵심 줄을 그대로 보여준다. 고칠지 사용자에게 묻는다. 묻지 않고 코드를 고치지 않는다.
- **키 섞임:** 파일과 줄 번호를 보여준다. 키를 `.env`로 옮기는 방법을 안내한다. 오탐이라고 판단해도 사용자 확인 없이 넘어가지 않는다.

## 하지 않는 것

- 압축 파일을 어디로 보내거나 올리지 않는다. 옮기는 것은 사용자가 한다.
- 검사를 끄는 옵션을 만들거나 쓰지 않는다.
