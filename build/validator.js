export function validate(rules, roles) {
  const errors = [];

  // 규칙 필수 필드 검사
  for (const rule of rules) {
    if (!rule.id) {
      errors.push({ type: 'MISSING_FIELD', message: 'rule missing id', target: rule.description || '(unknown)' });
    }
    if (!rule.description) {
      errors.push({ type: 'MISSING_FIELD', message: 'rule missing description', target: rule.id });
    }
    if (!rule.section) {
      errors.push({ type: 'MISSING_FIELD', message: 'rule missing section', target: rule.id });
    }
  }

  // 역할 필수 필드 검사
  for (const role of roles) {
    if (!role.id) {
      errors.push({ type: 'MISSING_FIELD', message: 'role missing id', target: role.description || '(unknown)' });
    }
    if (!role.description) {
      errors.push({ type: 'MISSING_FIELD', message: 'role missing description', target: role.id });
    }
    if (!role.transform) {
      errors.push({ type: 'MISSING_FIELD', message: 'role missing transform', target: role.id });
    }
  }

  // 규칙 id 중복 검사
  const ruleIds = rules.map(r => r.id).filter(Boolean);
  const duplicateRuleIds = ruleIds.filter((id, i) => ruleIds.indexOf(id) !== i);
  for (const id of new Set(duplicateRuleIds)) {
    errors.push({ type: 'DUPLICATE_RULE_ID', message: `duplicate rule id: ${id}`, target: id });
  }

  // 역할 id 중복 검사
  const roleIds = roles.map(r => r.id).filter(Boolean);
  const duplicateRoleIds = roleIds.filter((id, i) => roleIds.indexOf(id) !== i);
  for (const id of new Set(duplicateRoleIds)) {
    errors.push({ type: 'DUPLICATE_ROLE_ID', message: `duplicate role id: ${id}`, target: id });
  }

  // 역할의 규칙 참조 검사
  const ruleIdSet = new Set(ruleIds);
  for (const role of roles) {
    for (const ruleRef of (role.rules || [])) {
      if (!ruleIdSet.has(ruleRef)) {
        errors.push({ type: 'MISSING_RULE_REF', message: `role ${role.id} references missing rule: ${ruleRef}`, target: role.id });
      }
    }
  }

  return errors;
}
