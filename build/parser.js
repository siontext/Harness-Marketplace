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
    // 표 양끝의 '|'가 만드는 빈 칸만 걷어낸다. 중간의 빈 칸은 위치가 의미를
    // 가지므로(예: 비어 있는 '예외' 열) 남겨 둔다.
    const cells = trimmed.split('|').map(c => c.trim()).slice(1, -1);
    if (cells.length >= 2 && cells[0]) {
      patterns.push({
        pattern: cells[0],
        description: cells[1],
        alternative: cells[2] || null,
        exceptions: cells[3] ? cells[3].split(',').map(e => e.trim()).filter(Boolean) : [],
      });
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

export async function parseSkills(skillsDir) {
  const items = await parseMarkdownFiles(skillsDir);

  return items.map(item => {
    const skill = {
      id: item.id,
      description: item.description,
      platforms: item.platforms || ALL_PLATFORMS,
      section: item.section,
      order: item.order ?? null,
      type: item.type || null,
      content: item.content,
      _file: item._file,
    };

    if (skill.type === 'deny-rules') {
      skill.denyPatterns = parseDenyRulesTable(skill.content);
    }

    return skill;
  });
}

export async function parseAgents(agentsDir) {
  const items = await parseMarkdownFiles(agentsDir);

  return items.map(item => ({
    id: item.id,
    description: item.description,
    platforms: item.platforms || ALL_PLATFORMS,
    transform: item.transform,
    skills: item.rules || item.skills || [],
    tools: item.tools || null,
    content: item.content,
    _file: item._file,
  }));
}
