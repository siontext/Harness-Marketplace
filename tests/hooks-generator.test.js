import { describe, it, expect } from 'vitest';
import { generateHooksJson, generateDenyRulesJson } from '../build/hooks-generator.js';

const denyPatterns = [
  { pattern: 'rm -rf*', description: '재귀 삭제 금지', alternative: '개별 파일 삭제', exceptions: [] },
  { pattern: 'git push --force*', description: '강제 푸시 금지', alternative: 'force-with-lease 사용', exceptions: ['git push --force-with-lease*'] },
];

describe('generateHooksJson', () => {
  it('Agent 리마인더 훅을 항상 포함한다', () => {
    const parsed = JSON.parse(generateHooksJson(denyPatterns));
    const agentHook = parsed.hooks.PreToolUse.find(h => h.matcher === 'Agent');
    expect(agentHook).toBeDefined();
    expect(agentHook.hooks[0].command).toContain('AGENT HARNESS REMINDER');
  });

  it('deny 패턴이 있으면 Bash 차단 훅을 등록한다', () => {
    const parsed = JSON.parse(generateHooksJson(denyPatterns));
    const bashHook = parsed.hooks.PreToolUse.find(h => h.matcher === 'Bash');
    expect(bashHook).toBeDefined();
    expect(bashHook.hooks[0].command).toBe('python3 "${CLAUDE_PLUGIN_ROOT}/hooks/deny-guard.py"');
  });

  it('deny 패턴이 없으면 Bash 훅을 등록하지 않는다', () => {
    const parsed = JSON.parse(generateHooksJson([]));
    expect(parsed.hooks.PreToolUse.find(h => h.matcher === 'Bash')).toBeUndefined();
    expect(parsed.hooks.PreToolUse).toHaveLength(1);
  });
});

describe('generateDenyRulesJson', () => {
  it('패턴, 설명, 대체 방법을 그대로 옮긴다', () => {
    const parsed = JSON.parse(generateDenyRulesJson(denyPatterns));
    expect(parsed.rules).toHaveLength(2);
    expect(parsed.rules[0]).toEqual({
      pattern: 'rm -rf*',
      description: '재귀 삭제 금지',
      alternative: '개별 파일 삭제',
      exceptions: [],
    });
    expect(parsed.rules[1].exceptions).toEqual(['git push --force-with-lease*']);
  });

  it('빈 패턴이면 빈 배열을 만든다', () => {
    expect(JSON.parse(generateDenyRulesJson([])).rules).toEqual([]);
  });
});
