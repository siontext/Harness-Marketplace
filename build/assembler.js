function groupBySection(skills) {
  const groups = new Map();
  for (const skill of skills) {
    if (skill.type === 'deny-rules') continue;
    if (!groups.has(skill.section)) groups.set(skill.section, []);
    groups.get(skill.section).push(skill);
  }
  const sections = [];
  for (const [name, sectionSkills] of groups) {
    sectionSkills.sort((a, b) => {
      const orderA = a.order ?? Infinity;
      const orderB = b.order ?? Infinity;
      if (orderA !== orderB) return orderA - orderB;
      return a.id.localeCompare(b.id);
    });
    sections.push({ name, rules: sectionSkills });
  }
  sections.sort((a, b) => a.name.localeCompare(b.name));
  return sections;
}

function filterByPlatform(items, platform) {
  return items.filter(item => item.platforms.includes(platform));
}

function extractDenyPatterns(skills) {
  const denySkill = skills.find(s => s.type === 'deny-rules');
  return denySkill?.denyPatterns || [];
}

function collectReferencedSkills(agents, skills) {
  const referencedIds = new Set();
  for (const agent of agents) {
    for (const skillId of (agent.skills || [])) {
      referencedIds.add(skillId);
    }
  }
  return skills.filter(s => referencedIds.has(s.id));
}

export function assemble(skills, agents) {
  const platforms = ['claude', 'gemini', 'codex'];
  const result = {};
  for (const platform of platforms) {
    const platformSkills = filterByPlatform(skills, platform);
    const platformAgents = filterByPlatform(agents, platform);
    const sections = groupBySection(platformSkills);
    const denyPatterns = extractDenyPatterns(platformSkills);
    const platformData = { sections, roles: platformAgents, denyPatterns };
    if (platform === 'claude') {
      platformData.skillRules = collectReferencedSkills(platformAgents, platformSkills);
    }
    result[platform] = platformData;
  }
  return result;
}
