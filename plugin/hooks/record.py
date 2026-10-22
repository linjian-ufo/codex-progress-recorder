"""Codex lifecycle hook: export user-visible commentary for this session."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def export(event):
    session_id = event.get("session_id", "")
    if not session_id or not all(c.isalnum() or c == "-" for c in session_id):
        return
    transcript = event.get("transcript_path")
    if transcript and Path(transcript).is_file():
        source = Path(transcript)
    else:
        root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
        matches = list(root.rglob(f"*{session_id}.jsonl"))
        if not matches:
            return
        source = matches[0]
    entries = []
    session_cwd = None
    with source.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = item.get("payload") or {}
            if item.get("type") == "session_meta":
                session_cwd = payload.get("cwd")
            if item.get("type") != "response_item" or payload.get("type") != "message":
                continue
            phase = payload.get("phase")
            if payload.get("role") != "assistant" or phase not in ("commentary", "final_answer"):
                continue
            body = "\n".join(p.get("text", "") for p in payload.get("content", [])
                             if p.get("type") == "output_text").strip()
            if body:
                timestamp = item.get("timestamp", "")
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
                label = "最终回复" if phase == "final_answer" else "过程回复"
                entries.append(f"## {timestamp} · {label}\n\n{body}\n\n")
    configured = os.environ.get("CODEX_PROGRESS_OUTPUT_DIR")
    project = event.get("cwd") or session_cwd
    project_path = Path(project) if project else None
    if configured:
        output_dir = Path(configured)
    elif project_path and project_path.is_dir():
        output_dir = project_path / "Codex过程记录"
    else:
        output_dir = Path.home() / "Documents" / "Codex过程记录"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{session_id}.md"
    temporary = output_dir / f"{session_id}.{os.getpid()}.md.tmp"
    temporary.write_text(f"# Codex 过程回复\n\n会话：`{session_id}`\n\n" + "".join(entries), encoding="utf-8")
    temporary.replace(target)


if __name__ == "__main__":
    try:
        export(json.load(sys.stdin))
    except Exception as exc:
        print(f"Codex progress recorder: {exc}", file=sys.stderr)
        sys.exit(1)
