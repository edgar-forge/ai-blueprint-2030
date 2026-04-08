import fs from "node:fs";
import path from "node:path";

/**
 * Formats a date as YYYY-MM-DD.
 */
const formatDate = (date = new Date()) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
};

/**
 * Builds a single note section for the report.
 */
const buildNoteSection = (result, index) => {
  if (result.error) {
    return [
      `### ${index + 1}. ${result.fileName || "Unknown"}`,
      `- **오류**: ${result.error}`,
      result.rawOutput ? `- **원본 응답** (일부): \`${result.rawOutput.slice(0, 200)}\`` : "",
    ].filter(Boolean).join("\n");
  }

  const issues = (result.issues && result.issues.length > 0)
    ? result.issues.map((issue) => `  - ${issue}`).join("\n")
    : "  - 없음";

  const keywords = (result.bridgeKeywords && result.bridgeKeywords.length > 0)
    ? result.bridgeKeywords.map((kw) => `[[${kw}]]`).join(" ")
    : "없음";

  return [
    `### ${index + 1}. ${result.fileName}`,
    `- **현재 경로**: \`${result.currentPath}\``,
    `- **추천 폴더**: ${result.suggestedFolder}`,
    `- **분류 근거**: ${result.reason}`,
    `- **신뢰도**: ${result.confidence}`,
    `- **브릿지 키워드**: ${keywords}`,
    `- **이슈**:`,
    issues,
  ].join("\n");
};

/**
 * Generates the full markdown report content.
 */
const buildReportContent = (results, dateStr) => {
  const successResults = results.filter((r) => !r.error);
  const errorResults = results.filter((r) => r.error);

  const header = [
    `# Nightly Synapse Report — ${dateStr}`,
    "",
    `> 자동 생성됨. 총 ${results.length}개 노트 분석 | 성공 ${successResults.length} | 실패 ${errorResults.length}`,
    "",
    "---",
    "",
  ].join("\n");

  const sections = results.map((r, i) => buildNoteSection(r, i)).join("\n\n");

  const summary = [
    "",
    "---",
    "",
    "## 요약",
    "",
    `| 항목 | 수 |`,
    `|------|---:|`,
    `| 분석 대상 | ${results.length} |`,
    `| 분류 성공 | ${successResults.length} |`,
    `| 오류 발생 | ${errorResults.length} |`,
    "",
  ].join("\n");

  return header + sections + summary;
};

/**
 * Writes the nightly synapse report to the Inbox folder.
 * Creates the Inbox directory if it does not exist.
 * Returns the full path of the generated report file.
 */
export const generateReport = (vaultDir, results) => {
  const dateStr = formatDate();
  const inboxDir = path.join(vaultDir, "Inbox");

  if (!fs.existsSync(inboxDir)) {
    fs.mkdirSync(inboxDir, { recursive: true });
    console.log(`[report] Created Inbox directory: ${inboxDir}`);
  }

  const reportFileName = `Nightly-Synapse_${dateStr}.md`;
  const reportPath = path.join(inboxDir, reportFileName);
  const content = buildReportContent(results, dateStr);

  fs.writeFileSync(reportPath, content, "utf-8");
  console.log(`[report] Report written: ${reportPath}`);

  return reportPath;
};
