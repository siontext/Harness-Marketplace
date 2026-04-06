import { parseRules, parseRoles } from './parser.js';
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
    rulesDir = path.join(ROOT, 'rules'),
    rolesDir = path.join(ROOT, 'roles'),
    templatesDir = path.join(ROOT, 'templates'),
    distDir = path.join(ROOT, 'dist'),
    validateOnly = false,
    dryRun = false,
  } = options;

  // 1. Parse
  const rules = await parseRules(rulesDir);
  const roles = await parseRoles(rolesDir);

  // 2. Validate
  const errors = validate(rules, roles);
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
  const assembled = assemble(rules, roles);

  if (dryRun) {
    console.log('Dry run:');
    console.log(`  Claude: ${assembled.claude.sections.length} sections, ${assembled.claude.roles.length} roles`);
    console.log(`  Gemini: ${assembled.gemini.sections.length} sections, ${assembled.gemini.roles.length} roles`);
    console.log(`  Codex: ${assembled.codex.sections.length} sections, ${assembled.codex.roles.length} roles`);
    return;
  }

  // 4. Render & Write

  // Claude
  const claudeDir = path.join(distDir, 'claude');
  await fs.mkdir(claudeDir, { recursive: true });

  const claudeTemplate = await fs.readFile(path.join(templatesDir, 'claude', 'CLAUDE.md.hbs'), 'utf-8');
  const claudeData = {
    ...assembled.claude,
    denySection: assembled.claude.denyPatterns.length > 0,
    denyPatterns: assembled.claude.denyPatterns,
  };
  await fs.writeFile(path.join(claudeDir, 'CLAUDE.md'), renderTemplate(claudeTemplate, claudeData));

  // Claude agents
  const agentsDir = path.join(claudeDir, 'agents');
  await fs.mkdir(agentsDir, { recursive: true });
  const agentTemplate = await fs.readFile(path.join(templatesDir, 'claude', 'agents', 'agent.md.hbs'), 'utf-8');
  for (const role of assembled.claude.roles) {
    if (role.transform?.claude === 'agent') {
      await fs.writeFile(path.join(agentsDir, `${role.id}.md`), renderTemplate(agentTemplate, role));
    }
  }

  // Claude skills (only rules referenced by roles)
  const skillsDir = path.join(claudeDir, 'skills');
  for (const rule of assembled.claude.skillRules) {
    const skillDir = path.join(skillsDir, rule.id);
    await fs.mkdir(skillDir, { recursive: true });
    await fs.writeFile(path.join(skillDir, 'SKILL.md'), `---\nname: ${rule.id}\ndescription: ${rule.description}\n---\n\n${rule.content}\n`);
  }

  // Gemini
  const geminiDir = path.join(distDir, 'gemini');
  await fs.mkdir(geminiDir, { recursive: true });

  const geminiTemplate = await fs.readFile(path.join(templatesDir, 'gemini', 'GEMINI.md.hbs'), 'utf-8');
  await fs.writeFile(path.join(geminiDir, 'GEMINI.md'), renderTemplate(geminiTemplate, assembled.gemini));
  await fs.writeFile(path.join(geminiDir, 'settings.json'), generateGeminiSettings(assembled.gemini.denyPatterns));

  // Gemini roles (separate files for on-demand loading)
  const geminiRolesDir = path.join(geminiDir, 'roles');
  await fs.mkdir(geminiRolesDir, { recursive: true });
  for (const role of assembled.gemini.roles) {
    await fs.writeFile(path.join(geminiRolesDir, `${role.id}.md`), `# ${role.description}\n\n${role.content}\n`);
  }

  // Codex
  const codexDir = path.join(distDir, 'codex');
  await fs.mkdir(codexDir, { recursive: true });

  const codexTemplate = await fs.readFile(path.join(templatesDir, 'codex', 'AGENTS.md.hbs'), 'utf-8');
  await fs.writeFile(path.join(codexDir, 'AGENTS.md'), renderTemplate(codexTemplate, assembled.codex));
  await fs.writeFile(path.join(codexDir, 'config.json'), generateCodexConfig(assembled.codex.denyPatterns));

  // Codex roles (separate files for on-demand loading)
  const codexRolesDir = path.join(codexDir, 'roles');
  await fs.mkdir(codexRolesDir, { recursive: true });
  for (const role of assembled.codex.roles) {
    await fs.writeFile(path.join(codexRolesDir, `${role.id}.md`), `# ${role.description}\n\n${role.content}\n`);
  }

  const summary = {
    claude: { sections: assembled.claude.sections.length, agents: assembled.claude.roles.filter(r => r.transform?.claude === 'agent').length, skills: assembled.claude.skillRules.length },
    gemini: { sections: assembled.gemini.sections.length, roles: assembled.gemini.roles.length },
    codex: { sections: assembled.codex.sections.length, roles: assembled.codex.roles.length },
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
