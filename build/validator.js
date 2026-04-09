const VALID_TOOLS = new Set([
  'Read', 'Edit', 'Write', 'Glob', 'Grep', 'NotebookEdit',
  'Bash', 'PowerShell',
  'WebFetch', 'WebSearch',
  'Agent', 'SendMessage', 'TeamCreate', 'TeamDelete',
  'TaskCreate', 'TaskGet', 'TaskList', 'TaskUpdate', 'TaskStop',
  'CronCreate', 'CronDelete', 'CronList',
  'EnterPlanMode', 'ExitPlanMode', 'EnterWorktree', 'ExitWorktree',
  'AskUserQuestion', 'Skill', 'LSP',
]);

function extractToolBase(tool) {
  const match = tool.match(/^(\w+)(\(.*\))?$/);
  return match ? match[1] : null;
}

export function validate(skills, agents) {
  const errors = [];

  // 스킬 필수 필드 검사
  for (const skill of skills) {
    if (!skill.id) {
      errors.push({ type: 'MISSING_FIELD', message: 'skill missing id', target: skill.description || '(unknown)' });
    }
    if (!skill.description) {
      errors.push({ type: 'MISSING_FIELD', message: 'skill missing description', target: skill.id });
    }
    if (!skill.section) {
      errors.push({ type: 'MISSING_FIELD', message: 'skill missing section', target: skill.id });
    }
  }

  // 에이전트 필수 필드 검사
  for (const agent of agents) {
    if (!agent.id) {
      errors.push({ type: 'MISSING_FIELD', message: 'agent missing id', target: agent.description || '(unknown)' });
    }
    if (!agent.description) {
      errors.push({ type: 'MISSING_FIELD', message: 'agent missing description', target: agent.id });
    }
    if (!agent.transform) {
      errors.push({ type: 'MISSING_FIELD', message: 'agent missing transform', target: agent.id });
    }

    // tools 필드 검증
    if (agent.tools != null) {
      if (!Array.isArray(agent.tools)) {
        errors.push({ type: 'INVALID_TOOLS_FORMAT', message: `agent ${agent.id} tools must be an array`, target: agent.id });
      } else {
        for (const tool of agent.tools) {
          const base = extractToolBase(tool);
          if (!base || !VALID_TOOLS.has(base)) {
            errors.push({ type: 'INVALID_TOOL', message: `agent ${agent.id} has invalid tool: ${tool}`, target: agent.id });
          }
        }
      }
    }
  }

  // 스킬 id 중복 검사
  const skillIds = skills.map(s => s.id).filter(Boolean);
  const duplicateSkillIds = skillIds.filter((id, i) => skillIds.indexOf(id) !== i);
  for (const id of new Set(duplicateSkillIds)) {
    errors.push({ type: 'DUPLICATE_RULE_ID', message: `duplicate skill id: ${id}`, target: id });
  }

  // 에이전트 id 중복 검사
  const agentIds = agents.map(a => a.id).filter(Boolean);
  const duplicateAgentIds = agentIds.filter((id, i) => agentIds.indexOf(id) !== i);
  for (const id of new Set(duplicateAgentIds)) {
    errors.push({ type: 'DUPLICATE_ROLE_ID', message: `duplicate agent id: ${id}`, target: id });
  }

  // 에이전트의 스킬 참조 검사
  const skillIdSet = new Set(skillIds);
  for (const agent of agents) {
    for (const skillRef of (agent.skills || [])) {
      if (!skillIdSet.has(skillRef)) {
        errors.push({ type: 'MISSING_RULE_REF', message: `agent ${agent.id} references missing skill: ${skillRef}`, target: agent.id });
      }
    }
  }

  return errors;
}
