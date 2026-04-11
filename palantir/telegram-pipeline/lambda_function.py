"""
텔레그램 → Bedrock Claude → GitHub → Obsidian 파이프라인
AWS Lambda 핸들러

흐름:
1. 텔레그램 메시지 수신 (webhook)
2. Bedrock Claude로 PARA 분류 + 구조화
3. GitHub API로 볼트에 자동 커밋
"""

import json
import os
import re
import base64
import traceback
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

import boto3

from system_prompt import SYSTEM_PROMPT

# ─── 환경변수 ───
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ.get("GITHUB_REPO", "your-username/your-vault-repo")  # owner/repo
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514")
AWS_BEDROCK_REGION = os.environ.get("AWS_BEDROCK_REGION", "us-east-1")
LAMBDA_TIMEOUT = 90  # Opus는 깊게 사고하므로 90초
ALLOWED_CHAT_ID = int(os.environ.get("ALLOWED_CHAT_ID", "YOUR_CHAT_ID"))  # 성원만 사용 가능
DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "obsidian-pending-notes")

# ─── 상수 (매직 넘버 제거) ───
CONFIDENCE_THRESHOLD = 0.7  # 이 미만이면 Inbox로 강제 이동
MAX_BRIDGE_KEYWORDS = 5  # Ground Truth 규칙: 노트당 최대 5개
TELEGRAM_MSG_MAX_LEN = 4096  # 텔레그램 메시지 길이 제한
PREVIEW_BODY_MAX_LEN = 3000  # 미리보기 본문 최대 길이
TITLE_MAX_LEN = 80  # 파일명 최대 길이
MIN_CONTEXT_LINES = 3  # C-5 반려 기준: 이 이하 + 맥락 없음

# ─── 한국 시간 ───
KST = timezone(timedelta(hours=9))

# ─── 브릿지 키워드 사전 (Ground Truth B-1, B-2) ───
# ⚠️ 이 딕셔너리는 ~/obsidian-mcp-server/bridge_keywords.py와 동일해야 합니다.
# 한쪽을 수정하면 반드시 다른 쪽도 동기화하세요.
# SYSTEM_PROMPT는 system_prompt.py에서 import합니다.
from bridge_keywords import BRIDGE_KEYWORDS


# ─── AWS 클라이언트 (Lambda 콜드스타트 최적화) ───
bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=AWS_BEDROCK_REGION,
)
dynamodb = boto3.resource("dynamodb", region_name=AWS_BEDROCK_REGION)
pending_table = dynamodb.Table(DYNAMO_TABLE)


def detect_bridge_keywords(text: str) -> list[str]:
    """본문에서 브릿지 키워드를 감지한다 (Ground Truth B-2 신호 규칙)."""
    detected = []
    text_lower = text.lower()
    for keyword, signals in BRIDGE_KEYWORDS.items():
        for signal in signals:
            if signal.lower() in text_lower:
                detected.append(keyword)
                break
    return detected[:MAX_BRIDGE_KEYWORDS]


def call_bedrock_claude(message_text: str) -> dict:
    """Bedrock Claude (Opus 4.6)를 호출하여 메시지를 분류·구조화·살 붙이기한다."""
    today = datetime.now(KST).strftime("%Y-%m-%d")

    user_prompt = f"""오늘 날짜: {today}

다음 텔레그램 메시지를 분석하여:
1. 숨겨진 의도를 파악하고
2. 성원의 철학과 연결하여 살을 붙이고
3. PARA 분류하여 구조화된 마크다운으로 변환하세요.

---
{message_text}
---

JSON으로만 응답하세요."""

    # Context Caching: 시스템 프롬프트에 cache_control을 설정하여
    # 매 호출마다 동일한 긴 프롬프트(~3000토큰)를 캐싱.
    # 첫 호출에서 캐시가 생성되고, 이후 호출은 캐시된 프롬프트를 재사용하여
    # 입력 비용을 최대 90% 절감한다.
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "system": [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.4,
    })

    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    response_text = result["content"][0]["text"]

    # JSON 추출 (```json ... ``` 블록이 있을 수 있음)
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError("Claude 응답에서 JSON을 찾을 수 없음")


def commit_to_github(file_path: str, content: str, commit_message: str) -> dict:
    """GitHub API로 파일을 커밋한다."""
    encoded_path = urllib.parse.quote(file_path, safe="/")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{encoded_path}"

    # 기존 파일 확인 (같은 이름이 있으면 SHA 필요)
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "obsidian-telegram-pipeline",
    }

    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            existing = json.loads(resp.read())
            sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    # 파일 생성/업데이트
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def send_telegram_message(chat_id: int, text: str, reply_markup: dict = None):
    """텔레그램으로 응답 메시지를 보낸다."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload_dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload_dict["reply_markup"] = reply_markup
    payload = json.dumps(payload_dict).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError:
        # parse_mode 실패 시 plain text로 재시도
        payload_dict.pop("parse_mode", None)
        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())


def edit_telegram_message(chat_id: int, message_id: int, text: str):
    """텔레그램 메시지를 수정한다 (버튼 제거용)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = json.dumps({
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError:
        pass


def answer_callback_query(callback_query_id: str, text: str = ""):
    """텔레그램 callback query에 응답한다 (버튼 로딩 해제)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload = json.dumps({
        "callback_query_id": callback_query_id,
        "text": text,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError:
        pass


def sanitize_filename(title: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거한다."""
    sanitized = re.sub(r'[\\/:*?"<>|]', "", title)
    sanitized = sanitized.strip()
    return sanitized[:TITLE_MAX_LEN] if sanitized else "Untitled"


def save_pending(note_id: str, data: dict):
    """DynamoDB에 pending 노트를 임시 저장한다."""
    item = {"note_id": note_id, **data}
    # DynamoDB는 float를 Decimal로 저장해야 하므로 문자열로 변환
    item["confidence"] = str(item["confidence"])
    pending_table.put_item(Item=item)


def load_pending(note_id: str) -> dict:
    """DynamoDB에서 pending 노트를 불러온다."""
    resp = pending_table.get_item(Key={"note_id": note_id})
    item = resp.get("Item")
    if not item:
        return None
    item["confidence"] = float(item["confidence"])
    return item


def delete_pending(note_id: str):
    """DynamoDB에서 pending 노트를 삭제한다."""
    pending_table.delete_item(Key={"note_id": note_id})


def is_too_short(text: str) -> bool:
    """Ground Truth C-5: 3줄 이하 + 맥락 없음이면 반려 대상."""
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    context_signals = ["왜냐", "이유는", "맥락은", "때문에", "왜?", "→", "그래서", "느낀 건", "깨달은"]
    has_context = any(signal in text for signal in context_signals)
    return len(lines) <= MIN_CONTEXT_LINES and not has_context


def strip_frontmatter(markdown: str) -> str:
    """마크다운에서 프론트매터(---)를 제거하고 본문만 반환한다."""
    if not markdown.startswith("---"):
        return markdown
    end_idx = markdown.find("---", 3)
    if end_idx == -1:
        return markdown
    return markdown[end_idx + 3:].strip()


def build_preview_message(title: str, para_path: str, confidence: float,
                          slip_box_candidate: bool, bridge_keywords: list[str],
                          file_path: str, markdown_content: str) -> str:
    """미리보기 텍스트를 생성한다."""
    keywords_str = " ".join(bridge_keywords) if bridge_keywords else "없음"
    candidate_str = " | Slip-Box 승격 후보" if slip_box_candidate else ""

    body_text = strip_frontmatter(markdown_content)
    if len(body_text) > PREVIEW_BODY_MAX_LEN:
        body_text = body_text[:PREVIEW_BODY_MAX_LEN] + "\n\n... (이하 생략)"

    return (
        f"[미리보기]\n"
        f"제목: {title}\n"
        f"분류: {para_path} (확신도: {confidence:.0%}){candidate_str}\n"
        f"키워드: {keywords_str}\n"
        f"경로: {file_path}\n"
        f"{'─' * 30}\n\n"
        f"{body_text}\n\n"
        f"{'─' * 30}\n"
        f"확인 후 아래 버튼을 눌러주세요."
    )


def build_note_file_path(para_path: str, title: str) -> str:
    """PARA 경로 + 날짜 + 제목으로 파일 경로를 생성한다."""
    today = datetime.now(KST).strftime("%Y-%m-%d")
    safe_title = sanitize_filename(title)
    return f"{para_path}{today}_{safe_title}.md"


def handle_new_message(chat_id: int, text: str):
    """Step 1 — 제안: 메시지를 처리하고 미리보기 + 버튼을 보낸다."""
    if text.strip() == "/start":
        send_telegram_message(
            chat_id,
            "옵시디언 파이프라인 봇입니다.\n"
            "메시지를 보내면 분류·구조화한 결과를 보여드립니다.\n"
            "확인 후 저장 버튼을 누르면 볼트에 저장됩니다.\n\n"
            "Ground Truth 규칙:\n"
            "- '왜 이 생각을 했는가'를 같이 적어주세요\n"
            "- 3줄 이하 + 맥락 없으면 반려됩니다"
        )
        return

    if is_too_short(text):
        send_telegram_message(
            chat_id,
            "반려: 맥락이 부족합니다.\n\n"
            "Ground Truth F-1 규칙:\n"
            "\"왜 남겼지?\"를 반드시 같이 적어야 합니다.\n\n"
            "다시 보내주세요. 예시:\n"
            f"  {text}\n"
            "  → 왜냐하면 오늘 OO하면서 느낀 건데..."
        )
        return

    claude_result = call_bedrock_claude(text)

    title = claude_result.get("title", "Untitled")
    para_path = claude_result.get("para_path", "Inbox/")
    confidence = claude_result.get("confidence", 0)
    slip_box_candidate = claude_result.get("slip_box_candidate", False)
    bridge_keywords = claude_result.get("bridge_keywords", [])
    markdown_content = claude_result.get("markdown", "")

    if confidence < CONFIDENCE_THRESHOLD:
        para_path = "Inbox/"

    note_id = datetime.now(KST).strftime("%Y%m%d%H%M%S")
    save_pending(note_id, {
        "title": title,
        "para_path": para_path,
        "confidence": confidence,
        "slip_box_candidate": slip_box_candidate,
        "bridge_keywords": bridge_keywords,
        "markdown": markdown_content,
    })

    file_path = build_note_file_path(para_path, title)
    preview = build_preview_message(
        title, para_path, confidence, slip_box_candidate,
        bridge_keywords, file_path, markdown_content,
    )
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ 저장", "callback_data": f"save:{note_id}"},
                {"text": "✏️ Inbox로", "callback_data": f"inbox:{note_id}"},
                {"text": "❌ 취소", "callback_data": f"cancel:{note_id}"},
            ]
        ]
    }
    send_telegram_message(chat_id, preview, reply_markup=reply_markup)


def handle_callback(callback_query: dict):
    """Step 2 — 실행: 버튼 클릭 시 GitHub 커밋 또는 취소."""
    callback_id = callback_query["id"]
    callback_data = callback_query["data"]  # "save:20260402043012" 형식
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]

    # 권한 확인
    if chat_id != ALLOWED_CHAT_ID:
        answer_callback_query(callback_id, "권한 없음")
        return

    # action과 note_id 분리
    parts = callback_data.split(":", 1)
    action = parts[0]
    note_id = parts[1] if len(parts) > 1 else ""

    if action == "cancel":
        # ❌ 취소 — DynamoDB에서 삭제
        delete_pending(note_id)
        answer_callback_query(callback_id, "취소됨")
        edit_telegram_message(chat_id, message_id, "❌ 저장 취소됨")
        return

    # DynamoDB에서 pending 데이터 불러오기
    pending = load_pending(note_id)
    if not pending:
        answer_callback_query(callback_id, "만료된 데이터입니다. 다시 보내주세요.")
        return

    title = pending["title"]
    para_path = pending["para_path"]
    confidence = pending["confidence"]
    slip_box_candidate = pending["slip_box_candidate"]
    bridge_keywords = pending["bridge_keywords"]
    markdown_content = pending["markdown"]

    # Inbox로 변경
    if action == "inbox":
        para_path = "Inbox/"

    file_path = build_note_file_path(para_path, title)

    commit_msg = f"telegram: {title}"
    if slip_box_candidate:
        commit_msg += " [Slip-Box 후보]"

    # GitHub 커밋
    commit_to_github(file_path, markdown_content, commit_msg)

    # DynamoDB에서 삭제 (사용 완료)
    delete_pending(note_id)

    # 완료 메시지로 수정 (버튼 제거)
    keywords_str = " ".join(bridge_keywords) if bridge_keywords else "없음"
    candidate_str = " | Slip-Box 승격 후보" if slip_box_candidate else ""
    done_text = (
        f"✅ 저장 완료\n"
        f"제목: {title}\n"
        f"분류: {para_path} (확신도: {confidence:.0%}){candidate_str}\n"
        f"키워드: {keywords_str}\n"
        f"경로: {file_path}"
    )
    edit_telegram_message(chat_id, message_id, done_text)
    answer_callback_query(callback_id, "저장 완료!")


def lambda_handler(event, context):
    """AWS Lambda 진입점."""
    try:
        # API Gateway에서 body 파싱
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", event)

        # ── callback_query 처리 (버튼 클릭) ──
        callback_query = body.get("callback_query")
        if callback_query:
            handle_callback(callback_query)
            return {"statusCode": 200, "body": "Callback handled"}

        # ── 새 메시지 처리 ──
        message = body.get("message")
        if not message:
            return {"statusCode": 200, "body": "No message"}

        chat = message.get("chat")
        if not chat or "id" not in chat:
            return {"statusCode": 200, "body": "Invalid message format"}
        chat_id = chat["id"]

        # 봇 자신의 메시지 무시 (에러 메시지 무한 루프 방지)
        if message.get("from", {}).get("is_bot", False):
            return {"statusCode": 200, "body": "Bot message ignored"}

        # 성원만 사용 가능 (다른 사람의 메시지는 무시)
        if chat_id != ALLOWED_CHAT_ID:
            return {"statusCode": 200, "body": "Unauthorized"}

        text = message.get("text", "")
        message_id = str(message.get("message_id", ""))

        if not text:
            send_telegram_message(chat_id, "텍스트 메시지만 처리할 수 있습니다.")
            return {"statusCode": 200, "body": "Non-text message"}

        # 중복 메시지 방지 (텔레그램이 타임아웃으로 같은 메시지를 재전송하는 문제)
        dedup_key = f"msg:{message_id}"
        try:
            pending_table.put_item(
                Item={"note_id": dedup_key, "ttl": "dedup"},
                ConditionExpression="attribute_not_exists(note_id)",
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # 이미 처리 중인 메시지 → 무시
            return {"statusCode": 200, "body": "Duplicate"}

        handle_new_message(chat_id, text)
        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        try:
            send_telegram_message(ALLOWED_CHAT_ID, f"⚠️ 오류 발생: {type(e).__name__}: {str(e)[:200]}")
        except Exception:
            pass
        # 반드시 200 반환 — 500이면 텔레그램이 같은 webhook을 무한 재전송한다
        return {"statusCode": 200, "body": "Error handled"}
