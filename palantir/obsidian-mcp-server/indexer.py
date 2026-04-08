"""
옵시디언 노트 인덱서 (증분 인덱싱)
- 변경/추가된 노트만 업데이트, 삭제된 노트는 DB에서 제거
- --full 플래그로 전체 재인덱싱 가능
"""

import os
import re
import sys
import time
import json
import lancedb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from bridge_keywords import BRIDGE_KEYWORDS

VAULT_PATH = "{VAULT_PATH}"
DB_PATH = os.path.expanduser("~/obsidian-mcp-server/vault.lancedb")
TABLE_NAME = "notes"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
STATE_FILE = os.path.expanduser("~/obsidian-mcp-server/.index_state.json")
MAX_CHARS = 3000


def get_folder_weight(rel_path: str, filename: str) -> float:
    if rel_path.startswith("0. Slip-Box/") or "P1E" in filename:
        return 3.0
    elif rel_path.startswith("1. Project/"):
        return 2.0
    else:
        return 1.0


def detect_bridge_keywords(text: str) -> str:
    text_lower = text.lower()
    matched = []
    for kw_name, signals in BRIDGE_KEYWORDS.items():
        for signal in signals:
            if signal.lower() in text_lower:
                matched.append(kw_name)
                break
    return ",".join(matched)


def clean_markdown(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    text = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def scan_vault(vault_path: str) -> dict[str, float]:
    vault = Path(vault_path)
    skip_dirs = {".obsidian", ".trash", ".smart-env", "Attachments", ".git"}
    files = {}
    for md_file in vault.rglob("*.md"):
        if any(part in skip_dirs for part in md_file.parts):
            continue
        rel_path = str(md_file.relative_to(vault))
        files[rel_path] = md_file.stat().st_mtime
    return files


def load_state() -> dict[str, float]:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict[str, float]):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def compute_changes(current: dict[str, float], previous: dict[str, float]):
    added = []
    modified = []
    deleted = []
    for path, mtime in current.items():
        if path not in previous:
            added.append(path)
        elif mtime > previous[path]:
            modified.append(path)
    for path in previous:
        if path not in current:
            deleted.append(path)
    return added, modified, deleted


def process_note(vault_path: str, rel_path: str) -> dict | None:
    full_path = Path(vault_path) / rel_path
    try:
        text = full_path.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if not text:
        return None
    clean = clean_markdown(text)
    if len(clean) < 10:
        return None
    filename = full_path.stem
    weight = get_folder_weight(rel_path, filename)
    bridge_kws = detect_bridge_keywords(clean)
    return {
        "filename": filename,
        "path": rel_path,
        "text": clean[:MAX_CHARS],
        "weight": weight,
        "bridge_keywords": bridge_kws,
    }


def full_reindex(vault_path: str, current_files: dict[str, float]):
    print("[ 전체 재인덱싱 모드 ]")
    notes = []
    for rel_path in current_files:
        note = process_note(vault_path, rel_path)
        if note:
            notes.append(note)
    print(f"  -> {len(notes)}개 노트 발견")
    if not notes:
        print("노트를 찾지 못했습니다.")
        return
    print(f"임베딩 모델 로딩 중: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"{len(notes)}개 노트 임베딩 중...")
    texts = [n["text"] for n in notes]
    vectors = model.encode(texts, show_progress_bar=True, batch_size=64)
    db = lancedb.connect(DB_PATH)
    data = []
    for i, note in enumerate(notes):
        note["vector"] = vectors[i].tolist()
        data.append(note)
    existing = db.list_tables()
    table_names = existing.tables if hasattr(existing, "tables") else list(existing)
    if TABLE_NAME in table_names:
        db.drop_table(TABLE_NAME)
    db.create_table(TABLE_NAME, data=data)
    print(f"완료! {len(notes)}개 노트가 LanceDB에 저장되었습니다.")
    save_state(current_files)


def incremental_index(vault_path: str, current_files: dict[str, float],
                      added: list, modified: list, deleted: list):
    print("[ 증분 인덱싱 모드 ]")
    print(f"  -> 추가: {len(added)}개 / 수정: {len(modified)}개 / 삭제: {len(deleted)}개")
    to_process = added + modified
    if not to_process and not deleted:
        print("  -> 변경 사항 없음. 스킵.")
        return
    db = lancedb.connect(DB_PATH)
    table = db.open_table(TABLE_NAME)
    if deleted:
        for path in deleted:
            table.delete(f'path = "{path.replace(chr(34), "")}"')
        print(f"  -> {len(deleted)}개 노트 DB에서 제거 완료")
    if to_process:
        notes = []
        for rel_path in to_process:
            note = process_note(vault_path, rel_path)
            if note:
                notes.append(note)
        if notes:
            print(f"임베딩 모델 로딩 중: {EMBEDDING_MODEL}")
            model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"{len(notes)}개 노트 임베딩 중...")
            texts = [n["text"] for n in notes]
            vectors = model.encode(texts, show_progress_bar=True, batch_size=64)
            for note in notes:
                safe_path = note["path"].replace(chr(34), "")
                table.delete(f'path = "{safe_path}"')
            data = []
            for i, note in enumerate(notes):
                note["vector"] = vectors[i].tolist()
                data.append(note)
            table.add(data)
            print(f"  -> {len(data)}개 노트 임베딩 완료")
    save_state(current_files)


if __name__ == "__main__":
    start = time.time()
    force_full = "--full" in sys.argv
    print(f"볼트 경로: {VAULT_PATH}")
    print("볼트 스캔 중...")
    current_files = scan_vault(VAULT_PATH)
    print(f"  -> {len(current_files)}개 .md 파일 발견")
    previous_state = load_state()
    db = lancedb.connect(DB_PATH)
    existing = db.list_tables()
    table_names = existing.tables if hasattr(existing, "tables") else list(existing)
    need_full = force_full or not previous_state or TABLE_NAME not in table_names
    if need_full:
        if force_full:
            print("  -> --full 플래그 감지. 전체 재인덱싱 실행.")
        elif not previous_state:
            print("  -> 첫 실행. 전체 재인덱싱 실행.")
        else:
            print("  -> DB 테이블 없음. 전체 재인덱싱 실행.")
        full_reindex(VAULT_PATH, current_files)
    else:
        added, modified, deleted = compute_changes(current_files, previous_state)
        incremental_index(VAULT_PATH, current_files, added, modified, deleted)
    elapsed = time.time() - start
    print(f"\n총 소요 시간: {elapsed:.1f}초")
