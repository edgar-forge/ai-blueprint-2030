import { spawnSync } from "node:child_process";

/**
 * Safely extracts integer counts from results array.
 * Prevents LLM injection by computing counts directly
 * rather than interpolating user-controlled strings.
 */
const computeCounts = (results) => {
  if (!Array.isArray(results)) {
    return { total: 0, success: 0, errors: 0 };
  }

  const total = results.length;
  const errors = results.filter((r) => r != null && typeof r.error === "string").length;
  const success = total - errors;

  return { total, success, errors };
};

/**
 * Sends a macOS notification via osascript.
 * All dynamic values are computed internally (safe counts only).
 */
export const sendNotification = (results, reportPath = "") => {
  const { total, success, errors } = computeCounts(results);

  const title = "Nightly Synapse 완료";
  const message = `${total}개 노트 분석 완료 (성공: ${success}, 오류: ${errors})`;

  const subtitle = reportPath
    ? "리포트가 Inbox에 저장되었습니다"
    : "";

  const script = [
    `display notification "${message}"`,
    `with title "${title}"`,
    subtitle ? `subtitle "${subtitle}"` : "",
    `sound name "Glass"`,
  ].filter(Boolean).join(" ");

  const result = spawnSync("osascript", ["-e", script], {
    encoding: "utf-8",
    timeout: 10_000,
  });

  if (result.error) {
    console.error(`[notify] Notification failed: ${result.error.message}`);
    return false;
  }

  if (result.status !== 0) {
    console.error(`[notify] osascript error: ${(result.stderr || "").slice(0, 200)}`);
    return false;
  }

  console.log("[notify] macOS notification sent.");
  return true;
};
