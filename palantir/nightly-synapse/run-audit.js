// run-audit.js — 감사 에이전트 즉시 실행
import { runAudit } from './auditor.js';

// 무한루프 방지: 15분 후 강제 종료
const HARD_KILL_MS = 15 * 60 * 1000;
const killTimer = setTimeout(() => {
  console.error('⚠️ 15분 경과 — 강제 종료 (무한루프 방지)');
  process.exit(1);
}, HARD_KILL_MS);

runAudit()
  .then(() => {
    clearTimeout(killTimer);
    console.log('\n감사 완료.');
  })
  .catch(err => {
    clearTimeout(killTimer);
    console.error('감사 실패:', err);
    process.exit(1);
  });
