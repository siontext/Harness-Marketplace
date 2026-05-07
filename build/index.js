import { parseSkills, parseAgents } from './parser.js';
import { validate } from './validator.js';
import { assemble } from './assembler.js';
import { renderTemplate } from './renderer.js';
import { generateGeminiSettings, generateCodexConfig } from './settings-generator.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

export async function build(options = {}) {
  const {
    skillsDir = path.join(ROOT, 'skills'),
    agentsDir = path.join(ROOT, 'agents'),
    templatesDir = path.join(ROOT, 'templates'),
    distDir = path.join(ROOT, 'dist'),
    validateOnly = false,
    dryRun = false,
  } = options;

  // 1. Parse
  const skills = await parseSkills(skillsDir);
  const agents = await parseAgents(agentsDir);

  // 2. Validate
  const errors = validate(skills, agents);
  if (errors.length > 0) {
    console.error('Validation errors:');
    for (const err of errors) {
      console.error(`  [${err.type}] ${err.message}`);
    }
    throw new Error(`${errors.length} validation errors found`);
  }

  if (validateOnly) {
    console.log('Validation passed');
    return;
  }

  // 3. Assemble
  const assembled = assemble(skills, agents);

  if (dryRun) {
    console.log('Dry run:');
    console.log(`  Claude: ${assembled.claude.sections.length} sections, ${assembled.claude.roles.length} agents`);
    console.log(`  Gemini: ${assembled.gemini.sections.length} sections, ${assembled.gemini.roles.length} agents`);
    console.log(`  Codex: ${assembled.codex.sections.length} sections, ${assembled.codex.roles.length} agents`);
    return;
  }

  // 4. Render & Write

  // Claude
  const claudeDir = path.join(distDir, 'claude');
  await fs.mkdir(claudeDir, { recursive: true });

  // Claude plugin.json for plugin system
  const pkgJson = JSON.parse(await fs.readFile(path.join(ROOT, 'package.json'), 'utf-8'));
  const pluginMeta = { name: 'harness', description: '크로스 플랫폼 AI 에이전트 하네스', version: pkgJson.version };
  await fs.writeFile(path.join(claudeDir, 'plugin.json'), JSON.stringify(pluginMeta, null, 2));

  const claudeTemplate = await fs.readFile(path.join(templatesDir, 'claude', 'CLAUDE.md.hbs'), 'utf-8');
  const claudeData = {
    ...assembled.claude,
    denySection: assembled.claude.denyPatterns.length > 0,
    denyPatterns: assembled.claude.denyPatterns,
  };
  await fs.writeFile(path.join(claudeDir, 'CLAUDE.md'), renderTemplate(claudeTemplate, claudeData));

  // Claude agents
  const claudeAgentsDir = path.join(claudeDir, 'agents');
  await fs.mkdir(claudeAgentsDir, { recursive: true });
  const agentTemplate = await fs.readFile(path.join(templatesDir, 'claude', 'agents', 'agent.md.hbs'), 'utf-8');
  for (const agent of assembled.claude.roles) {
    if (agent.transform?.claude === 'agent') {
      await fs.writeFile(path.join(claudeAgentsDir, `${agent.id}.md`), renderTemplate(agentTemplate, agent));
    }
  }

  // Claude hooks
  const claudeHooksDir = path.join(claudeDir, 'hooks');
  await fs.mkdir(claudeHooksDir, { recursive: true });
  const hooksJson = {
    hooks: {
      PreToolUse: [
        {
          matcher: 'Agent',
          hooks: [
            {
              type: 'command',
              command: "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PreToolUse\", \"additionalContext\": \"[AGENT HARNESS REMINDER] 에이전트를 호출하기 전에 반드시 해당 에이전트의 하네스 파일을 읽으세요. 파일 위치: ~/.claude/plugins/marketplaces/team-harness/agents/<agent-id>.md (예: designer.md, backend-dev.md). 하네스를 읽어야 통신 프로토콜(브리지 형식, AskUserQuestion 중계 등)을 정확히 파악할 수 있습니다.\"}}'",
              statusMessage: '에이전트 하네스 확인 중...',
            },
          ],
        },
      ],
    },
  };
  await fs.writeFile(path.join(claudeHooksDir, 'hooks.json'), JSON.stringify(hooksJson, null, 2));

  // Claude skills (only skills referenced by agents)
  const claudeSkillsDir = path.join(claudeDir, 'skills');
  for (const skill of assembled.claude.skillRules) {
    const skillDir = path.join(claudeSkillsDir, skill.id);
    await fs.mkdir(skillDir, { recursive: true });
    await fs.writeFile(path.join(skillDir, 'SKILL.md'), `---\nname: ${skill.id}\ndescription: ${skill.description}\n---\n\n${skill.content}\n`);
  }

  // Gemini
  const geminiDir = path.join(distDir, 'gemini');
  await fs.mkdir(geminiDir, { recursive: true });

  const geminiTemplate = await fs.readFile(path.join(templatesDir, 'gemini', 'GEMINI.md.hbs'), 'utf-8');
  await fs.writeFile(path.join(geminiDir, 'GEMINI.md'), renderTemplate(geminiTemplate, assembled.gemini));
  await fs.writeFile(path.join(geminiDir, 'settings.json'), generateGeminiSettings(assembled.gemini.denyPatterns));

  // Gemini agents (template-based)
  const geminiAgentsDir = path.join(geminiDir, 'agents');
  await fs.mkdir(geminiAgentsDir, { recursive: true });
  const geminiAgentTemplate = await fs.readFile(path.join(templatesDir, 'gemini', 'agents', 'agent.md.hbs'), 'utf-8');
  for (const agent of assembled.gemini.roles) {
    await fs.writeFile(path.join(geminiAgentsDir, `${agent.id}.md`), renderTemplate(geminiAgentTemplate, agent));
  }

  // Gemini skills (separate files for on-demand loading)
  const geminiSkillsDir = path.join(geminiDir, 'skills');
  await fs.mkdir(geminiSkillsDir, { recursive: true });
  for (const section of assembled.gemini.sections) {
    for (const skill of section.rules) {
      await fs.writeFile(path.join(geminiSkillsDir, `${skill.id}.md`), `# ${skill.description}\n\n${skill.content}\n`);
    }
  }

  // Codex
  const codexDir = path.join(distDir, 'codex');
  await fs.mkdir(codexDir, { recursive: true });

  const codexTemplate = await fs.readFile(path.join(templatesDir, 'codex', 'AGENTS.md.hbs'), 'utf-8');
  await fs.writeFile(path.join(codexDir, 'AGENTS.md'), renderTemplate(codexTemplate, assembled.codex));
  await fs.writeFile(path.join(codexDir, 'config.json'), generateCodexConfig(assembled.codex.denyPatterns));

  // Codex agents (TOML format, template-based)
  const codexAgentsDir = path.join(codexDir, 'agents');
  await fs.mkdir(codexAgentsDir, { recursive: true });
  const codexAgentTemplate = await fs.readFile(path.join(templatesDir, 'codex', 'agents', 'agent.toml.hbs'), 'utf-8');
  for (const agent of assembled.codex.roles) {
    await fs.writeFile(path.join(codexAgentsDir, `${agent.id}.toml`), renderTemplate(codexAgentTemplate, agent));
  }

  // Codex skills (SKILL.md format in skill-name/ folders, same as Claude)
  const codexSkillsDir = path.join(codexDir, 'skills');
  for (const section of assembled.codex.sections) {
    for (const skill of section.rules) {
      const skillDir = path.join(codexSkillsDir, skill.id);
      await fs.mkdir(skillDir, { recursive: true });
      await fs.writeFile(path.join(skillDir, 'SKILL.md'), `---\nname: ${skill.id}\ndescription: ${skill.description}\n---\n\n${skill.content}\n`);
    }
  }

  const summary = {
    claude: { sections: assembled.claude.sections.length, agents: assembled.claude.roles.filter(a => a.transform?.claude === 'agent').length, skills: assembled.claude.skillRules.length },
    gemini: { sections: assembled.gemini.sections.length, agents: assembled.gemini.roles.length },
    codex: { sections: assembled.codex.sections.length, agents: assembled.codex.roles.length },
  };
  console.log('Build complete:', JSON.stringify(summary, null, 2));

  return summary;
}

// CLI entry
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  const validateOnly = process.argv.includes('--validate-only');
  const dryRun = process.argv.includes('--dry-run');
  build({ validateOnly, dryRun }).catch(err => {
    console.error(err.message);
    process.exit(1);
  });
}
