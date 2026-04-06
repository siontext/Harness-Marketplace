import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

function expandHome(p) {
  if (p.startsWith('~/')) {
    return path.join(process.env.HOME || process.env.USERPROFILE, p.slice(2));
  }
  return p;
}

async function copyFile(src, dest) {
  await fs.mkdir(path.dirname(dest), { recursive: true });
  await fs.copyFile(src, dest);
  console.log(`  copy: ${src} -> ${dest}`);
}

async function mergeSettings(srcPath, destPath) {
  const srcContent = await fs.readFile(srcPath, 'utf-8');
  const srcSettings = JSON.parse(srcContent);

  let destSettings = {};
  try {
    const destContent = await fs.readFile(destPath, 'utf-8');
    destSettings = JSON.parse(destContent);
  } catch {
    // file doesn't exist — use empty object
  }

  // Only overwrite deny_rules, preserve everything else
  const merged = { ...destSettings, deny_rules: srcSettings.deny_rules };

  await fs.mkdir(path.dirname(destPath), { recursive: true });
  await fs.writeFile(destPath, JSON.stringify(merged, null, 2));
  console.log(`  merge: ${destPath} (deny_rules updated, personal settings preserved)`);
}

async function copyDir(srcDir, destDir) {
  await fs.mkdir(destDir, { recursive: true });
  const entries = await fs.readdir(srcDir, { withFileTypes: true });
  for (const entry of entries) {
    const src = path.join(srcDir, entry.name);
    const dest = path.join(destDir, entry.name);
    if (entry.isDirectory()) {
      await copyDir(src, dest);
    } else {
      await copyFile(src, dest);
    }
  }
}

async function syncPlatform(platform, config) {
  const targetDir = expandHome(config.target);
  const distDir = path.join(ROOT, 'dist', platform);

  console.log(`\n[${platform}] sync start -> ${targetDir}`);

  if (platform === 'gemini') {
    await copyFile(path.join(distDir, 'GEMINI.md'), path.join(targetDir, 'GEMINI.md'));
    await mergeSettings(path.join(distDir, 'settings.json'), path.join(targetDir, 'settings.json'));
  } else if (platform === 'codex') {
    await copyFile(path.join(distDir, 'AGENTS.md'), path.join(targetDir, 'AGENTS.md'));
    await mergeSettings(path.join(distDir, 'config.json'), path.join(targetDir, 'config.json'));
  }

  // Copy roles/ and rules/ for on-demand loading
  for (const subDir of ['roles', 'rules']) {
    const srcDir = path.join(distDir, subDir);
    try {
      await fs.access(srcDir);
      await copyDir(srcDir, path.join(targetDir, subDir));
    } catch {
      // dir doesn't exist — skip
    }
  }

  console.log(`[${platform}] sync complete`);
}

async function main() {
  const configPath = path.join(ROOT, 'harness.config.json');
  const config = JSON.parse(await fs.readFile(configPath, 'utf-8'));

  const args = process.argv.slice(2);
  const platformArg = args.find(a => a.startsWith('--platform'))?.split('=')[1]
    || (args.includes('--platform') ? args[args.indexOf('--platform') + 1] : null);
  const settingsOnly = args.includes('--settings-only');

  const platforms = platformArg ? [platformArg] : Object.keys(config.sync);

  for (const platform of platforms) {
    const platformConfig = config.sync[platform];
    if (!platformConfig) {
      console.error(`unknown platform: ${platform}`);
      continue;
    }

    if (settingsOnly) {
      const distDir = path.join(ROOT, 'dist', platform);
      const targetDir = expandHome(platformConfig.target);
      const settingsFile = platform === 'gemini' ? 'settings.json' : 'config.json';
      await mergeSettings(path.join(distDir, settingsFile), path.join(targetDir, settingsFile));
    } else {
      await syncPlatform(platform, platformConfig);
    }
  }
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});
