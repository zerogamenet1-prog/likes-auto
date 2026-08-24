import hashlib
import os
import re
import secrets
from pathlib import Path

from db import ROOT, connect, get_settings, now


KINDS = ("promptpay", "truemoney", "bank", "wallet", "crypto", "other")
KIND_LABEL = {
    "promptpay": "PromptPay / QR",
    "truemoney": "TrueMoney Wallet",
    "bank": "Bank transfer",
    "wallet": "E-wallet",
    "crypto": "Crypto",
    "other": "Other",
}
# Thai labels filled after import to keep file ASCII-safe
SLIP_DIR = ROOT / "static" / "uploads" / "slips"
SLIP_MAX = 8 * 1024 * 1024
SLIP_OK = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
}


def _tlv(tag, value):
    value = str(value or "")
    return "%s%02d%s" % (tag, len(value), value)


def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return "%04X" % crc


def normalize_promptpay(target: str) -> str:
    raw = re.sub(r"\D", "", str(target or ""))
    if not raw:
        return ""
    if len(raw) == 13:
        return raw
    if len(raw) == 15 and raw.startswith("0066"):
        return raw[-13:]
    if len(raw) == 10 and raw.startswith("0"):
        return ("0000000000000" + ("66" + raw[1:]))[-13:]
    if len(raw) == 9:
        return ("0000000000000" + ("66" + raw))[-13:]
    if len(raw) >= 13:
        return raw[:13]
    return raw


def promptpay_payload(target: str, amount=None, merchant="LIKES AUTO"):
    proxy = normalize_promptpay(target)
    if not proxy:
        return ""
    digits = re.sub(r"\D", "", str(target or ""))
    if len(digits) == 13:
        aid_tag = "02"
    else:
        aid_tag = "01"
    merchant_info = _tlv("00", "A000000677010111") + _tlv(aid_tag, proxy)
    amount_txt = ""
    if amount not in (None, "", 0, "0"):
        try:
            amount_txt = "%.2f" % float(amount)
        except (TypeError, ValueError):
            amount_txt = ""
    name = re.sub(r"[^A-Za-z0-9 ._-]", "", str(merchant or "LIKES AUTO"))[:25] or "LIKES AUTO"
    parts = [
        _tlv("00", "01"),
        _tlv("01", "12" if amount_txt else "11"),
        _tlv("29", merchant_info),
        _tlv("53", "764"),
    ]
    if amount_txt:
        parts.append(_tlv("54", amount_txt))
    parts.extend([
        _tlv("58", "TH"),
        _tlv("59", name),
        _tlv("60", "Bangkok"),
    ])
    body = "".join(parts) + "6304"
    return body + crc16_ccitt(body)


def infer_kind(name, kind=""):
    k = (kind or "").strip().lower()
    if k in KINDS:
        return k
    text = (name or "").lower()
    if any(x in text for x in ("promptpay", "qr")) or "\u0e1e\u0e23\u0e49\u0e2d\u0e21\u0e40\u0e1e\u0e22\u0e4c" in (name or ""):
        return "promptpay"
    if "true" in text or "\u0e17\u0e23\u0e39" in (name or ""):
        return "truemoney"
    if any(x in text for x in ("crypto", "usdt", "btc")) or "\u0e04\u0e23\u0e34\u0e1b\u0e42\u0e15" in (name or ""):
        return "crypto"
    if "wallet" in text or "\u0e27\u0e2d\u0e25\u0e40\u0e25" in (name or ""):
        return "wallet"
    if "bank" in text or "\u0e18\u0e19\u0e32\u0e04\u0e32\u0e23" in (name or "") or "\u0e42\u0e2d\u0e19" in (name or ""):
        return "bank"
    return "other"


def make_ref_code(pid=0):
    return "LA%s" % secrets.token_hex(3).upper()


def unique_amount(base, pid):
    try:
        amt = float(base)
    except (TypeError, ValueError):
        return 0.0
    used = set()
    con = connect()
    rows = con.execute(
        "SELECT amount FROM payments WHERE status='pending' AND id!=?",
        (int(pid or 0),),
    ).fetchall()
    con.close()
    for row in rows:
        try:
            used.add(round(float(row["amount"] or 0), 2))
        except (TypeError, ValueError, KeyError):
            pass
    for step in range(1, 100):
        cents = ((int(pid or 0) + step) % 99) + 1
        exact = round(amt + (cents / 100.0), 2)
        if exact not in used:
            return exact
    return round(amt + (((int(pid or 0) % 99) + 1) / 100.0), 2)

def pay_migrate():
    con = connect()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY,
            email TEXT,
            token TEXT UNIQUE,
            used INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS slip_refs (
            trans_ref TEXT PRIMARY KEY,
            payment_id INTEGER,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS slip_hashes (
            sha256 TEXT PRIMARY KEY,
            payment_id INTEGER,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS slip_tries (
            id INTEGER PRIMARY KEY,
            payment_id INTEGER,
            created_at TEXT
        );
        """
    )
    for table, col, spec in [
        ("payments", "slip", "TEXT"),
        ("payments", "note", "TEXT"),
        ("payments", "ref_code", "TEXT"),
        ("payments", "method_id", "INTEGER"),
        ("payments", "kind", "TEXT"),
        ("payments", "trans_ref", "TEXT"),
        ("methods", "kind", "TEXT"),
        ("methods", "pay_to", "TEXT"),
        ("banks", "promptpay", "TEXT"),
    ]:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(%s)" % table)]
        if col not in cols:
            cur.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, spec))
    for row in cur.execute("SELECT id, name, kind FROM methods").fetchall():
        if not (row["kind"] or "").strip():
            cur.execute("UPDATE methods SET kind=? WHERE id=?", (infer_kind(row["name"]), row["id"]))
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("truemoney", ""))
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("pay_unique_satang", "1"))
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("pay_merchant", "LIKES AUTO"))
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("easyslip_key", ""))
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("auto_approve_slip", "1"))
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("pay_notify_token", ""))
    con.commit()
    con.close()


def method_row(method_id=None, name=""):
    con = connect()
    row = None
    if method_id:
        row = con.execute("SELECT * FROM methods WHERE id=?", (method_id,)).fetchone()
    if not row and name:
        row = con.execute("SELECT * FROM methods WHERE name=? COLLATE NOCASE", (name,)).fetchone()
    con.close()
    return dict(row) if row else None


def active_methods():
    con = connect()
    items = con.execute("SELECT * FROM methods WHERE status='active' ORDER BY id").fetchall()
    con.close()
    out = []
    for item in items:
        row = dict(item)
        row["kind"] = infer_kind(row.get("name"), row.get("kind"))
        row["kind_label"] = KIND_LABEL.get(row["kind"], row["kind"])
        out.append(row)
    return out


def get_payment(pid):
    con = connect()
    row = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    con.close()
    return dict(row) if row else None


def pay_target(method, settings):
    settings = settings or {}
    kind = infer_kind(method.get("name") if method else "", (method or {}).get("kind"))
    pay_to = ((method or {}).get("pay_to") or "").strip()
    if kind == "promptpay":
        return pay_to or (settings.get("promptpay") or "").strip()
    if kind == "truemoney":
        return pay_to or (settings.get("truemoney") or "").strip()
    return pay_to


def checkout_info(payment, settings=None, banks=None, method=None):
    settings = settings or get_settings()
    payment = dict(payment or {})
    method = method or method_row(payment.get("method_id"), payment.get("method"))
    kind = infer_kind(payment.get("method"), payment.get("kind") or (method or {}).get("kind"))
    target = pay_target(method or {"name": payment.get("method"), "kind": kind, "pay_to": ""}, settings)
    amount = payment.get("amount")
    merchant = settings.get("pay_merchant") or settings.get("site_name") or "LIKES AUTO"
    payload = ""
    if kind == "promptpay" and target:
        payload = promptpay_payload(target, amount, merchant)
    return {
        "payment": payment,
        "method": method or {},
        "kind": kind,
        "kind_label": KIND_LABEL.get(kind, kind),
        "target": target,
        "payload": payload,
        "banks": banks or [],
        "ref_code": payment.get("ref_code") or "",
        "amount": amount,
    }


def sniff_slip_ext(raw, filename=""):
    name = Path(str(filename or "")).name.lower()
    ext = Path(name).suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    blob = raw or b""
    if blob[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return ".webp"
    if blob[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if blob[:4] == b"%PDF":
        return ".pdf"
    if ext in SLIP_OK:
        return ext
    return ""


def save_slip_bytes(raw, pid, filename=""):
    if raw is None:
        return None, "file_read"
    if len(raw) > SLIP_MAX:
        return None, "file_size"
    if len(raw) < 32:
        return None, "file_bad"
    ext = sniff_slip_ext(raw, filename)
    if ext not in SLIP_OK:
        return None, "file_type"
    SLIP_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(raw + str(pid).encode() + os.urandom(4)).hexdigest()[:16]
    name = "p%s_%s%s" % (pid, digest, ext)
    dest = SLIP_DIR / name
    dest.write_bytes(raw)
    return "/static/uploads/slips/" + name, None


def save_slip_file(upload, pid):
    filename = Path(getattr(upload, "filename", "") or "").name
    raw = None
    if hasattr(upload, "file") and upload.file is not None:
        raw = upload.file.read()
    return save_slip_bytes(raw, pid, filename)


def attach_slip(pid, username, path, note=""):
    con = connect()
    row = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not row or row["client"] != username or row["status"] != "pending":
        con.close()
        return False
    con.execute(
        "UPDATE payments SET slip=?, note=? WHERE id=?",
        (path or row["slip"], (note or row["note"] or "").strip(), pid),
    )
    con.commit()
    con.close()
    return True


def set_pay_note(pid, note=""):
    con = connect()
    con.execute("UPDATE payments SET note=? WHERE id=?", ((note or "").strip(), pid))
    con.commit()
    con.close()


def cancel_own_payment(pid, username):
    con = connect()
    row = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not row or row["client"] != username or row["status"] != "pending":
        con.close()
        return False
    con.execute("UPDATE payments SET status='canceled' WHERE id=?", (pid,))
    con.commit()
    con.close()
    return True


def new_reset_token(email):
    token = secrets.token_urlsafe(24)
    con = connect()
    con.execute(
        "INSERT INTO reset_tokens (email, token, used, created_at) VALUES (?,?,0,?)",
        (email, token, now()),
    )
    con.commit()
    con.close()
    return token


def use_reset_token(token):
    con = connect()
    row = con.execute("SELECT * FROM reset_tokens WHERE token=? AND used=0", (token,)).fetchone()
    if not row:
        con.close()
        return None
    from datetime import datetime
    created = str(row["created_at"] or "")
    try:
        ts = datetime.strptime(created[:16], "%Y-%m-%d %H:%M")
        if (datetime.now() - ts).total_seconds() > 3600 * 6:
            con.close()
            return None
    except Exception:
        pass
    con.execute("UPDATE reset_tokens SET used=1 WHERE id=?", (row["id"],))
    con.commit()
    con.close()
    return dict(row)


def qr_png_bytes(payload: str) -> bytes:
    import io
    import segno
    qr = segno.make(str(payload or ""), error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=8, border=2, dark="#14081f", light="#ffffff")
    return buf.getvalue()

def parse_incoming_amounts(text):
    from inbound import parse_incoming_amounts as parse
    return parse(text)


def pay_notify_token():
    from db import save_settings
    s = get_settings()
    tok = str(s.get("pay_notify_token") or "").strip()
    if len(tok) < 16:
        tok = secrets.token_hex(16)
        save_settings({"pay_notify_token": tok})
    return tok


def _satang(value):
    try:
        return int(round(float(value) * 100))
    except (TypeError, ValueError):
        return 0


def credit_by_incoming(amount, source="match"):
    from db import add_log, approve_payment
    try:
        amt = round(float(amount), 2)
    except (TypeError, ValueError):
        return None, "bad_amount"
    if amt < 1:
        return None, "bad_amount"
    settings = get_settings()
    if source not in ("admin", "oiio", "confirm") and str(settings.get("auto_approve_slip") or "1") == "0":
        return None, "off"
    want = _satang(amt)
    con = connect()
    rows = con.execute("SELECT id, amount FROM payments WHERE status='pending' ORDER BY id DESC").fetchall()
    con.close()
    pending = []
    for row in rows:
        sat = _satang(row["amount"])
        if sat >= 100:
            pending.append((int(row["id"]), sat))
    hits = [pid for pid, sat in pending if sat == want]
    if not hits and want % 100 == 0:
        bucket = [pid for pid, sat in pending if sat // 100 == want // 100]
        if len(bucket) == 1:
            hits = bucket
    if not hits:
        return None, "none"
    if len(hits) > 1:
        return None, "ambiguous"
    pid = hits[0]
    if not approve_payment(pid):
        return None, "approve"
    add_log("auto credit #%s %.2f %s" % (pid, amt, source), "-")
    return pid, "paid"
