// detector.js — 오늘 수정된 .md 파일 감지
import fs from 'fs';
import path from 'path';

const IGNORE_DIRS = new Set([
  '.obsidian', '.smart-env', '.trash', '.git', '.claude',
  'scripts', 'Attachments', '4. Archives',
  '콘텐츠_소스', '(archive)'
]);

const IGNORE_FILES = new Set([
  'CLAUDE.md', 'Claude_Project_Instruction.md',
  'Obsidian_Knowledge_Base.txt'
]);

/**
 * 볼트 전체를 재귀 탐색하여 오늘 수정된 .md 파일만 반환
 */
export function getTodayModifiedNotes(vaultDir) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const results = [];
  walkDir(vaultDir, vaultDir, today, results);
  return results;
}

function walkDir(baseDir, currentDir, since, results) {
  let entries;
  try {
    entries = fs.readdirSync(currentDir, { withFileTypes: true });
  } catch { return; }

  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;

    const fullPath = path.join(currentDir, entry.name);
    const relativePath = path.relative(baseDir, fullPath);

    if (entry.isDirectory()) {
      const topDir = relativePath.split(path.sep)[0];
      if (IGNORE_DIRS.has(topDir)) continue;
      walkDir(baseDir, fullPath, since, results);
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      if (IGNORE_FILES.has(entry.name)) continue;

      try {
        const stat = fs.statSync(fullPath);
        if (stat.mtime >= since) {
          results.push({
            file: entry.name,
            filePath: fullPath,
            relativePath,
            mtime: stat.mtime,
            content: fs.readFileSync(fullPath, 'utf-8')
          });
        }
      } catch { continue; }
    }
  }
}

/**
 * 기존 Slip-Box 노트 목록을 수집 (연결 참고용)
 */
export function getExistingSlipBoxNotes(vaultDir) {
  const slipBoxDir = path.join(vaultDir, '0. Slip-Box');
  const notes = [];
  walkSlipBox(slipBoxDir, notes);
  return notes;
}

function walkSlipBox(dir, notes) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walkSlipBox(fullPath, notes);
    } else if (entry.name.endsWith('.md')) {
      notes.push(entry.name.replace('.md', ''));
    }
  }
}
