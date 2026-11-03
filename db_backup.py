"""Push/pull SQLite backup to Visperhost so Render Free redeploys can restore it.

Render Free has no persistent disk — every redeploy starts empty. This module:
- snapshots SQLite safely
- pushes to Visperhost (db-put.php) with history copies
- debounces backups after mutations
- flushes a final backup on process shutdown (SIGTERM before redeploy)

Hard rule: never overwrite a richer Visperhost restore with a thinner DB
(fewer clients / fewer paid payments), even on shutdown or FORCE.
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
DEFAULT_RESTORE = (
    os.environ.get("DB_RESTORE_URL")
    or "https://likes-auto.com/.la-db-restore-d1qyg5az73cs4unx8jl9trbw.db"
)
DEFAULT_RESTORE_ALT = (
    os.environ.get("DB_RESTORE_URL_ALT")
    or "https://likes-auto.com/.la-db-restore-latest.db"
)

_lock = threading.Lock()
_timer: threading.Timer | None = None
_pending_reason = ""
_last_ok_at = 0.0
_last_msg = ""
_shutdown_done = False
DEBOUNCE_SEC = 4.0
MIN_GAP_SEC = 12.0
# Money/user events flush quickly. shutdown is NEVER force-capable.
CRITICAL_REASONS = frozenset({
    "admin",
    "flush",
    "approve_payment",
    "adjust_balance",
    "signup",
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


def db_fingerprint(db: Path) -> dict:
    """Wealth score used to refuse thinner restores/backups."""
    out = {"clients": -1, "paid": -1, "balance": -1.0, "bytes": 0}
    try:
        out["bytes"] = int(Path(db).stat().st_size)
    except Exception:
        return out
    try:
        uri = "file:%s?mode=ro&immutable=1" % Path(db).resolve().as_posix()
        con = sqlite3.connect(uri, uri=True)
    except Exception:
        try:
            con = sqlite3.connect(str(db))
        except Exception:
            return out
    try:
        try:
            out["clients"] = int(
                con.execute("SELECT COUNT(*) FROM clients").fetchone()[0] or 0
            )
        except Exception:
            out["clients"] = -1
        try:
            out["paid"] = int(
                con.execute(
                    "SELECT COUNT(*) FROM payments WHERE status='paid'"
                ).fetchone()[0]
                or 0
            )
        except Exception:
            out["paid"] = -1
        try:
            out["balance"] = float(
                con.execute(
                    "SELECT COALESCE(SUM(balance),0) FROM clients"
                ).fetchone()[0]
                or 0
            )
        except Exception:
            out["balance"] = -1.0
        return out
    finally:
        try:
            con.close()
        except Exception:
            pass


def _client_count(db: Path) -> int:
    return int(db_fingerprint(db).get("clients") or -1)


def _is_thinner(local: dict, remote: dict) -> bool:
    """True when local would destroy customers / paid history on Visperhost."""
    lc, rc = int(local.get("clients") or -1), int(remote.get("clients") or -1)
    if lc >= 0 and rc >= 0 and lc < rc:
        return True
    if lc == 0 and rc > 0:
        return True
    lp, rp = int(local.get("paid") or -1), int(remote.get("paid") or -1)
    if lc >= 0 and rc >= 0 and lc == rc and lp >= 0 and rp >= 0 and lp < rp:
        return True
    lb, rb = int(local.get("bytes") or 0), int(remote.get("bytes") or 0)
    if lc == 0 and rb >= 100000 and lb + 4096 < rb:
        return True
    return False


def _download_restore(url: str, dest: Path) -> bool:
    bust = "%s?t=%s" % (url.rstrip("?"), int(time.time()))
    try:
        req = urllib.request.Request(
            bust,
            headers={
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "User-Agent": "likes-auto-db-backup/3-restore",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        if not raw.startswith(b"SQLite format 3") or len(raw) < 4096:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp-restore")
        tmp.write_bytes(raw)
        tmp.replace(dest)
        return True
    except Exception:
        return False


def _remote_restore_fingerprint() -> dict:
    """Peek hosted restore so a seeded empty boot cannot overwrite a richer backup."""
    empty = {"clients": -1, "paid": -1, "balance": -1.0, "bytes": 0}
    url = DEFAULT_RESTORE.strip()
    tmp = None
    try:
        bust = "%s?peek=%s" % (url, int(time.time()))
        req = urllib.request.Request(
            bust,
            headers={
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "User-Agent": "likes-auto-db-backup/3-peek",
            },
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
        if not raw.startswith(b"SQLite format 3") or len(raw) < 1024:
            return empty
        tmp = Path(DB_PATH).parent / ("app-peek-%s.db" % int(time.time()))
        tmp.write_bytes(raw)
        return db_fingerprint(tmp)
    except Exception:
        return empty
    finally:
        if tmp is not None and tmp.is_file():
            try:
                tmp.unlink()
            except Exception:
                pass


def ensure_restored_db() -> bool:
    """If local DB lost customers, pull Visperhost restore before serving traffic."""
    local = Path(DB_PATH)
    local_fp = db_fingerprint(local) if local.is_file() else {
        "clients": 0, "paid": 0, "balance": 0.0, "bytes": 0
    }
    remote_fp = _remote_restore_fingerprint()
    if int(remote_fp.get("clients") or 0) <= 0:
        return False
    if int(local_fp.get("clients") or 0) >= int(remote_fp.get("clients") or 0) and not _is_thinner(
        local_fp, remote_fp
    ):
        # Local is at least as rich.
        if int(local_fp.get("clients") or 0) > 0:
            return False
    for url in (DEFAULT_RESTORE, DEFAULT_RESTORE_ALT):
        if _download_restore(url, local):
            got = db_fingerprint(local)
            if int(got.get("clients") or 0) >= int(remote_fp.get("clients") or 0):
                try:
                    from db import add_log

                    add_log(
                        "db-restore ok clients=%s paid=%s" % (got.get("clients"), got.get("paid")),
                        "-",
                    )
                except Exception:
                    pass
                return True
    return False


def push_db_backup(
    path: Path | None = None,
    reason: str = "",
    allow_thinner: bool = False,
) -> tuple[bool, str]:
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
        local_fp = db_fingerprint(db)
        remote_fp = _remote_restore_fingerprint()
        # Absolute rule: never wipe customers unless explicitly allow_thinner.
        if not allow_thinner and _is_thinner(local_fp, remote_fp):
            _last_msg = (
                "skip_thinner_than_remote local=%s remote=%s reason=%s"
                % (local_fp, remote_fp, reason)
            )
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
            "User-Agent": "likes-auto-db-backup/3",
        }
        # Never send FORCE for thinner. Only intentional admin allow_thinner.
        if allow_thinner:
            headers["X-LA-DB-ALLOW_THINNER"] = "1"
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
    delay = 0.8 if reason in CRITICAL_REASONS else DEBOUNCE_SEC
    with _lock:
        prev = _pending_reason
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
        # reason=shutdown never bypasses thinner protection.
        flush_backup_now("shutdown")
    except Exception:
        pass


atexit.register(backup_on_shutdown)
