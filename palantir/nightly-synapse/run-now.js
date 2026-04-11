// run-now.js — 즉시 실행용 (테스트 & 수동 실행)
import { runNightlySynapse } from './synapse.js';

// 무한루프 방지: 15분 후 강제 종료
const HARD_KILL_MS = 15 * 60 * 1000;
const killTimer = setTimeout(() => {
  console.error('⚠️ 15분 경과 — 강제 종료 (무한루프 방지)');
  process.exit(1);
}, HARD_KILL_MS);

runNightlySynapse()
  .then(() => {
    clearTimeout(killTimer);
    console.log('\n완료.');
  })
  .catch(err => {
    clearTimeout(killTimer);
    console.error('실행 실패:', err);
    process.exit(1);
  });
