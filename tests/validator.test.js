import { describe, it, expect } from 'vitest';
import { validate } from '../build/validator.js';

describe('validate', () => {
  it('유효한 데이터는 오류 없이 통과한다', () => {
    const skills = [
      { id: 'skill-a', description: 'A', section: '섹션', platforms: ['claude'] },
      { id: 'skill-b', description: 'B', section: '섹션', platforms: ['claude'] },
    ];
    const agents = [
      { id: 'agent-a', description: 'A', transform: { claude: 'agent' }, skills: ['skill-a'] },
    ];
    const errors = validate(skills, agents);
    expect(errors).toEqual([]);
  });

  it('스킬 id 중복을 감지한다', () => {
    const skills = [
      { id: 'dup', description: 'A', section: '섹션' },
      { id: 'dup', description: 'B', section: '섹션' },
    ];
    const errors = validate(skills, []);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'DUPLICATE_RULE_ID' }));
  });

  it('에이전트가 존재하지 않는 스킬을 참조하면 오류', () => {
    const skills = [{ id: 'skill-a', description: 'A', section: '섹션' }];
    const agents = [{ id: 'agent-a', description: 'A', transform: { claude: 'agent' }, skills: ['skill-a', 'nonexistent'] }];
    const errors = validate(skills, agents);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'MISSING_RULE_REF' }));
  });

  it('필수 필드 누락을 감지한다 — 스킬', () => {
    const skills = [{ description: 'no id', section: '섹션' }];
    const errors = validate(skills, []);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'MISSING_FIELD' }));
  });

  it('필수 필드 누락을 감지한다 — 에이전트', () => {
    const agents = [{ id: 'agent-a', description: 'A' }];
    const errors = validate([], agents);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'MISSING_FIELD' }));
  });

  it('에이전트 id 중복을 감지한다', () => {
    const agents = [
      { id: 'dup', description: 'A', transform: { claude: 'agent' }, skills: [] },
      { id: 'dup', description: 'B', transform: { claude: 'agent' }, skills: [] },
    ];
    const errors = validate([], agents);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'DUPLICATE_ROLE_ID' }));
  });
});
