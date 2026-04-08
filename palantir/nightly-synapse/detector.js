import fs from "node:fs";
import path from "node:path";

const IGNORE_DIRS = new Set([
  ".obsidian",
  ".smart-env",
  ".trash",
  ".git",
  ".claude",
  "scripts",
  "Attachments",
  "4. Archives",
]);

const IGNORE_FILES = new Set([
  "CLAUDE.md",
  "Claude_Project_Instruction.md",
]);

/**
 * Returns the start-of-today timestamp (local time, midnight).
 */
const getTodayStart = () => {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
};

/**
 * Recursively walks a directory, collecting .md file paths
 * while respecting IGNORE_DIRS and IGNORE_FILES.
 */
const walkDir = (dir, collected = []) => {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (err) {
    console.error(`[detector] Cannot read directory: ${dir} — ${err.message}`);
    return collected;
  }

  for (const entry of entries) {
    const entryName = entry.name;

    if (entry.isDirectory()) {
      if (IGNORE_DIRS.has(entryName)) continue;
      walkDir(path.join(dir, entryName), collected);
      continue;
    }

    if (!entryName.endsWith(".md")) continue;
    if (IGNORE_FILES.has(entryName)) continue;

    collected.push(path.join(dir, entryName));
  }

  return collected;
};

/**
 * Scans the vault for .md files modified today.
 * Returns an array of { filePath, fileName, mtime } objects.
 */
export const getTodayModifiedNotes = (vaultDir) => {
  const todayStart = getTodayStart();
  const allMdFiles = walkDir(vaultDir);

  const modified = [];
  for (const filePath of allMdFiles) {
    try {
      const stat = fs.statSync(filePath);
      if (stat.mtimeMs >= todayStart) {
        modified.push({
          filePath,
          fileName: path.basename(filePath, ".md"),
          mtime: stat.mtime.toISOString(),
        });
      }
    } catch (err) {
      console.error(`[detector] Cannot stat file: ${filePath} — ${err.message}`);
    }
  }

  console.log(`[detector] Found ${modified.length} note(s) modified today.`);
  return modified;
};

/**
 * Returns a Set of existing Slip-Box note file names (without extension)
 * for link-validation purposes.
 */
export const getExistingSlipBoxNotes = (vaultDir) => {
  const slipBoxDir = path.join(vaultDir, "0. Slip-Box");
  if (!fs.existsSync(slipBoxDir)) {
    console.warn(`[detector] Slip-Box directory not found: ${slipBoxDir}`);
    return new Set();
  }

  const files = walkDir(slipBoxDir);
  const noteNames = new Set(
    files.map((f) => path.basename(f, ".md"))
  );

  console.log(`[detector] ${noteNames.size} existing Slip-Box note(s) indexed.`);
  return noteNames;
};
