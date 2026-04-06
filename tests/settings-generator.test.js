import { describe, it, expect } from 'vitest';
import { generateGeminiSettings, generateCodexConfig } from '../build/settings-generator.js';

const denyPatterns = [
  { pattern: 'rm -rf*', description: '재귀 삭제 금지' },
  { pattern: 'sudo *', description: '관리자 권한 금지' },
];

describe('generateGeminiSettings', () => {
  it('deny_rules 배열이 포함된 JSON을 생성한다', () => {
    const result = generateGeminiSettings(denyPatterns);
    const parsed = JSON.parse(result);
    expect(parsed.deny_rules).toHaveLength(2);
    expect(parsed.deny_rules[0]).toEqual({ tool: 'shell', pattern: 'rm -rf*' });
    expect(parsed.deny_rules[1]).toEqual({ tool: 'shell', pattern: 'sudo *' });
  });

  it('빈 패턴이면 빈 배열을 생성한다', () => {
    const result = generateGeminiSettings([]);
    const parsed = JSON.parse(result);
    expect(parsed.deny_rules).toEqual([]);
  });
});

describe('generateCodexConfig', () => {
  it('deny_rules 배열이 포함된 JSON을 생성한다', () => {
    const result = generateCodexConfig(denyPatterns);
    const parsed = JSON.parse(result);
    expect(parsed.deny_rules).toHaveLength(2);
    expect(parsed.deny_rules[0]).toEqual({ tool: 'shell', pattern: 'rm -rf*' });
  });
});
