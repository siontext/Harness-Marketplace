import { describe, it, expect } from 'vitest';
import { parseSkills, parseAgents, parseDenyRulesTable } from '../build/parser.js';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');

describe('parseSkills', () => {
  it('스킬 파일을 파싱한다', async () => {
    const skills = await parseSkills(path.join(fixturesDir, 'skills'));
    const skill = skills.find(s => s.id === 'test-rule');

    expect(skill).toBeDefined();
    expect(skill.description).toBe('테스트 규칙');
    expect(skill.platforms).toEqual(['claude', 'gemini', 'codex']);
    expect(skill.section).toBe('테스트');
    expect(skill.order).toBe(1);
    expect(skill.content).toContain('규칙 1');
  });

  it('platforms 생략 시 전체 플랫폼으로 설정한다', async () => {
    const skills = await parseSkills(path.join(fixturesDir, 'skills'));
    const deny = skills.find(s => s.id === 'test-deny');

    expect(deny.platforms).toEqual(['claude', 'gemini', 'codex']);
  });

  it('deny-rules 타입의 테이블을 파싱한다', async () => {
    const skills = await parseSkills(path.join(fixturesDir, 'skills'));
    const deny = skills.find(s => s.id === 'test-deny');

    expect(deny.type).toBe('deny-rules');
    expect(deny.denyPatterns).toEqual([
      { pattern: 'rm -rf*', description: '재귀 삭제 금지', alternative: null, exceptions: [] },
      { pattern: 'sudo *', description: '관리자 권한 금지', alternative: null, exceptions: [] },
    ]);
  });
});

describe('parseAgents', () => {
  it('에이전트 파일을 파싱한다', async () => {
    const agents = await parseAgents(path.join(fixturesDir, 'agents'));
    const agent = agents.find(a => a.id === 'test-role');

    expect(agent).toBeDefined();
    expect(agent.description).toBe('테스트 역할');
    expect(agent.transform).toEqual({ claude: 'agent', gemini: 'section', codex: 'section' });
    expect(agent.skills).toEqual(['test-rule']);
    expect(agent.content).toContain('테스트 역할입니다');
  });
});

describe('parseDenyRulesTable — 예외 열', () => {
  const table = [
    '| 패턴 | 설명 | 대체 방법 | 예외 |',
    '|---|---|---|---|',
    '| rm -rf* | 재귀 삭제 금지 | 개별 파일 삭제 | |',
    '| git push --force* | 강제 푸시 금지 | force-with-lease 사용 | git push --force-with-lease* |',
  ].join('\n');

  it('비어 있는 예외 열을 빈 배열로 읽는다', () => {
    const [rule] = parseDenyRulesTable(table);
    expect(rule.pattern).toBe('rm -rf*');
    expect(rule.alternative).toBe('개별 파일 삭제');
    expect(rule.exceptions).toEqual([]);
  });

  it('예외 열이 채워진 행은 배열로 읽는다', () => {
    const rule = parseDenyRulesTable(table)[1];
    expect(rule.exceptions).toEqual(['git push --force-with-lease*']);
  });
});
