import { describe, it, expect } from 'vitest';
import { validate } from '../build/validator.js';

const makeSkill = (id) => ({ id, description: `${id} desc`, section: 'test' });
const makeAgent = (overrides = {}) => ({
  id: 'test-agent',
  description: 'test',
  transform: { claude: 'agent' },
  skills: [],
  ...overrides,
});

describe('tools validation', () => {
  it('rejects unknown tool names', () => {
    const agents = [makeAgent({ tools: ['Read', 'FakeTool'] })];
    const errors = validate([], agents);
    expect(errors).toContainEqual(
      expect.objectContaining({ type: 'INVALID_TOOL', target: 'test-agent' })
    );
  });

  it('accepts valid tool names', () => {
    const agents = [makeAgent({ tools: ['Read', 'Glob', 'Grep', 'Bash'] })];
    const errors = validate([], agents);
    const toolErrors = errors.filter(e => e.type === 'INVALID_TOOL');
    expect(toolErrors).toHaveLength(0);
  });

  it('accepts Bash pattern syntax', () => {
    const agents = [makeAgent({ tools: ['Read', 'Bash(git *)', 'Bash(gh *)'] })];
    const errors = validate([], agents);
    const toolErrors = errors.filter(e => e.type === 'INVALID_TOOL');
    expect(toolErrors).toHaveLength(0);
  });

  it('accepts agents without tools field', () => {
    const agents = [makeAgent()];
    const errors = validate([], agents);
    const toolErrors = errors.filter(e => e.type === 'INVALID_TOOL');
    expect(toolErrors).toHaveLength(0);
  });

  it('rejects non-array tools field', () => {
    const agents = [makeAgent({ tools: 'Read' })];
    const errors = validate([], agents);
    expect(errors).toContainEqual(
      expect.objectContaining({ type: 'INVALID_TOOLS_FORMAT', target: 'test-agent' })
    );
  });
});
