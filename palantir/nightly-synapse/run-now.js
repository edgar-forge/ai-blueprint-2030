import { runSynapse } from "./synapse.js";

console.log("[run-now] 수동 실행 시작...");

const result = await runSynapse();

if (result.success) {
  console.log("[run-now] 완료.");
  if (result.reportPath) {
    console.log(`[run-now] 리포트: ${result.reportPath}`);
  } else {
    console.log("[run-now] 오늘 수정된 노트 없음.");
  }
} else {
  console.error(`[run-now] 실패: ${result.error}`);
  process.exit(1);
}
