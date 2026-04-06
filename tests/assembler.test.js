import { describe, it, expect } from 'vitest';
import { assemble } from '../build/assembler.js';

const rules = [
  { id: 'rule-a', description: 'A', section: '아키텍처', order: 2, platforms: ['claude', 'gemini', 'codex'], content: 'Rule A content' },
  { id: 'rule-b', description: 'B', section: '아키텍처', order: 1, platforms: ['claude', 'gemini', 'codex'], content: 'Rule B content' },
  { id: 'rule-c', description: 'C', section: '코딩', order: 1, platforms: ['claude'], content: 'Rule C content' },
  { id: 'deny-rules', description: 'Deny', section: '보안', type: 'deny-rules', platforms: ['claude', 'gemini', 'codex'], content: 'deny table', denyPatterns: [
    { pattern: 'rm -rf*', description: '삭제 금지' },
  ]},
];

const roles = [
  { id: 'reviewer', description: '리뷰어', platforms: ['claude', 'gemini', 'codex'], transform: { claude: 'agent', gemini: 'section', codex: 'section' }, rules: ['rule-a', 'rule-b'], content: 'Reviewer content' },
];

describe('assemble', () => {
  it('플랫폼별 데이터를 생성한다', () => {
    const result = assemble(rules, roles);
    expect(result.claude).toBeDefined();
    expect(result.gemini).toBeDefined();
    expect(result.codex).toBeDefined();
  });

  it('규칙을 section별로 그룹핑하고 order로 정렬한다', () => {
    const result = assemble(rules, roles);
    const archSection = result.claude.sections.find(s => s.name === '아키텍처');
    expect(archSection.rules[0].id).toBe('rule-b');
    expect(archSection.rules[1].id).toBe('rule-a');
  });

  it('플랫폼 필터링을 적용한다', () => {
    const result = assemble(rules, roles);
    const codingSection = result.gemini.sections.find(s => s.name === '코딩');
    expect(codingSection).toBeUndefined();
  });

  it('deny 패턴을 추출한다', () => {
    const result = assemble(rules, roles);
    expect(result.gemini.denyPatterns).toEqual([{ pattern: 'rm -rf*', description: '삭제 금지' }]);
    expect(result.codex.denyPatterns).toEqual([{ pattern: 'rm -rf*', description: '삭제 금지' }]);
  });

  it('역할의 참조 규칙 id를 resolve한다', () => {
    const result = assemble(rules, roles);
    const reviewer = result.claude.roles[0];
    expect(reviewer.rules).toEqual(['rule-a', 'rule-b']);
  });

  it('스킬 생성 대상 규칙을 식별한다', () => {
    const result = assemble(rules, roles);
    expect(result.claude.skillRules).toBeDefined();
    expect(result.claude.skillRules.map(r => r.id)).toContain('rule-a');
    expect(result.claude.skillRules.map(r => r.id)).toContain('rule-b');
    expect(result.claude.skillRules.map(r => r.id)).not.toContain('deny-rules');
  });
});
