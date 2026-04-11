// notify.js — macOS 네이티브 알림
import { execFile } from 'child_process';

/**
 * macOS 알림 전송 (osascript 사용)
 */
export function notify({ title, message, sound = 'Glass' }) {
  // 이스케이프: osascript injection 방지
  const esc = (s) => String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  const script = `display notification "${esc(message)}" with title "${esc(title)}" sound name "${esc(sound)}"`;

  execFile('osascript', ['-e', script], (err) => {
    if (err) console.error('알림 전송 실패:', err.message);
  });
}

/**
 * Synapse 결과 알림
 */
export function notifySynapseResult(results) {
  const promotes = results.filter(r => r.classification?.action === 'slip_box_promote');
  const total = results.length;

  if (promotes.length > 0) {
    notify({
      title: 'Nightly Synapse 완료',
      message: `${total}개 노트 점검 → Slip-Box 승격 후보 ${promotes.length}개 발견. Inbox에서 리포트를 확인하세요.`,
      sound: 'Purr'
    });
  } else {
    notify({
      title: 'Nightly Synapse 완료',
      message: `${total}개 노트 점검 완료. 승격 후보 없음.`,
      sound: 'Glass'
    });
  }
}
