import { describe, it, expect } from 'vitest';
import { renderTemplate } from '../build/renderer.js';

describe('renderTemplate', () => {
  it('sections와 roles를 렌더링한다', () => {
    const template = '{{#each sections}}## {{name}}\n{{#each rules}}{{{content}}}\n{{/each}}{{/each}}{{#each roles}}- {{id}}: {{description}}\n{{/each}}';
    const data = {
      sections: [{ name: '아키텍처', rules: [{ content: 'Rule A' }] }],
      roles: [{ id: 'reviewer', description: '리뷰어' }],
    };
    const result = renderTemplate(template, data);
    expect(result).toContain('## 아키텍처');
    expect(result).toContain('Rule A');
    expect(result).toContain('reviewer: 리뷰어');
  });

  it('빈 데이터를 처리한다', () => {
    const template = '{{#each sections}}{{name}}{{/each}}';
    const data = { sections: [] };
    const result = renderTemplate(template, data);
    expect(result).toBe('');
  });
});
