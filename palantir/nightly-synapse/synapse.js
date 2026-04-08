import { getTodayModifiedNotes } from "./detector.js";
import { classifyNotes } from "./classifier.js";
import { generateReport } from "./report.js";
import { sendNotification } from "./notify.js";

const TOTAL_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_CONSECUTIVE_FAILURES = 3;

const DEFAULT_VAULT_DIR = process.env.VAULT_DIR || "{VAULT_PATH}";

/**
 * Runs the full Nightly Synapse pipeline:
 * detect -> classify -> report -> notify.
 *
 * Returns { success, reportPath, results, error }.
 */
export const runSynapse = async (options = {}) => {
  const {
    vaultDir = DEFAULT_VAULT_DIR,
    groundTruthPath,
  } = options;

  const startTime = Date.now();

  const checkTimeout = () => {
    if (Date.now() - startTime > TOTAL_TIMEOUT_MS) {
      throw new Error("Synapse 총 실행 시간 초과 (10분)");
    }
  };

  console.log("=".repeat(50));
  console.log("[synapse] Nightly Synapse 시작");
  console.log(`[synapse] Vault: ${vaultDir}`);
  console.log(`[synapse] 시작 시각: ${new Date().toISOString()}`);
  console.log("=".repeat(50));

  try {
    // Step 1: Detect today's modified notes
    checkTimeout();
    const modifiedNotes = getTodayModifiedNotes(vaultDir);

    if (modifiedNotes.length === 0) {
      console.log("[synapse] 오늘 수정된 노트가 없습니다. 종료합니다.");
      sendNotification([], "");
      return { success: true, reportPath: null, results: [], error: null };
    }

    console.log(`[synapse] ${modifiedNotes.length}개 노트 분류 시작...`);

    // Step 2: Classify notes with consecutive failure tracking
    checkTimeout();
    const results = [];
    let consecutiveFailures = 0;

    for (const note of modifiedNotes) {
      checkTimeout();

      const classifierOptions = groundTruthPath ? { groundTruthPath } : {};
      const [result] = classifyNotes([note], classifierOptions);
      results.push(result);

      if (result.error) {
        consecutiveFailures += 1;
        console.warn(
          `[synapse] 연속 실패 ${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES}: ${result.fileName}`
        );

        if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
          const msg = `연속 ${MAX_CONSECUTIVE_FAILURES}회 실패로 중단합니다.`;
          console.error(`[synapse] ${msg}`);

          const reportPath = generateReport(vaultDir, results);
          sendNotification(results, reportPath);

          return { success: false, reportPath, results, error: msg };
        }
      } else {
        consecutiveFailures = 0;
      }
    }

    // Step 3: Generate report
    checkTimeout();
    const reportPath = generateReport(vaultDir, results);

    // Step 4: Send notification
    sendNotification(results, reportPath);

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[synapse] 완료. 소요 시간: ${elapsed}초`);

    return { success: true, reportPath, results, error: null };
  } catch (err) {
    console.error(`[synapse] 치명적 오류: ${err.message}`);
    sendNotification([], "");
    return { success: false, reportPath: null, results: [], error: err.message };
  }
};
