#!/usr/bin/env python3
"""PreToolUse 훅 — 반출 전용 프로젝트에서 소스를 원격 저장소로 내보내는 git 명령을 막는다.

반출 전용 프로젝트: git 루트(없으면 작업 폴더)에 run-application.sh가 있는 프로젝트.
이런 프로젝트의 소스는 압축 파일(/python:export)로만 옮긴다.

stdin  : Claude Code PreToolUse 훅 입력 JSON
stdout : 차단 시 permissionDecision=deny JSON, 통과 시 아무것도 출력하지 않음
"""
import json
import re
import shlex
import sys
from pathlib import Path

MARKER = "run-application.sh"

# 명령 경계 뒤의 git 호출. `cd x && git push`, `git -C x push`도 잡는다.
BOUNDARY = r'(?:^|[;&|(\n`"\'])\s*'
GIT = BOUNDARY + r'git(?:\s+-C\s+(?P<path>\S+))?(?:\s+-[^\s]+(?:\s+[^\s-][^\s]*)?)*\s+'
BLOCKED = [
    (re.compile(GIT + r'push\b'), 'git push'),
    (re.compile(GIT + r'remote\s+(?:add|set-url)\b'), 'git remote add / set-url'),
]
CD = re.compile(BOUNDARY + r'cd\s+(?P<path>[^\s;&|]+)')


def find_root(start):
    """start에서 위로 올라가며 git 루트를 찾는다. 없으면 start."""
    for path in [start, *start.parents]:
        if (path / '.git').exists():
            return path
    return start


def is_export_project(path):
    return (find_root(path) / MARKER).is_file() or (path / MARKER).is_file()


def resolve(base, raw):
    try:
        raw = shlex.split(raw)[0]
    except (ValueError, IndexError):
        pass
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (base / path)


def deny(label):
    reason = (
        f"[하네스 보안 규칙] {label} — 반출 전용 프로젝트({MARKER}가 있는 곳)의 소스는 "
        "원격 저장소에 올리지 않는다.\n대체 방법: /python:export로 압축 파일을 만들어 옮긴다."
    )
    json.dump({
        'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny',
            'permissionDecisionReason': reason,
        }
    }, sys.stdout, ensure_ascii=False)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = (payload.get('tool_input') or {}).get('command')
    if not isinstance(command, str) or not command.strip():
        return 0

    cwd = Path(payload.get('cwd') or '.').resolve()
    candidates = [cwd] + [resolve(cwd, m.group('path')) for m in CD.finditer(command)]

    for pattern, label in BLOCKED:
        for match in pattern.finditer(command):
            paths = list(candidates)
            if match.group('path'):
                paths.append(resolve(cwd, match.group('path')))
            if any(is_export_project(p.resolve()) for p in paths):
                deny(label)
                return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
