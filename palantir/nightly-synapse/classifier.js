import fs from "node:fs";
import { spawnSync } from "node:child_process";

const DEFAULT_GROUND_TRUTH_PATH =
  "{VAULT_PATH}/2. Area of Responsibility/AI 설정/AI_세컨드브레인_Ground_Truth.md";

const TIMEOUT_MS = 120_000;

/**
 * Loads Ground Truth markdown content from disk.
 */
const loadGroundTruth = (groundTruthPath = DEFAULT_GROUND_TRUTH_PATH) => {
  try {
    return fs.readFileSync(groundTruthPath, "utf-8");
  } catch (err) {
    console.error(`[classifier] Failed to load Ground Truth: ${err.message}`);
    return null;
  }
};

/**
 * Strips markdown code-block fences (```json ... ```) from a string.
 */
const stripCodeBlocks = (raw) => {
  const trimmed = raw.trim();
  const fencePattern = /^```(?:json)?\s*\n?([\s\S]*?)\n?\s*```$/;
  const match = trimmed.match(fencePattern);
  return match ? match[1].trim() : trimmed;
};

/**
 * Builds the classification prompt for a single note.
 */
const buildPrompt = (note, groundTruth) => `
당신은 옵시디언 볼트의 노트 분류 전문가입니다.
아래 Ground Truth 규칙에 따라 노트를 분석하고 JSON으로 응답하세요.

## Ground Truth
${groundTruth}

## 분류 대상 노트
- 파일명: ${note.fileName}
- 경로: ${note.filePath}
- 수정시각: ${note.mtime}
- 내용:
${note.content}

## 응답 형식 (JSON만 출력)
{
  "fileName": "${note.fileName}",
  "currentPath": "${note.filePath}",
  "suggestedFolder": "PARA 분류 결과 (0. Slip-Box | 1. Projects | 2. AoR | 3. Resources | 4. Archives)",
  "reason": "분류 근거 1~2문장",
  "bridgeKeywords": ["연결 가능한 브릿지 키워드 최대 5개"],
  "issues": ["발견된 문제점 (프론트매터 누락, 링크 깨짐 등)"],
  "confidence": 0.0
}
`.trim();

/**
 * Classifies a single note by calling `claude -p` via stdin.
 * Returns the parsed JSON result or null on failure.
 */
export const classifyNote = (note, options = {}) => {
  const {
    groundTruthPath = DEFAULT_GROUND_TRUTH_PATH,
  } = options;

  const groundTruth = loadGroundTruth(groundTruthPath);
  if (!groundTruth) {
    return { fileName: note.fileName, error: "Ground Truth 로드 실패" };
  }

  let content;
  try {
    content = fs.readFileSync(note.filePath, "utf-8");
  } catch (err) {
    return { fileName: note.fileName, error: `파일 읽기 실패: ${err.message}` };
  }

  const noteWithContent = { ...note, content };
  const prompt = buildPrompt(noteWithContent, groundTruth);

  const result = spawnSync("claude", ["-p"], {
    input: prompt,
    encoding: "utf-8",
    timeout: TIMEOUT_MS,
    maxBuffer: 10 * 1024 * 1024,
  });

  if (result.error) {
    const msg = result.error.code === "ETIMEDOUT"
      ? "분류 타임아웃 (120초 초과)"
      : `프로세스 오류: ${result.error.message}`;
    return { fileName: note.fileName, error: msg };
  }

  if (result.status !== 0) {
    return {
      fileName: note.fileName,
      error: `claude CLI 종료 코드 ${result.status}: ${(result.stderr || "").slice(0, 200)}`,
    };
  }

  const rawOutput = (result.stdout || "").trim();
  if (!rawOutput) {
    return { fileName: note.fileName, error: "claude CLI 빈 응답" };
  }

  try {
    const cleaned = stripCodeBlocks(rawOutput);
    return JSON.parse(cleaned);
  } catch (err) {
    return {
      fileName: note.fileName,
      error: `JSON 파싱 실패: ${err.message}`,
      rawOutput: rawOutput.slice(0, 500),
    };
  }
};

/**
 * Classifies an array of notes sequentially.
 * Returns an array of classification results.
 */
export const classifyNotes = (notes, options = {}) => {
  const results = [];
  for (const note of notes) {
    console.log(`[classifier] Classifying: ${note.fileName}`);
    const result = classifyNote(note, options);
    results.push(result);
  }
  return results;
};
