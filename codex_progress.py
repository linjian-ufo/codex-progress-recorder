"""Export Codex Desktop's visible progress messages from local session logs."""

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path


def session_root():
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"


def sessions(root):
    return sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def progress(path):
    with path.open("r", encoding="utf-8", errors="replace") as source:
        for line in source:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue  # A live session may end with a partial line.
            payload = item.get("payload") or {}
            if item.get("type") != "response_item" or payload.get("type") != "message":
                continue
            phase = payload.get("phase")
            if payload.get("role") != "assistant" or phase not in ("commentary", "final_answer"):
                continue
            message = "\n".join(part.get("text", "") for part in payload.get("content", [])
                                if part.get("type") == "output_text").strip()
            if message:
                yield item.get("timestamp", ""), phase, message


def stamp(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso


def title(path):
    match = re.search(r"([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.jsonl$", path.name)
    return match.group(1) if match else path.stem


def main():
    parser = argparse.ArgumentParser(description="Record visible Codex progress replies (commentary).")
    parser.add_argument("--session", help="Session UUID or full .jsonl file path; default: newest session")
    parser.add_argument("--output", type=Path, help="Markdown output file; default: stdout")
    parser.add_argument("--follow", action="store_true", help="Keep recording new replies")
    parser.add_argument("--list", action="store_true", help="List recent sessions")
    args = parser.parse_args()
    found = sessions(session_root())
    if args.list:
        for path in found[:30]:
            print(f"{title(path)}  {datetime.fromtimestamp(path.stat().st_mtime).astimezone():%Y-%m-%d %H:%M}  {path}")
        return
    if args.session:
        specified = Path(args.session)
        matches = [specified] if specified.is_file() else [p for p in found if title(p) == args.session]
    else:
        matches = found[:1]
    if not matches:
        parser.error("Session not found. Run --list to see available sessions.")
    path = matches[0]
    seen = 0
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"# Codex 过程回复\n\n会话：`{title(path)}`\n\n", encoding="utf-8")
    while True:
        entries = list(progress(path))
        new = entries[seen:]
        if new:
            rendered = "".join(f"## {stamp(ts)} · {'最终回复' if phase == 'final_answer' else '过程回复'}\n\n{body}\n\n" for ts, phase, body in new)
            if args.output:
                with args.output.open("a", encoding="utf-8") as target:
                    target.write(rendered)
            else:
                print(rendered, end="", flush=True)
            seen = len(entries)
        if not args.follow:
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
