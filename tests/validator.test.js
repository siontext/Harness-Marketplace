import { describe, it, expect } from 'vitest';
import { validate } from '../build/validator.js';

describe('validate', () => {
  it('유효한 데이터는 오류 없이 통과한다', () => {
    const rules = [
      { id: 'rule-a', description: 'A', section: '섹션', platforms: ['claude'] },
      { id: 'rule-b', description: 'B', section: '섹션', platforms: ['claude'] },
    ];
    const roles = [
      { id: 'role-a', description: 'A', transform: { claude: 'agent' }, rules: ['rule-a'] },
    ];
    const errors = validate(rules, roles);
    expect(errors).toEqual([]);
  });

  it('규칙 id 중복을 감지한다', () => {
    const rules = [
      { id: 'dup', description: 'A', section: '섹션' },
      { id: 'dup', description: 'B', section: '섹션' },
    ];
    const errors = validate(rules, []);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'DUPLICATE_RULE_ID' }));
  });

  it('역할이 존재하지 않는 규칙을 참조하면 오류', () => {
    const rules = [{ id: 'rule-a', description: 'A', section: '섹션' }];
    const roles = [{ id: 'role-a', description: 'A', transform: { claude: 'agent' }, rules: ['rule-a', 'nonexistent'] }];
    const errors = validate(rules, roles);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'MISSING_RULE_REF' }));
  });

  it('필수 필드 누락을 감지한다 — 규칙', () => {
    const rules = [{ description: 'no id', section: '섹션' }];
    const errors = validate(rules, []);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'MISSING_FIELD' }));
  });

  it('필수 필드 누락을 감지한다 — 역할', () => {
    const roles = [{ id: 'role-a', description: 'A' }];
    const errors = validate([], roles);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'MISSING_FIELD' }));
  });

  it('역할 id 중복을 감지한다', () => {
    const roles = [
      { id: 'dup', description: 'A', transform: { claude: 'agent' }, rules: [] },
      { id: 'dup', description: 'B', transform: { claude: 'agent' }, rules: [] },
    ];
    const errors = validate([], roles);
    expect(errors).toContainEqual(expect.objectContaining({ type: 'DUPLICATE_ROLE_ID' }));
  });
});
