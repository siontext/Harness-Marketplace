import matter from 'gray-matter';
import { glob } from 'glob';
import fs from 'fs/promises';
import path from 'path';

const ALL_PLATFORMS = ['claude', 'gemini', 'codex'];

export function parseDenyRulesTable(content) {
  const lines = content.split('\n');
  const patterns = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith('|') || trimmed.startsWith('| 패턴') || trimmed.startsWith('|---')) {
      continue;
    }
    const cells = trimmed.split('|').map(c => c.trim()).filter(Boolean);
    if (cells.length >= 2) {
      patterns.push({ pattern: cells[0], description: cells[1] });
    }
  }

  return patterns;
}

async function parseMarkdownFiles(dir) {
  const pattern = path.join(dir, '**/*.md').replace(/\\/g, '/');
  const files = await glob(pattern);
  const results = [];

  for (const file of files) {
    const raw = await fs.readFile(file, 'utf-8');
    const { data, content } = matter(raw);
    results.push({ ...data, content: content.trim(), _file: file });
  }

  return results;
}

export async function parseRules(rulesDir) {
  const items = await parseMarkdownFiles(rulesDir);

  return items.map(item => {
    const rule = {
      id: item.id,
      description: item.description,
      platforms: item.platforms || ALL_PLATFORMS,
      section: item.section,
      order: item.order ?? null,
      type: item.type || null,
      content: item.content,
      _file: item._file,
    };

    if (rule.type === 'deny-rules') {
      rule.denyPatterns = parseDenyRulesTable(rule.content);
    }

    return rule;
  });
}

export async function parseRoles(rolesDir) {
  const items = await parseMarkdownFiles(rolesDir);

  return items.map(item => ({
    id: item.id,
    description: item.description,
    platforms: item.platforms || ALL_PLATFORMS,
    transform: item.transform,
    rules: item.rules || [],
    content: item.content,
    _file: item._file,
  }));
}
