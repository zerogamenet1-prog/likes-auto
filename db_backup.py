"""Push/pull SQLite backup to Visperhost so Render Free redeploys can restore it."""
from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

from db import DB_PATH

DEFAULT_PUT = "https://likes-auto.com/db-put.php"
DEFAULT_TOKEN = os.environ.get("DB_BACKUP_TOKEN") or "la-db-bak-RMkcYN4hq7OE19m6vhGe9c-zwDoWGI0Yx9IfvF-IGA"


def backup_token() -> str:
    return (os.environ.get("DB_BACKUP_TOKEN") or DEFAULT_TOKEN).strip()


def push_db_backup(path: Path | None = None) -> tuple[bool, str]:
    db = Path(path or DB_PATH)
    if not db.is_file() or db.stat().st_size < 1024:
        return False, "missing_db"
    url = (os.environ.get("DB_BACKUP_PUT_URL") or DEFAULT_PUT).strip()
    token = backup_token()
    raw = db.read_bytes()
    if not raw.startswith(b"SQLite format 3"):
        return False, "not_sqlite"
    req = urllib.request.Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "X-LA-DB-TOKEN": token,
            "User-Agent": "likes-auto-db-backup/1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return True, body[:200]
    except urllib.error.HTTPError as e:
        return False, f"http_{e.code}:{e.read()[:120]!r}"
    except Exception as e:
        return False, f"{type(e).__name__}:{e}"
