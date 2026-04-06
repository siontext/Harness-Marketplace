import { describe, it, expect, afterAll } from 'vitest';
import { build } from '../build/index.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const fixturesDir = path.join(__dirname, 'fixtures');
const tempDist = path.join(__dirname, 'temp-dist');
const templatesDir = path.join(__dirname, '..', 'templates');

afterAll(async () => {
  await fs.rm(tempDist, { recursive: true, force: true });
});

describe('build', () => {
  it('전체 빌드 파이프라인을 실행한다', async () => {
    await build({
      skillsDir: path.join(fixturesDir, 'skills'),
      agentsDir: path.join(fixturesDir, 'agents'),
      templatesDir,
      distDir: tempDist,
    });

    // CLAUDE.md 생성 확인 (목차만, 인라인 아님)
    const claudeMd = await fs.readFile(path.join(tempDist, 'claude', 'CLAUDE.md'), 'utf-8');
    expect(claudeMd).toContain('Project Guidelines');
    expect(claudeMd).toContain('test-rule');

    // Claude 에이전트 파일 생성 확인
    const agentMd = await fs.readFile(path.join(tempDist, 'claude', 'agents', 'test-role.md'), 'utf-8');
    expect(agentMd).toContain('name: test-role');
    expect(agentMd).toContain('테스트 역할 내용');

    // Claude 스킬 파일 생성 확인
    const skillMd = await fs.readFile(path.join(tempDist, 'claude', 'skills', 'test-rule', 'SKILL.md'), 'utf-8');
    expect(skillMd).toContain('테스트 규칙 내용');

    // GEMINI.md 생성 확인 (목차만)
    const geminiMd = await fs.readFile(path.join(tempDist, 'gemini', 'GEMINI.md'), 'utf-8');
    expect(geminiMd).toContain('Project Guidelines');
    expect(geminiMd).toContain('agents/test-role.md');
    expect(geminiMd).toContain('skills/test-rule.md');

    // Gemini 에이전트/스킬 파일 생성 확인
    const geminiAgent = await fs.readFile(path.join(tempDist, 'gemini', 'agents', 'test-role.md'), 'utf-8');
    expect(geminiAgent).toContain('테스트 역할');
    const geminiSkill = await fs.readFile(path.join(tempDist, 'gemini', 'skills', 'test-rule.md'), 'utf-8');
    expect(geminiSkill).toContain('테스트 규칙 내용');

    // Gemini settings.json 생성 확인
    const geminiSettings = JSON.parse(await fs.readFile(path.join(tempDist, 'gemini', 'settings.json'), 'utf-8'));
    expect(geminiSettings.deny_rules).toBeDefined();
    expect(geminiSettings.deny_rules.length).toBeGreaterThan(0);

    // AGENTS.md 생성 확인 (목차만)
    const agentsMd = await fs.readFile(path.join(tempDist, 'codex', 'AGENTS.md'), 'utf-8');
    expect(agentsMd).toContain('Project Guidelines');
    expect(agentsMd).toContain('agents/test-role.md');

    // Codex 에이전트/스킬 파일 생성 확인
    const codexAgent = await fs.readFile(path.join(tempDist, 'codex', 'agents', 'test-role.md'), 'utf-8');
    expect(codexAgent).toContain('테스트 역할');

    // Codex config.json 생성 확인
    const codexConfig = JSON.parse(await fs.readFile(path.join(tempDist, 'codex', 'config.json'), 'utf-8'));
    expect(codexConfig.deny_rules).toBeDefined();
  });
});
