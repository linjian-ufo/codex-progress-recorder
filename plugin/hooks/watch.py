"""Watch local Codex transcripts and keep exported replies current."""

import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from record import export


def main():
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    seen = {}
    while True:
        try:
            # Recent sessions are enough for active chats; old files are handled by hooks.
            folders = []
            for day in (date.today(), date.today() - timedelta(days=1)):
                folders.append(root / str(day.year) / f"{day.month:02d}" / f"{day.day:02d}")
            for folder in folders:
                if not folder.is_dir():
                    continue
                for path in folder.glob("*.jsonl"):
                    try:
                        modified = path.stat().st_mtime_ns
                    except OSError:
                        continue
                    if seen.get(path) == modified:
                        continue
                    seen[path] = modified
                    session_id = path.stem.rsplit("-", 5)[-5:]
                    session_id = "-".join(session_id)
                    try:
                        export({"session_id": session_id, "transcript_path": str(path)})
                    except (OSError, ValueError):
                        pass
        except OSError:
            pass
        time.sleep(2)


if __name__ == "__main__":
    main()
