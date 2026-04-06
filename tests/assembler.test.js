import { describe, it, expect } from 'vitest';
import { assemble } from '../build/assembler.js';

const skills = [
  { id: 'skill-a', description: 'A', section: '아키텍처', order: 2, platforms: ['claude', 'gemini', 'codex'], content: 'Skill A content' },
  { id: 'skill-b', description: 'B', section: '아키텍처', order: 1, platforms: ['claude', 'gemini', 'codex'], content: 'Skill B content' },
  { id: 'skill-c', description: 'C', section: '코딩', order: 1, platforms: ['claude'], content: 'Skill C content' },
  { id: 'deny-rules', description: 'Deny', section: '보안', type: 'deny-rules', platforms: ['claude', 'gemini', 'codex'], content: 'deny table', denyPatterns: [
    { pattern: 'rm -rf*', description: '삭제 금지' },
  ]},
];

const agents = [
  { id: 'reviewer', description: '리뷰어', platforms: ['claude', 'gemini', 'codex'], transform: { claude: 'agent', gemini: 'section', codex: 'section' }, skills: ['skill-a', 'skill-b'], content: 'Reviewer content' },
];

describe('assemble', () => {
  it('플랫폼별 데이터를 생성한다', () => {
    const result = assemble(skills, agents);
    expect(result.claude).toBeDefined();
    expect(result.gemini).toBeDefined();
    expect(result.codex).toBeDefined();
  });

  it('스킬을 section별로 그룹핑하고 order로 정렬한다', () => {
    const result = assemble(skills, agents);
    const archSection = result.claude.sections.find(s => s.name === '아키텍처');
    expect(archSection.rules[0].id).toBe('skill-b');
    expect(archSection.rules[1].id).toBe('skill-a');
  });

  it('플랫폼 필터링을 적용한다', () => {
    const result = assemble(skills, agents);
    const codingSection = result.gemini.sections.find(s => s.name === '코딩');
    expect(codingSection).toBeUndefined();
  });

  it('deny 패턴을 추출한다', () => {
    const result = assemble(skills, agents);
    expect(result.gemini.denyPatterns).toEqual([{ pattern: 'rm -rf*', description: '삭제 금지' }]);
    expect(result.codex.denyPatterns).toEqual([{ pattern: 'rm -rf*', description: '삭제 금지' }]);
  });

  it('에이전트의 참조 스킬 id를 유지한다', () => {
    const result = assemble(skills, agents);
    const reviewer = result.claude.roles[0];
    expect(reviewer.skills).toEqual(['skill-a', 'skill-b']);
  });

  it('스킬 생성 대상을 식별한다', () => {
    const result = assemble(skills, agents);
    expect(result.claude.skillRules).toBeDefined();
    expect(result.claude.skillRules.map(s => s.id)).toContain('skill-a');
    expect(result.claude.skillRules.map(s => s.id)).toContain('skill-b');
    expect(result.claude.skillRules.map(s => s.id)).not.toContain('deny-rules');
  });
});
