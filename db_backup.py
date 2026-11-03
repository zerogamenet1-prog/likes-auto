"""Push/pull SQLite backup to Visperhost so Render Free redeploys can restore it.

Render Free has no persistent disk — every redeploy starts empty. This module:
- snapshots SQLite safely
- pushes to Visperhost (db-put.php) with history copies
- debounces backups after mutations
- flushes a final backup on process shutdown (SIGTERM before redeploy)
"""
from __future__ import annotations

import atexit
import os
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from db import DB_PATH

DEFAULT_PUT = "https://likes-auto.com/db-put.php"
DEFAULT_TOKEN = os.environ.get("DB_BACKUP_TOKEN") or "la-db-bak-RMkcYN4hq7OE19m6vhGe9c-zwDoWGI0Yx9IfvF-IGA"

_lock = threading.Lock()
_timer: threading.Timer | None = None
_pending_reason = ""
_last_ok_at = 0.0
_last_msg = ""
_shutdown_done = False
DEBOUNCE_SEC = 4.0
MIN_GAP_SEC = 12.0
# Reasons that must push immediately (no debounce gap).
# Money/user events flush quickly. shutdown is NOT force-capable:
# a dying Free instance can already have an empty disk and must not
# overwrite a richer Visperhost restore.
CRITICAL_REASONS = frozenset({
    "admin",
    "flush",
    "approve_payment",
    "adjust_balance",
    "signup",
})
FORCE_REASONS = frozenset({
    "admin",
    "flush",
    "force",
})


def backup_token() -> str:
    return (os.environ.get("DB_BACKUP_TOKEN") or DEFAULT_TOKEN).strip()


def snapshot_db(dest: Path | None = None) -> Path | None:
    """Consistent SQLite copy via the backup API (safe while app is writing)."""
    src = Path(DB_PATH)
    if not src.is_file() or src.stat().st_size < 1024:
        return None
    out = Path(dest or (src.parent / ("app-snap-%s.db" % int(time.time()))))
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        raw = src.read_bytes()
        if not raw.startswith(b"SQLite format 3"):
            return None
        # Prefer online backup API for a consistent snapshot.
        sconn = sqlite3.connect(str(src), timeout=30)
        try:
            dconn = sqlite3.connect(str(out))
            try:
                sconn.backup(dconn)
            finally:
                dconn.close()
        finally:
            sconn.close()
        if out.stat().st_size < 1024:
            return None
        return out
    except Exception:
        try:
            out.write_bytes(src.read_bytes())
            return out if out.is_file() and out.stat().st_size >= 1024 else None
        except Exception:
            return None


def _client_count(db: Path) -> int:
    """Count clients without creating -wal/-shm beside the source file."""
    try:
        uri = "file:%s?mode=ro&immutable=1" % Path(db).resolve().as_posix()
        con = sqlite3.connect(uri, uri=True)
        try:
            row = con.execute("SELECT COUNT(*) FROM clients").fetchone()
            return int(row[0] or 0) if row else 0
        finally:
            con.close()
    except Exception:
        try:
            con = sqlite3.connect(str(db))
            try:
                row = con.execute("SELECT COUNT(*) FROM clients").fetchone()
                return int(row[0] or 0) if row else 0
            finally:
                con.close()
        except Exception:
            return -1


def _remote_restore_client_count() -> int:
    """Peek hosted restore so a seeded empty boot cannot overwrite a richer backup."""
    url = (
        os.environ.get("DB_RESTORE_URL")
        or "https://likes-auto.com/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db"
    ).strip()
    bust = "%s?peek=%s" % (url, int(time.time()))
    tmp = None
    try:
        req = urllib.request.Request(
            bust,
            headers={
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "User-Agent": "likes-auto-db-backup/2-peek",
            },
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
        if not raw.startswith(b"SQLite format 3") or len(raw) < 1024:
            return -1
        tmp = Path(DB_PATH).parent / ("app-peek-%s.db" % int(time.time()))
        tmp.write_bytes(raw)
        return _client_count(tmp)
    except Exception:
        return -1
    finally:
        if tmp is not None and tmp.is_file():
            try:
                tmp.unlink()
            except Exception:
                pass


def push_db_backup(path: Path | None = None, reason: str = "") -> tuple[bool, str]:
    global _last_ok_at, _last_msg
    snap = None
    try:
        if path is None:
            snap = snapshot_db()
            db = snap
        else:
            db = Path(path)
        if not db or not db.is_file() or db.stat().st_size < 1024:
            return False, "missing_db"
        reason = reason or "manual"
        # Guard: never let a thin/dying instance wipe a richer Visperhost restore.
        local_n = _client_count(db)
        remote_n = _remote_restore_client_count()
        force = reason in FORCE_REASONS
        if not force and local_n >= 0 and remote_n >= 0 and local_n < remote_n:
            _last_msg = "skip_thinner_than_remote local=%s remote=%s reason=%s" % (
                local_n,
                remote_n,
                reason,
            )
            return False, _last_msg
        if not force and local_n == 0 and remote_n > 0:
            _last_msg = "skip_zero_clients reason=%s" % reason
            return False, _last_msg
        url = (os.environ.get("DB_BACKUP_PUT_URL") or DEFAULT_PUT).strip()
        token = backup_token()
        raw = db.read_bytes()
        if not raw.startswith(b"SQLite format 3"):
            return False, "not_sqlite"
        headers = {
            "Content-Type": "application/octet-stream",
            "X-LA-DB-TOKEN": token,
            "X-LA-DB-REASON": reason[:80],
            "User-Agent": "likes-auto-db-backup/2",
        }
        if force:
            headers["X-LA-DB-FORCE"] = "1"
        req = urllib.request.Request(
            url,
            data=raw,
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            _last_ok_at = time.time()
            _last_msg = body[:200]
            return True, _last_msg
    except urllib.error.HTTPError as e:
        _last_msg = f"http_{e.code}:{e.read()[:120]!r}"
        return False, _last_msg
    except Exception as e:
        _last_msg = f"{type(e).__name__}:{e}"
        return False, _last_msg
    finally:
        if snap and snap.is_file():
            try:
                snap.unlink()
            except Exception:
                pass


def backup_status() -> dict:
    return {
        "last_ok_at": _last_ok_at,
        "last_msg": _last_msg,
        "db_bytes": Path(DB_PATH).stat().st_size if Path(DB_PATH).is_file() else 0,
    }


def _fire():
    global _timer, _pending_reason
    with _lock:
        reason = _pending_reason or "debounced"
        _pending_reason = ""
        _timer = None
    # Avoid hammering Visperhost if many writes land together.
    critical = reason in CRITICAL_REASONS
    if (
        _last_ok_at
        and (time.time() - _last_ok_at) < MIN_GAP_SEC
        and not critical
    ):
        schedule_backup(reason)
        return
    ok, msg = push_db_backup(reason=reason)
    try:
        from db import add_log

        add_log("db-backup %s %s" % ("ok" if ok else "fail", (msg or "")[:120]), "-")
    except Exception:
        pass


def schedule_backup(reason: str = "change") -> None:
    """Debounced background push — call after any important DB write."""
    global _timer, _pending_reason
    reason = reason or "change"
    # Critical money/user events flush almost immediately.
    delay = 0.8 if reason in CRITICAL_REASONS else DEBOUNCE_SEC
    with _lock:
        prev = _pending_reason
        # Keep the more critical pending reason if both are queued.
        if prev in CRITICAL_REASONS and reason not in CRITICAL_REASONS:
            reason = prev
        _pending_reason = reason
        if _timer is not None:
            try:
                _timer.cancel()
            except Exception:
                pass
        _timer = threading.Timer(delay, _fire)
        _timer.daemon = True
        _timer.start()


def flush_backup_now(reason: str = "flush") -> tuple[bool, str]:
    global _timer, _pending_reason
    with _lock:
        if _timer is not None:
            try:
                _timer.cancel()
            except Exception:
                pass
            _timer = None
        _pending_reason = ""
    return push_db_backup(reason=reason)


def backup_on_shutdown() -> None:
    """Render sends SIGTERM before wiping the Free instance — push DB first."""
    global _shutdown_done
    if _shutdown_done:
        return
    _shutdown_done = True
    try:
        flush_backup_now("shutdown")
    except Exception:
        pass


atexit.register(backup_on_shutdown)
