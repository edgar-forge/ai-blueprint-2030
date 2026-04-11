// synapse.js — 핵심 로직: 감지 → 분류 → 리포트
import { getTodayModifiedNotes, getExistingSlipBoxNotes } from './detector.js';
import { classifyNote } from './classifier.js';
import { generateAndSaveReport } from './report.js';
import { notifySynapseResult } from './notify.js';

const VAULT_DIR = process.env.VAULT_DIR
  || '/path/to/your/obsidian-vault';

// ─── 상수 ───
const MAX_TOTAL_MS = 10 * 60 * 1000;  // 전체 시간 제한 10분
const MAX_CONSECUTIVE_FAILURES = 3;    // 연속 실패 허용 횟수

export async function runNightlySynapse() {
  console.log('오늘 수정된 노트 탐색 중...');

  const todayNotes = getTodayModifiedNotes(VAULT_DIR);
  if (todayNotes.length === 0) {
    console.log('오늘 수정된 노트 없음. 종료.');
    return;
  }
  console.log(`${todayNotes.length}개 노트 발견:`);
  todayNotes.forEach(n => console.log(`  - ${n.relativePath}`));

  const existingNotes = getExistingSlipBoxNotes(VAULT_DIR);
  console.log(`기존 Slip-Box 노트: ${existingNotes.length}개`);

  const startTime = Date.now();
  let consecutiveFailures = 0;

  const results = [];
  for (const note of todayNotes) {
    if (Date.now() - startTime > MAX_TOTAL_MS) {
      console.log('전체 시간 제한(10분) 초과 — 중단');
      break;
    }
    console.log(`분류 중: ${note.relativePath}`);
    try {
      const classification = await classifyNote(note, existingNotes, VAULT_DIR);
      results.push({ note: note.file, relativePath: note.relativePath, classification });
      consecutiveFailures = 0;
    } catch (err) {
      console.error(`  분류 실패: ${err.message}`);
      results.push({
        note: note.file,
        relativePath: note.relativePath,
        classification: { error: err.message }
      });
      consecutiveFailures++;
      if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
        console.log(`연속 ${MAX_CONSECUTIVE_FAILURES}회 실패 — 중단`);
        break;
      }
    }
  }

  // 4. 리포트 생성
  const reportPath = generateAndSaveReport(results, VAULT_DIR);
  console.log(`리포트 저장 완료: ${reportPath}`);

  // 5. 결과 요약
  const promotes = results.filter(r => r.classification?.action === 'slip_box_promote');
  console.log(`\n=== 결과 요약 ===`);
  console.log(`총 처리: ${results.length}개`);
  console.log(`Slip-Box 승격 후보: ${promotes.length}개`);
  console.log(`리포트: ${reportPath}`);

  // 6. macOS 알림
  notifySynapseResult(results);

  return { results, reportPath };
}
