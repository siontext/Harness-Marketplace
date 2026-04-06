import { describe, it, expect } from 'vitest';
import { parseRules, parseRoles, parseDenyRulesTable } from '../build/parser.js';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');

describe('parseRules', () => {
  it('일반 규칙 파일을 파싱한다', async () => {
    const rules = await parseRules(path.join(fixturesDir, 'rules'));
    const rule = rules.find(r => r.id === 'test-rule');

    expect(rule).toBeDefined();
    expect(rule.description).toBe('테스트 규칙');
    expect(rule.platforms).toEqual(['claude', 'gemini', 'codex']);
    expect(rule.section).toBe('테스트');
    expect(rule.order).toBe(1);
    expect(rule.content).toContain('규칙 1');
  });

  it('platforms 생략 시 전체 플랫폼으로 설정한다', async () => {
    const rules = await parseRules(path.join(fixturesDir, 'rules'));
    const deny = rules.find(r => r.id === 'test-deny');

    expect(deny.platforms).toEqual(['claude', 'gemini', 'codex']);
  });

  it('deny-rules 타입의 테이블을 파싱한다', async () => {
    const rules = await parseRules(path.join(fixturesDir, 'rules'));
    const deny = rules.find(r => r.id === 'test-deny');

    expect(deny.type).toBe('deny-rules');
    expect(deny.denyPatterns).toEqual([
      { pattern: 'rm -rf*', description: '재귀 삭제 금지' },
      { pattern: 'sudo *', description: '관리자 권한 금지' },
    ]);
  });
});

describe('parseRoles', () => {
  it('역할 파일을 파싱한다', async () => {
    const roles = await parseRoles(path.join(fixturesDir, 'roles'));
    const role = roles.find(r => r.id === 'test-role');

    expect(role).toBeDefined();
    expect(role.description).toBe('테스트 역할');
    expect(role.transform).toEqual({ claude: 'agent', gemini: 'section', codex: 'section' });
    expect(role.rules).toEqual(['test-rule']);
    expect(role.content).toContain('테스트 역할입니다');
  });
});
