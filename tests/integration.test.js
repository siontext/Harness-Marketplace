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
      rulesDir: path.join(fixturesDir, 'rules'),
      rolesDir: path.join(fixturesDir, 'roles'),
      templatesDir,
      distDir: tempDist,
    });

    // CLAUDE.md 생성 확인
    const claudeMd = await fs.readFile(path.join(tempDist, 'claude', 'CLAUDE.md'), 'utf-8');
    expect(claudeMd).toContain('Project Guidelines');
    expect(claudeMd).toContain('테스트 규칙 내용');

    // 에이전트 파일 생성 확인
    const agentMd = await fs.readFile(path.join(tempDist, 'claude', 'agents', 'test-role.md'), 'utf-8');
    expect(agentMd).toContain('name: test-role');
    expect(agentMd).toContain('테스트 역할 내용');

    // 스킬 파일 생성 확인
    const skillMd = await fs.readFile(path.join(tempDist, 'claude', 'skills', 'test-rule', 'SKILL.md'), 'utf-8');
    expect(skillMd).toContain('테스트 규칙 내용');

    // GEMINI.md 생성 확인
    const geminiMd = await fs.readFile(path.join(tempDist, 'gemini', 'GEMINI.md'), 'utf-8');
    expect(geminiMd).toContain('Project Guidelines');
    expect(geminiMd).toContain('테스트 역할');

    // Gemini settings.json 생성 확인
    const geminiSettings = JSON.parse(await fs.readFile(path.join(tempDist, 'gemini', 'settings.json'), 'utf-8'));
    expect(geminiSettings.deny_rules).toBeDefined();
    expect(geminiSettings.deny_rules.length).toBeGreaterThan(0);

    // AGENTS.md 생성 확인
    const agentsMd = await fs.readFile(path.join(tempDist, 'codex', 'AGENTS.md'), 'utf-8');
    expect(agentsMd).toContain('Project Guidelines');

    // Codex config.json 생성 확인
    const codexConfig = JSON.parse(await fs.readFile(path.join(tempDist, 'codex', 'config.json'), 'utf-8'));
    expect(codexConfig.deny_rules).toBeDefined();
  });
});
