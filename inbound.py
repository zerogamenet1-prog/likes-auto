import json
import re
import urllib.parse
import urllib.request

from db import connect, now

SITE_URL = "https://likes-auto.com"
AMT_RE = re.compile(r"(?<![\d])(\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2}|\d{1,7},\d{2})(?![\d])")
AMT = r"(?:\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2}|\d{1,7},\d{2})"
IN_WORDS = (
    "\u0e23\u0e31\u0e1a\u0e42\u0e2d\u0e19|\u0e42\u0e2d\u0e19\u0e40\u0e02\u0e49\u0e32|\u0e40\u0e07\u0e34\u0e19\u0e40\u0e02\u0e49\u0e32|"
    "\u0e44\u0e14\u0e49\u0e23\u0e31\u0e1a|\u0e40\u0e07\u0e34\u0e19\u0e40\u0e02\u0e49\u0e32\u0e1a\u0e0a|\u0e42\u0e2d\u0e19\u0e40\u0e07\u0e34\u0e19\u0e40\u0e02\u0e49\u0e32|"
    "received|credited|promptpay|\u0e1e\u0e23\u0e49\u0e2d\u0e21\u0e40\u0e1e\u0e22\u0e4c"
)
OUT_WORDS = (
    "\u0e2b\u0e31\u0e01\u0e1a\u0e0a|\u0e2b\u0e31\u0e01\u0e1a\u0e31\u0e0d\u0e0a\u0e35|\u0e40\u0e07\u0e34\u0e19\u0e2d\u0e2d\u0e01|"
    "\u0e42\u0e2d\u0e19\u0e2d\u0e2d\u0e01|\u0e15\u0e31\u0e14\u0e1a\u0e31\u0e0d\u0e0a\u0e35|\u0e0a\u0e33\u0e23\u0e30\u0e1a\u0e34\u0e25|"
    "withdrawn|debited|paid to"
)
BAL_WORDS = (
    "\u0e04\u0e07\u0e40\u0e2b\u0e25\u0e37\u0e2d|\u0e22\u0e2d\u0e14\u0e04\u0e07\u0e40\u0e2b\u0e25\u0e37\u0e2d|"
    "\u0e22\u0e2d\u0e14\u0e04\u0e07\u0e40\u0e2b\u0e25\u0e37\u0e2d|available|balance|\u0e40\u0e2b\u0e25\u0e37\u0e2d"
)
IN_RE = re.compile(r"(" + IN_WORDS + r")[^\d]{0,80}(" + AMT + r")", re.I)
OUT_RE = re.compile(r"(" + OUT_WORDS + r")", re.I)
BAL_RE = re.compile(r"(" + BAL_WORDS + r")[^\d]{0,16}(" + AMT + r")", re.I)
QTY_RE = re.compile(r"(?:\+|\u0e08\u0e33\u0e19\u0e27\u0e19)\s*(" + AMT + r")", re.I)
BANK_SENDERS = (
    "kbank", "scb", "ktb", "bbl", "bay", "ttb", "gsb", "baac", "kkp", "cimb", "uob",
    "lhbank", "tmb", "krungsri", "krungthai", "krung thai", "bangkok", "promptpay", "truemoney",
    "ghb", "tisco", "thanachart", "kkbank", "\u0e01\u0e23\u0e38\u0e07\u0e44\u0e17\u0e22",
)
KRUNGTHAI_SENDERS = (
    "krungthai", "krung thai", "ktb", "\u0e01\u0e23\u0e38\u0e07\u0e44\u0e17\u0e22",
)


def migrate():
    con = connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS pay_inbounds ("
        "id INTEGER PRIMARY KEY, source TEXT, raw TEXT, amount REAL, "
        "payment_id INTEGER, result TEXT, created_at TEXT)"
    )
    con.commit()
    con.close()


def to_amount(raw):
    text = str(raw or "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        amt = round(float(text), 2)
    except ValueError:
        return 0.0
    if amt < 1:
        return 0.0
    return amt


def is_bank_sender(sender):
    text = str(sender or "").lower()
    return any(name in text for name in BANK_SENDERS)


def is_krungthai_sender(sender):
    text = str(sender or "").lower()
    return any(name in text for name in KRUNGTHAI_SENDERS)


def sms_direction(text):
    blob = str(text or "")
    has_in = bool(IN_RE.search(blob) or re.search(IN_WORDS, blob, re.I))
    has_out = bool(OUT_RE.search(blob))
    if has_out and not has_in:
        return "out"
    if has_in and not has_out:
        return "in"
    if has_out:
        return "out"
    if has_in:
        return "in"
    return "unknown"


def parse_incoming_amounts(text):
    blob = str(text or "")
    skip = set()
    for match in BAL_RE.finditer(blob):
        amt = to_amount(match.group(2))
        if amt:
            skip.add(amt)
    preferred = []
    for match in IN_RE.finditer(blob):
        amt = to_amount(match.group(2))
        if amt and amt not in skip and amt not in preferred:
            preferred.append(amt)
    for match in QTY_RE.finditer(blob):
        amt = to_amount(match.group(1))
        if amt and amt not in skip and amt not in preferred:
            preferred.append(amt)
    found = list(preferred)
    for raw in AMT_RE.findall(blob):
        amt = to_amount(raw)
        if amt and amt not in skip and amt not in found:
            found.append(amt)
    try:
        direct = round(float(blob.replace(",", ".")), 2)
        if direct >= 1 and direct not in skip and direct not in found:
            found.insert(0, direct)
    except ValueError:
        pass
    satang = [amt for amt in found if int(round(amt * 100)) % 100]
    if satang:
        return satang + [amt for amt in found if amt not in satang]
    return found


def log_inbound(source, raw, amount, payment_id, result):
    migrate()
    con = connect()
    con.execute(
        "INSERT INTO pay_inbounds (source, raw, amount, payment_id, result, created_at) VALUES (?,?,?,?,?,?)",
        (source, str(raw or "")[:800], amount, payment_id, result, now()),
    )
    con.commit()
    con.close()


def list_inbounds(limit=20):
    migrate()
    con = connect()
    rows = con.execute("SELECT * FROM pay_inbounds ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    con.close()
    return [dict(row) for row in rows]


def process_inbound(text="", amount="", source="notify", sender=""):
    return None, None, "disabled"


def set_telegram_webhook(bot_token, secret):
    token = str(bot_token or "").strip()
    if not token:
        return False
    hook = "%s/internal/pay/tg?token=%s" % (SITE_URL, urllib.parse.quote(secret))
    url = "https://api.telegram.org/bot%s/setWebhook" % token
    body = urllib.parse.urlencode({"url": hook, "secret_token": secret}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace") or "{}")
        return bool(data.get("ok"))
    except Exception:
        return False


def telegram_text(payload):
    if not isinstance(payload, dict):
        return ""
    msg = payload.get("message") or payload.get("edited_message") or payload.get("channel_post") or {}
    if not isinstance(msg, dict):
        return ""
    return str(msg.get("text") or msg.get("caption") or "")