function groupBySection(rules) {
  const groups = new Map();
  for (const rule of rules) {
    if (rule.type === 'deny-rules') continue;
    if (!groups.has(rule.section)) groups.set(rule.section, []);
    groups.get(rule.section).push(rule);
  }
  const sections = [];
  for (const [name, sectionRules] of groups) {
    sectionRules.sort((a, b) => {
      const orderA = a.order ?? Infinity;
      const orderB = b.order ?? Infinity;
      if (orderA !== orderB) return orderA - orderB;
      return a.id.localeCompare(b.id);
    });
    sections.push({ name, rules: sectionRules });
  }
  return sections;
}

function filterByPlatform(items, platform) {
  return items.filter(item => item.platforms.includes(platform));
}

function extractDenyPatterns(rules) {
  const denyRule = rules.find(r => r.type === 'deny-rules');
  return denyRule?.denyPatterns || [];
}

function collectSkillRules(roles, rules) {
  const referencedIds = new Set();
  for (const role of roles) {
    for (const ruleId of role.rules) {
      referencedIds.add(ruleId);
    }
  }
  return rules.filter(r => referencedIds.has(r.id));
}

export function assemble(rules, roles) {
  const platforms = ['claude', 'gemini', 'codex'];
  const result = {};
  for (const platform of platforms) {
    const platformRules = filterByPlatform(rules, platform);
    const platformRoles = filterByPlatform(roles, platform);
    const sections = groupBySection(platformRules);
    const denyPatterns = extractDenyPatterns(platformRules);
    const platformData = { sections, roles: platformRoles, denyPatterns };
    if (platform === 'claude') {
      platformData.skillRules = collectSkillRules(platformRoles, platformRules);
    }
    result[platform] = platformData;
  }
  return result;
}
