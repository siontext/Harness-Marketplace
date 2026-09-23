const AGENT_REMINDER_COMMAND =
  "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PreToolUse\", \"additionalContext\": \"[AGENT HARNESS REMINDER] 에이전트를 호출하기 전에 반드시 해당 에이전트의 하네스 파일을 읽으세요. 파일 위치: ~/.claude/plugins/marketplaces/team-harness/agents/<agent-id>.md (예: designer.md, backend-dev.md). 하네스를 읽어야 통신 프로토콜(브리지 형식, AskUserQuestion 중계 등)을 정확히 파악할 수 있습니다.\"}}'";

/**
 * Claude 플러그인 hooks.json을 만든다.
 *
 * deny 패턴이 하나라도 있으면 Bash PreToolUse 훅을 함께 등록한다.
 * Gemini/Codex는 settings.json의 deny_rules로 차단되지만 Claude에는
 * 대응 설정이 없어, 같은 원천에서 훅을 생성해 차단력을 맞춘다.
 */
export function generateHooksJson(denyPatterns = []) {
  const preToolUse = [
    {
      matcher: 'Agent',
      hooks: [
        {
          type: 'command',
          command: AGENT_REMINDER_COMMAND,
          statusMessage: '에이전트 하네스 확인 중...',
        },
      ],
    },
  ];

  if (denyPatterns.length > 0) {
    preToolUse.push({
      matcher: 'Bash',
      hooks: [
        {
          type: 'command',
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/deny-guard.py"',
          statusMessage: '위험 명령 검사 중...',
        },
      ],
    });
  }

  return JSON.stringify({ hooks: { PreToolUse: preToolUse } }, null, 2);
}

/** deny-guard.py가 읽는 규칙 파일. deny-rules.md 표를 그대로 옮긴다. */
export function generateDenyRulesJson(denyPatterns = []) {
  const rules = denyPatterns.map(({ pattern, description, alternative, exceptions }) => ({
    pattern,
    description,
    alternative: alternative || null,
    exceptions: exceptions || [],
  }));
  return JSON.stringify({ rules }, null, 2);
}
