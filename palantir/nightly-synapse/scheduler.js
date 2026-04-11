// scheduler.js — 매일 저녁 22시 Synapse + 22:30 Audit
import cron from 'node-cron';
import { runNightlySynapse } from './synapse.js';
import { runAudit } from './auditor.js';

// 22:00 — Nightly Synapse (노트 분류)
cron.schedule('0 22 * * *', () => {
  console.log(`[${new Date().toISOString()}] Nightly Synapse 시작`);
  runNightlySynapse().catch(err => {
    console.error('Nightly Synapse 실패:', err);
  });
}, {
  timezone: 'Asia/Seoul'
});

// 22:30 — Daily Audit (교차검증)
cron.schedule('30 22 * * *', () => {
  console.log(`[${new Date().toISOString()}] Daily Audit 시작`);
  runAudit().catch(err => {
    console.error('Daily Audit 실패:', err);
  });
}, {
  timezone: 'Asia/Seoul'
});

console.log('스케줄러 시작 — 22:00 Synapse / 22:30 Audit (KST)');
