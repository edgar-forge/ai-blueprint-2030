// auditor.js — Claude 작업 교차검증 에이전트
// Nightly Synapse 리포트 + git diff + 세션 로그를 종합하여 감사 리포트 생성
import fs from 'fs';
import path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

const VAULT_DIR = process.env.VAULT_DIR
  || '/path/to/your/obsidian-vault';
const LOG_DIR = path.join(process.env.HOME, '.claude/session-logs');

// ─── 상수 ───
const MAX_LOG_ENTRIES = 50;
const MAX_GIT_FILES = 50;
const MAX_BUFFER_BYTES = 1024 * 1024;
const GIT_DIFF_MAX_CHARS = 2000;
const SLIP_BOX_REQUIRED_FIELDS = ['tags', 'created', 'source', 'luhmann'];
const MAX_BRIDGE_KEYWORDS = 5;
const MAX_NOTE_LENGTH = 3000;
const ATOMICITY_EXCEPTIONS = [
  'M1A — AI 시대의 구조',
  'P2A — 사피엔스의'
];
const LLM_TIMEOUT_MS = 60_000;

/**
 * 1. 오늘의 세션 로그 읽기
 */
function getTodaySessionLog() {
  const today = new Date().toISOString().split('T')[0];
  const logPath = path.join(LOG_DIR, `${today}.jsonl`);
  if (!fs.existsSync(logPath)) return [];

  return fs.readFileSync(logPath, 'utf-8')
    .split('\n')
    .filter(line => line.trim())
    .map(line => {
      try { return JSON.parse(line); } catch { return null; }
    })
    .filter(Boolean);
}

/**
 * 2. git diff로 오늘 변경 내용 가져오기
 */
async function getGitDiff() {
  try {
    const today = new Date().toISOString().split('T')[0];
    const { stdout } = await execFileAsync('git', [
      'log', '--since', `${today}T00:00:00`, '--name-only', '--oneline'
    ], { cwd: VAULT_DIR, maxBuffer: MAX_BUFFER_BYTES });

    if (stdout.trim()) {
      const lines = stdout.trim().split('\n');
      const mdFiles = lines.filter(l => l.endsWith('.md')).slice(0, MAX_GIT_FILES);
      const commitCount = lines.filter(l => !l.includes('/')).length;
      return `커밋 수: ${commitCount}개\n변경된 .md 파일 (최대 ${MAX_GIT_FILES}개):\n${mdFiles.join('\n')}`;
    }

    const { stdout: diffOut } = await execFileAsync('git', [
      'diff', '--name-only'
    ], { cwd: VAULT_DIR, maxBuffer: MAX_BUFFER_BYTES });
    return diffOut.trim().slice(0, GIT_DIFF_MAX_CHARS) || '오늘 변경 없음';
  } catch {
    return 'git 사용 불가';
  }
}

function collectAllNoteNames(dir, nameSet) {
  if (!fs.existsSync(dir)) return;
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name.startsWith('.')) continue;
      collectAllNoteNames(fullPath, nameSet);
    } else if (entry.name.endsWith('.md')) {
      nameSet.add(entry.name.replace(/\.md$/, ''));
    }
  }
}

/**
 * 3. 규칙 기반 자동 검증 (기계적 체크)
 */
function runRuleChecks() {
  const issues = [];
  const slipBoxDir = path.join(VAULT_DIR, '0. Slip-Box');
  const allNoteNames = new Set();
  collectAllNoteNames(VAULT_DIR, allNoteNames);

  checkSlipBoxNotes(slipBoxDir, VAULT_DIR, issues, allNoteNames);
  checkSynapseReport(issues);

  return issues;
}

function checkSynapseReport(issues) {
  const today = new Date().toISOString().split('T')[0];
  const reportPath = path.join(VAULT_DIR, 'Inbox', `Nightly-Synapse_${today}.md`);
  if (!fs.existsSync(reportPath)) {
    issues.push({
      severity: 'warning',
      category: 'synapse',
      message: `오늘의 Nightly Synapse 리포트가 없습니다: ${reportPath}`
    });
  }
}

function checkSlipBoxNotes(dir, vaultDir, issues, allNoteNames) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      checkSlipBoxNotes(fullPath, vaultDir, issues, allNoteNames);
      continue;
    }
    if (!entry.name.endsWith('.md')) continue;

    const content = fs.readFileSync(fullPath, 'utf-8');
    const relativePath = path.relative(vaultDir, fullPath);

    checkFrontmatter(content, relativePath, issues);
    checkBridgeKeywords(content, relativePath, issues);
    checkBrokenLinks(content, relativePath, allNoteNames, issues);
    checkAtomicity(content, relativePath, issues);
  }
}

function checkFrontmatter(content, relativePath, issues) {
  if (!content.startsWith('---')) {
    issues.push({
      severity: 'error',
      category: 'slip-box-format',
      message: `프론트매터 없음: ${relativePath}`
    });
    return;
  }

  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) return;

  const fm = fmMatch[1];
  for (const field of SLIP_BOX_REQUIRED_FIELDS) {
    if (!fm.includes(`${field}:`)) {
      issues.push({
        severity: 'warning',
        category: 'slip-box-format',
        message: `프론트매터 필드 누락 (${field}): ${relativePath}`
      });
    }
  }
}

function checkBridgeKeywords(content, relativePath, issues) {
  const lines = content.split('\n');
  const lastLines = lines.slice(-5).join('\n');
  if (!lastLines.includes('브릿지 키워드:')) {
    issues.push({
      severity: 'warning',
      category: 'slip-box-bridge',
      message: `브릿지 키워드 라인 없음: ${relativePath}`
    });
  }

  const bridgeLine = lines.find(l => l.includes('브릿지 키워드:'));
  if (!bridgeLine) return;

  const kwCount = (bridgeLine.match(/\[\[/g) || []).length;
  if (kwCount > MAX_BRIDGE_KEYWORDS) {
    issues.push({
      severity: 'error',
      category: 'slip-box-bridge',
      message: `브릿지 키워드 ${kwCount}개 (최대 ${MAX_BRIDGE_KEYWORDS}개): ${relativePath}`
    });
  }
}

function checkBrokenLinks(content, relativePath, allNoteNames, issues) {
  const links = content.match(/\[\[([^\]|]+?)(\|[^\]]+?)?\]\]/g) || [];
  for (const link of links) {
    const noteName = link.replace(/\[\[/, '').replace(/(\|[^\]]+?)?\]\]/, '');
    if (noteName.includes('_') && !noteName.includes(' ')) continue;
    if (noteName.startsWith('프로젝트_')) continue;
    if (!allNoteNames.has(noteName)) {
      issues.push({
        severity: 'warning',
        category: 'slip-box-broken-link',
        message: `깨진 링크 [[${noteName}]]: ${relativePath}`
      });
    }
  }
}

function checkAtomicity(content, relativePath, issues) {
  const isException = ATOMICITY_EXCEPTIONS.some(ex => relativePath.includes(ex));
  if (content.length > MAX_NOTE_LENGTH && !isException) {
    issues.push({
      severity: 'info',
      category: 'slip-box-atomicity',
      message: `노트 길이 ${content.length}자 (원자성 점검 필요): ${relativePath}`
    });
  }
}

/**
 * 4. Claude CLI로 LLM 교차 리뷰
 */
async function runLLMReview(sessionLog, gitDiff, ruleIssues) {
  const logSummary = sessionLog.length > 0
    ? sessionLog.slice(-MAX_LOG_ENTRIES).map(l => `[${l.tool}] ${l.input}`).join('\n')
    : '오늘 기록된 세션 로그 없음';

  const issuesSummary = ruleIssues.length > 0
    ? ruleIssues.map(i => `[${i.severity}] ${i.category}: ${i.message}`).join('\n')
    : '규칙 위반 없음';

  const prompt = buildLLMPrompt(logSummary, gitDiff, issuesSummary);

  try {
    const { spawnSync } = await import('child_process');
    const result = spawnSync('claude', ['-p', '--output-format', 'text'], {
      input: prompt,
      maxBuffer: MAX_BUFFER_BYTES,
      timeout: LLM_TIMEOUT_MS,
      env: { ...process.env, PATH: process.env.PATH },
      encoding: 'utf-8'
    });

    if (result.error) throw result.error;
    const text = result.stdout.trim();
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) return JSON.parse(jsonMatch[0]);
    console.error('JSON 파싱 실패. raw 응답 앞부분:', text.slice(0, 300));
    return { error: 'JSON 파싱 실패', raw: text.slice(0, 500) };
  } catch (err) {
    console.error('LLM 리뷰 에러:', err.message);
    return { error: `LLM 리뷰 실패: ${err.message}` };
  }
}

function buildLLMPrompt(logSummary, gitDiff, issuesSummary) {
  return `당신은 Obsidian 볼트의 "감사/리뷰어" 역할입니다.
아래 정보를 바탕으로 오늘 하루 동안 진행된 작업을 교차검증하세요.

## 역할
- 낮에 "작성자(Builder)" Claude가 작업한 결과를 **비판적으로** 검토
- 잘못된 것만 지적하지 말고, 잘된 것도 인정
- 사람(성원)이 봐야 할 핵심 포인트만 간결하게 정리

## 오늘 Claude 세션 로그 (최근 ${MAX_LOG_ENTRIES}건)
${logSummary}

## Git 변경 요약
${gitDiff}

## 자동 규칙 검증 결과
${issuesSummary}

## 검증 기준
1. Slip-Box 규칙: 프론트매터 4필드, 브릿지 키워드 3~5개, 원자성, 최소 2개 연결
2. PARA 분류: 폴더 위치가 내용과 맞는지
3. 볼트 오염 방지: 존재하지 않는 링크 생성, 자의적 확장, 구조 변경 등
4. 코드 품질: scripts/ 하위 코드에 명백한 버그나 보안 이슈가 있는지

## 응답 형식 (JSON, 마크다운 코드블록 없이)
{
  "overall_score": "A/B/C/D (A=우수, D=심각한 문제)",
  "summary": "한 줄 요약",
  "well_done": ["잘된 점 1", "잘된 점 2"],
  "issues": [
    {
      "severity": "critical/warning/info",
      "file": "파일 경로",
      "description": "문제 설명",
      "suggestion": "권장 조치"
    }
  ],
  "action_items": ["성원이 확인해야 할 것 1", "확인해야 할 것 2"]
}`;
}

/**
 * 5. 감사 리포트 생성
 */
function generateAuditReport(sessionLog, gitDiff, ruleIssues, llmReview) {
  const today = new Date().toISOString().split('T')[0];
  const criticals = ruleIssues.filter(i => i.severity === 'error');
  const warnings = ruleIssues.filter(i => i.severity === 'warning');
  const infos = ruleIssues.filter(i => i.severity === 'info');

  const ruleSection = formatRuleSection(criticals, warnings, infos, ruleIssues.length);
  const llmSection = formatLLMSection(llmReview);
  const activitySection = formatActivitySection(sessionLog, gitDiff);

  return `---
tags: [system/audit]
created: ${today}
---

# Daily Audit Report — ${today}

> Claude의 하루 작업을 교차검증한 감사 리포트입니다.

---

## 종합 평가

- **등급**: ${llmReview.overall_score || 'N/A'}
- **요약**: ${llmReview.summary || 'LLM 리뷰 미완료'}

---

## 잘된 점

${(llmReview.well_done || []).map(w => `- ${w}`).join('\n') || '_없음_'}

---

## 자동 규칙 검증 (${ruleIssues.length}건)

${ruleSection}

---

## LLM 교차 리뷰 이슈

${llmSection}

---

## 성원 확인 필요 사항

${(llmReview.action_items || []).map((a, i) => `${i + 1}. ${a}`).join('\n') || '_없음_'}

---

${activitySection}

---

_Generated by Audit Agent at ${new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}_
`;
}

function formatRuleSection(criticals, warnings, infos, totalCount) {
  if (totalCount === 0) return '_규칙 위반 없음_\n';

  let section = '';
  if (criticals.length > 0) {
    section += `### 오류 (${criticals.length}건)\n${criticals.map(i => `- **${i.category}**: ${i.message}`).join('\n')}\n\n`;
  }
  if (warnings.length > 0) {
    section += `### 경고 (${warnings.length}건)\n${warnings.map(i => `- **${i.category}**: ${i.message}`).join('\n')}\n\n`;
  }
  if (infos.length > 0) {
    section += `### 참고 (${infos.length}건) — 확인 불필요, 기록용\n<details>\n<summary>펼쳐보기</summary>\n\n${infos.map(i => `- **${i.category}**: ${i.message}`).join('\n')}\n</details>\n`;
  }
  return section;
}

function formatLLMSection(llmReview) {
  const issues = llmReview.issues || [];
  if (issues.length === 0) return '_이슈 없음_';

  return issues.map(i =>
    `- **[${i.severity}]** \`${i.file || '전체'}\`: ${i.description}\n  → ${i.suggestion}`
  ).join('\n\n');
}

function formatActivitySection(sessionLog, gitDiff) {
  const writeCount = sessionLog.filter(l => l.tool === 'Write').length;
  const editCount = sessionLog.filter(l => l.tool === 'Edit').length;
  const bashCount = sessionLog.filter(l => l.tool === 'Bash').length;

  return `## 오늘 Claude 활동 요약

- 세션 로그: ${sessionLog.length}건
- 도구 사용: Write ${writeCount}회, Edit ${editCount}회, Bash ${bashCount}회

### Git 변경
\`\`\`
${gitDiff}
\`\`\``;
}

/**
 * 메인 실행
 */
export async function runAudit() {
  console.log('감사 에이전트 시작...');

  const sessionLog = getTodaySessionLog();
  console.log(`세션 로그: ${sessionLog.length}건`);

  const gitDiff = await getGitDiff();
  console.log(`Git diff 수집 완료`);

  const ruleIssues = runRuleChecks();
  console.log(`규칙 검증: ${ruleIssues.length}건 발견`);

  console.log('LLM 교차 리뷰 중...');
  const llmReview = await runLLMReview(sessionLog, gitDiff, ruleIssues);
  console.log(`LLM 리뷰 완료: ${llmReview.overall_score || 'error'}`);

  const today = new Date().toISOString().split('T')[0];
  const reportContent = generateAuditReport(sessionLog, gitDiff, ruleIssues, llmReview);
  let reportPath = path.join(VAULT_DIR, 'Inbox', `Daily-Audit_${today}.md`);
  if (fs.existsSync(reportPath)) {
    let suffix = 1;
    do {
      reportPath = path.join(VAULT_DIR, 'Inbox', `Daily-Audit_${today}_${String(suffix).padStart(3, '0')}.md`);
      suffix++;
    } while (fs.existsSync(reportPath));
  }
  fs.writeFileSync(reportPath, reportContent, 'utf-8');
  console.log(`리포트 저장: ${reportPath}`);

  const { notify } = await import('./notify.js');
  const criticalCount = (llmReview.issues || []).filter(i => i.severity === 'critical').length
    + ruleIssues.filter(i => i.severity === 'error').length;
  notify({
    title: 'Daily Audit 완료',
    message: criticalCount > 0
      ? `주의: 심각한 이슈 ${criticalCount}건 발견. Inbox에서 확인하세요.`
      : `등급 ${llmReview.overall_score || '?'} — 이슈 없음.`,
    sound: criticalCount > 0 ? 'Basso' : 'Glass'
  });

  return { sessionLog, ruleIssues, llmReview, reportPath };
}
