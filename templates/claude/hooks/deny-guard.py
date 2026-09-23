#!/usr/bin/env python3
"""PreToolUse 훅 — Bash 명령을 deny-rules.json과 대조해 위험 명령을 차단한다.

skills/security/deny-rules.md 표가 단일 원천이며, 빌드가 같은 디렉토리에
deny-rules.json을 생성한다. 이 스크립트는 그 JSON만 읽으므로 규칙을 바꿀 때
스크립트를 손댈 필요가 없다.

stdin  : Claude Code PreToolUse 훅 입력 JSON
stdout : 차단 시 permissionDecision=deny JSON, 통과 시 아무것도 출력하지 않음
"""
import json
import os
import re
import sys

# 명령 경계 — 문자열 맨 앞, 또는 구분자/따옴표/등호 뒤.
# `cd /tmp && rm -rf x`처럼 복합 명령에 숨긴 경우와
# `psql -c "DROP TABLE users"`처럼 따옴표 안에 넣은 경우를 모두 잡는다.
#
# 따옴표를 경계로 인정하면 `echo "sudo ..."` 같은 단순 언급도 걸리지만,
# 오탐은 재시도 한 번으로 끝나는 반면 미탐은 되돌릴 수 없으므로
# 막는 쪽으로 기운다. 정당한 명령은 표의 `예외` 열로 풀어준다.
BOUNDARY = r'(?:^|[;&|(\n`"\'=])\s*'


def glob_to_regex(pattern):
    """deny-rules.md 표의 글롭 패턴(`rm -rf*`)을 정규식으로 바꾼다."""
    return BOUNDARY + re.escape(pattern).replace(r'\*', r'.*')


def matches(pattern, command):
    return re.search(glob_to_regex(pattern), command, re.IGNORECASE) is not None


def load_rules():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deny-rules.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f).get('rules', [])


def deny(rule):
    reason = f"[하네스 보안 규칙] {rule['pattern']} — {rule.get('description', '차단된 명령')}"
    if rule.get('alternative'):
        reason += f"\n대체 방법: {rule['alternative']}"
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

    try:
        rules = load_rules()
    except (OSError, json.JSONDecodeError, ValueError) as err:
        # 규칙 파일이 깨졌으면 차단하지 못한다는 사실을 조용히 넘기지 않는다.
        print(f'[harness] deny-rules.json을 읽지 못했습니다: {err}', file=sys.stderr)
        return 0

    for rule in rules:
        pattern = rule.get('pattern')
        if not pattern or not matches(pattern, command):
            continue
        # 표가 대안으로 권하는 명령(예: git push --force-with-lease)은 통과시킨다.
        if any(matches(exc, command) for exc in rule.get('exceptions') or []):
            continue
        deny(rule)
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
