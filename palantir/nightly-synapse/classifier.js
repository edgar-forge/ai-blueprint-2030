// classifier.js — Claude CLI로 Slip-Box 분류 판정 (별도 API 키 불필요)
import fs from 'fs';
import path from 'path';

// ─── 상수 ───
const MAX_CONTENT_CHARS = 8000;  // 분류 시 노트 본문 최대 길이
const MAX_BUFFER_BYTES = 1024 * 1024;
const CLASSIFY_TIMEOUT_MS = 60_000;

/**
 * Ground Truth 문서를 읽어서 분류 프롬프트의 기준으로 사용
 */
function loadGroundTruth(vaultDir) {
  const gtPath = path.join(
    vaultDir,
    '2. Area of Responsibility/AI 설정/AI_세컨드브레인_Ground_Truth.md'
  );
  if (fs.existsSync(gtPath)) {
    return fs.readFileSync(gtPath, 'utf-8');
  }
  return '';
}

/**
 * 단일 노트를 분류 — claude CLI의 -p (print) 모드 사용
 */
export async function classifyNote(note, existingSlipBoxNotes, vaultDir) {
  const groundTruth = loadGroundTruth(vaultDir);

  const prompt = `당신은 성원의 옵시디언 Zettelkasten/Slip-Box 분류 전문가입니다.
아래의 Ground Truth 문서를 기준으로 노트를 분석하세요.

## Ground Truth (절대 기준)
${groundTruth}

## 분석할 노트
- 파일명: ${note.file}
- 위치: ${note.relativePath}
- 내용:
${note.content.slice(0, MAX_CONTENT_CHARS)}

## 기존 Slip-Box 영구노트 목록 (연결 참고용)
${existingSlipBoxNotes.join('\n')}

## 작업 지침
1. PARA 분류 기준(A-1)에 따라 이 노트의 타입을 판정하세요.
2. Slip-Box 승격 후보라면:
   - 루만 넘버링(기존 번호 체계 참고)
   - 하위 폴더(Biz/Mission/철학)
   - PKM 태그(PKM/Biz, PKM/Mission, PKM/Learning 중 1개)
   - 연결할 기존 영구노트 (최소 2개)
   - 브릿지 키워드 (B-1 테이블에서 3~5개, 6개 이상 금지)
   를 제안하세요.
3. 승격이 아니라면 현재 위치가 적절한지, 다른 곳으로 이동해야 하는지 판단하세요.

## 응답 형식 (JSON만 출력, 마크다운 코드블록 없이)
{
  "type": "permanent | fleeting | project | reference | area",
  "reason": "분류 이유 한 줄",
  "action": "slip_box_promote | keep | move | merge",
  "current_location_ok": true,
  "suggested_move_to": "이동 제안 경로 (move일 때만)",
  "slip_box": {
    "suggested_name": "B1I — 핵심 아이디어 한 문장.md",
    "subfolder": "Biz/B1_콘텐츠 전략",
    "luhmann": "B1I",
    "pkm_tag": "PKM/Biz",
    "connections": ["기존 노트명1", "기존 노트명2"],
    "bridge_keywords": ["[[키워드1]]", "[[키워드2]]", "[[키워드3]]"],
    "rewritten_content": "성원의 언어로 다시 쓴 영구노트 내용 (원자성 유지, 200자 이내)"
  },
  "summary": "핵심 내용 2줄 요약"
}

slip_box 필드는 type이 "permanent"이고 action이 "slip_box_promote"일 때만 포함하세요.
`;

  const { spawnSync } = await import('child_process');
  const result = spawnSync('claude', ['-p', '--output-format', 'text'], {
    input: prompt,
    maxBuffer: MAX_BUFFER_BYTES,
    timeout: CLASSIFY_TIMEOUT_MS,
    env: { ...process.env, PATH: process.env.PATH },
    encoding: 'utf-8'
  });

  if (result.error) throw result.error;
  const stdout = result.stdout;

  const text = stdout.trim();

  try {
    // JSON 블록이 ```json ... ``` 형태로 올 수도 있으므로 처리
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return JSON.parse(text);
  } catch {
    return { error: 'JSON 파싱 실패', raw: text };
  }
}
