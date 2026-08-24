import hashlib
import io
import re
import sqlite3
from datetime import datetime, timedelta, timezone

from db import ROOT, add_log, approve_payment, connect, get_settings, now
from pay import get_payment, infer_kind, method_row, normalize_promptpay, pay_target, promptpay_payload


TZ_BKK = timezone(timedelta(hours=7))
MIN_REF = 8
MAX_TRIES = 20
SLIP_BEFORE_PAY_SEC = 20 * 60
SLIP_AFTER_PAY_SEC = 48 * 60 * 60
FUTURE_SLACK_SEC = 8 * 60


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def amounts_match(expected, actual):
    return abs(_num(expected) - _num(actual)) <= 0.009


def slip_api_ready(settings=None):
    s = settings or get_settings()
    return str(s.get("auto_approve_slip") or "1") != "0"


def parse_tlv(data):
    out = {}
    i = 0
    text = str(data or "")
    while i + 4 <= len(text):
        tag = text[i : i + 2]
        try:
            ln = int(text[i + 2 : i + 4])
        except ValueError:
            break
        val = text[i + 4 : i + 4 + ln]
        if len(val) != ln:
            break
        out[tag] = val
        i += 4 + ln
    return out


def payload_amount(text):
    blob = str(text or "")
    tlv = parse_tlv(blob)
    if "54" in tlv:
        return _num(tlv.get("54"))
    found = re.findall(r"54(\d{2})(\d+\.\d{2})", blob)
    for ln, amt in found:
        if int(ln) == len(amt):
            return _num(amt)
    return 0.0


def payload_ref(text):
    blob = str(text or "")
    extra = parse_tlv(parse_tlv(blob).get("62") or "")
    for key in ("05", "07", "01", "02"):
        val = (extra.get(key) or "").strip()
        if len(val) >= MIN_REF:
            return val
    m = re.search(r"[A-Z0-9]{18,}", blob)
    if m:
        return m.group(0)
    return ""


def strip_crc(text):
    blob = str(text or "").strip()
    idx = blob.rfind("6304")
    if idx >= 12:
        return blob[:idx]
    return blob


def emv_crc_ok(text):
    blob = str(text or "").strip()
    idx = blob.rfind("6304")
    if idx < 12 or idx + 8 != len(blob):
        return False
    from pay import crc16_ccitt

    try:
        return crc16_ccitt(blob[: idx + 4]).upper() == blob[-4:].upper()
    except Exception:
        return False


def our_receive_payload(pay, settings=None):
    settings = settings or get_settings()
    method = method_row(pay.get("method_id"), pay.get("method"))
    kind = infer_kind(pay.get("method"), pay.get("kind") or (method or {}).get("kind"))
    if kind != "promptpay":
        return ""
    target = pay_target(method or {"name": pay.get("method"), "kind": kind, "pay_to": ""}, settings)
    merchant = settings.get("pay_merchant") or settings.get("site_name") or "LIKES AUTO"
    return promptpay_payload(target, pay.get("amount"), merchant)


def is_our_receive_qr(text, ours):
    if not ours or not text:
        return False
    if str(text).strip() == str(ours).strip():
        return True
    return strip_crc(text) == strip_crc(ours)


def is_promptpay_presentment(text):
    blob = str(text or "")
    if "A000000677010112" in blob:
        return False
    return "A000000677010111" in blob


def is_transfer_slip_qr(text):
    blob = str(text or "").strip()
    if len(blob) < 24:
        return False
    if is_promptpay_presentment(blob):
        return False
    if "A000000677010112" in blob:
        return True
    tlv = parse_tlv(blob)
    extra = parse_tlv(tlv.get("62") or "")
    if any(len((extra.get(key) or "").strip()) >= MIN_REF for key in ("05", "07", "01", "02")):
        return blob.startswith("000201")
    return False


def _digits(value):
    return re.sub(r"\D", "", str(value or ""))


def our_account_ids(pay, settings=None):
    settings = settings or get_settings()
    method = method_row(pay.get("method_id"), pay.get("method"))
    found = []
    for src in (pay_target(method or {}, settings), settings.get("promptpay"), (method or {}).get("pay_to")):
        raw = _digits(src)
        if len(raw) < 9:
            continue
        for item in (raw, normalize_promptpay(src)):
            if item and item not in found:
                found.append(item)
        if raw.startswith("0") and len(raw) == 10:
            alt = "66" + raw[1:]
            if alt not in found:
                found.append(alt)
        if raw.startswith("66") and len(raw) == 11:
            alt = "0" + raw[2:]
            if alt not in found:
                found.append(alt)
    return found


def payload_destinations(text):
    found = []

    def walk(blob, depth=0):
        if depth > 4 or not blob:
            return
        tlv = parse_tlv(blob)
        if not tlv:
            return
        for tag, val in tlv.items():
            if tag in ("00", "51", "52", "53", "54", "58", "59", "60", "63", "91"):
                if tag == "00" and depth > 0:
                    continue
                if tag != "00":
                    continue
            digits = _digits(val)
            if "000000677010" in digits:
                continue
            if len(digits) in (10, 13) or (len(digits) == 11 and digits.startswith("66")):
                if digits not in found:
                    found.append(digits)
            if len(val) >= 8:
                walk(val, depth + 1)

    walk(str(text or ""))
    return found


def _receiver_visible(info):
    rec = ((info or {}).get("receiver") or {}).get("account") or {}
    out = []
    proxy = rec.get("proxy") or {}
    bank = rec.get("bank") or {}
    for item in (proxy.get("account"), bank.get("account"), info.get("receiver_id")):
        if item:
            out.append(str(item))
    return out


def _account_forms(our):
    forms = []
    raw = _digits(our)
    if not raw:
        return forms
    for item in (raw, normalize_promptpay(raw)):
        if item and item not in forms:
            forms.append(item)
    if raw.startswith("0") and len(raw) == 10:
        for item in ("66" + raw[1:], "0066" + raw[1:]):
            if item not in forms:
                forms.append(item)
    if raw.startswith("66") and len(raw) == 11:
        for item in ("0" + raw[2:], "00" + raw):
            if item not in forms:
                forms.append(item)
    if raw.startswith("0066") and len(raw) == 13:
        for item in ("0" + raw[4:], raw[2:]):
            if item not in forms:
                forms.append(item)
    return forms


def _mask_fits(mask, our):
    cleaned = re.sub(r"[^0-9xX*]", "", str(mask or ""))
    vis = _digits(cleaned)
    if len(vis) < 4:
        return False
    forms = _account_forms(our)
    if not forms:
        return False
    pat = "".join(r"\d" if ch in "xX*" else re.escape(ch) for ch in cleaned)
    try:
        rx = re.compile("^" + pat + "$")
    except re.error:
        rx = None
    for form in forms:
        if rx and rx.match(form):
            return True
        if rx and len(form) >= len(cleaned) and rx.match(form[-len(cleaned) :]):
            return True
        if len(vis) >= 6 and vis in form:
            return True
    lead = re.match(r"\d+", cleaned)
    tail = re.search(r"\d+$", cleaned)
    if lead and tail:
        a, b = lead.group(), tail.group()
        if a != b and len(a) + len(b) >= 4:
            for form in forms:
                hidden = len(form) - len(a) - len(b)
                if hidden >= 3 and form.startswith(a) and form.endswith(b):
                    return True
    return False


def ids_match(left, right):
    a, b = _digits(left), _digits(right)
    if len(a) < 9 or len(b) < 9:
        return False
    if a == b:
        return True
    return bool(set(_account_forms(a)).intersection(_account_forms(b)))


def receiver_verdict(info, pay, payload=""):
    ours = our_account_ids(pay)
    if not ours:
        return "unknown"
    cands = []
    for item in _receiver_visible(info):
        if str(item or "").strip():
            cands.append(str(item))
    blob = payload or (info or {}).get("payload") or ""
    if is_transfer_slip_qr(blob):
        cands.extend(payload_destinations(blob))
    if any(ids_match(cand, our) or _mask_fits(cand, our) for cand in cands for our in ours):
        return "match"
    for cand in cands:
        digits = _digits(cand)
        masked = bool(re.search(r"[xX*]", cand))
        if masked:
            continue
        if len(digits) in (10, 13) or (len(digits) == 11 and digits.startswith("66")):
            if not any(ids_match(digits, our) for our in ours):
                return "other"
    return "unknown"


def receiver_matches_us(info, pay, payload=""):
    return receiver_verdict(info, pay, payload) == "match"


def parse_slip_dt(value):
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is not None:
            dt = dt.astimezone(TZ_BKK).replace(tzinfo=None)
        return dt
    except ValueError:
        pass
    for fmt, size in (
        ("%Y-%m-%d %H:%M:%S", 19),
        ("%Y-%m-%d %H:%M", 16),
        ("%Y%m%d%H%M%S", 14),
        ("%d/%m/%Y %H:%M:%S", 19),
        ("%d/%m/%Y %H:%M", 16),
    ):
        try:
            return datetime.strptime(text[:size], fmt)
        except ValueError:
            continue
    return None


def slip_time_ok(info, pay):
    dt = parse_slip_dt((info or {}).get("date"))
    if not dt:
        return True
    created = parse_slip_dt(pay.get("created_at")) or datetime.now()
    now_dt = datetime.now()
    if dt > now_dt + timedelta(seconds=FUTURE_SLACK_SEC):
        return False
    if dt < created - timedelta(seconds=SLIP_BEFORE_PAY_SEC):
        return False
    if dt > created + timedelta(seconds=SLIP_AFTER_PAY_SEC):
        return False
    return True


def _slip_amount(info):
    amt = (info or {}).get("amount")
    if isinstance(amt, dict):
        return _num(amt.get("amount"))
    if (info or {}).get("amountInSlip") not in (None, ""):
        return _num(info.get("amountInSlip"))
    return _num(amt)


def normalize_bank_info(info, payload=""):
    info = dict(info or {})
    raw = info.get("rawSlip")
    if isinstance(raw, dict):
        merged = dict(raw)
        for key in ("transRef", "date", "amount", "receiver", "isDuplicate", "amountInSlip"):
            if info.get(key) not in (None, ""):
                merged[key] = info.get(key)
        info = merged
    trans = str(info.get("transRef") or info.get("ref") or info.get("trans_ref") or "").strip()
    recv = info.get("receiver") if isinstance(info.get("receiver"), dict) else {}
    if info.get("receiver_id") or info.get("receiver_name"):
        recv = {
            "account": {
                "name": {"th": info.get("receiver_name") or ""},
                "bank": {"account": info.get("receiver_id") or ""},
                "proxy": {"account": info.get("receiver_id") or ""},
            }
        }
    return {
        "transRef": trans,
        "date": info.get("date") or info.get("transDate") or "",
        "amount": info.get("amountInSlip") if info.get("amountInSlip") not in (None, "") else info.get("amount"),
        "receiver": recv,
        "payload": info.get("payload") or payload,
        "isDuplicate": bool(info.get("isDuplicate")),
        "receiver_id": info.get("receiver_id") or "",
        "verified": bool(info.get("verified")),
    }


def _ensure_tables(con):
    con.executescript(
        """
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


def too_many_tries(pid):
    con = connect()
    _ensure_tables(con)
    cutoff = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    n = con.execute(
        "SELECT COUNT(*) AS c FROM slip_tries WHERE payment_id=? AND created_at>=?",
        (int(pid), cutoff),
    ).fetchone()["c"]
    con.execute(
        "INSERT INTO slip_tries (payment_id, created_at) VALUES (?,?)",
        (int(pid), now()),
    )
    con.commit()
    con.close()
    return int(n or 0) >= MAX_TRIES


def trans_ref_used(trans_ref, pid=None):
    if not trans_ref:
        return False
    con = connect()
    _ensure_tables(con)
    row = con.execute("SELECT payment_id FROM slip_refs WHERE trans_ref=?", (trans_ref,)).fetchone()
    if row and (pid is None or int(row["payment_id"] or 0) != int(pid)):
        con.close()
        return True
    row = con.execute("SELECT id FROM payments WHERE trans_ref=? AND id!=?", (trans_ref, pid or 0)).fetchone()
    con.close()
    return bool(row)


def save_trans_ref(pid, trans_ref):
    ok, _code = claim_trans_ref(pid, trans_ref)
    return ok


def claim_trans_ref(pid, trans_ref):
    ref = str(trans_ref or "").strip()
    if len(ref) < MIN_REF:
        return False, "no_ref"
    con = connect()
    _ensure_tables(con)
    try:
        con.execute(
            "INSERT INTO slip_refs (trans_ref, payment_id, created_at) VALUES (?,?,?)",
            (ref, int(pid), now()),
        )
    except sqlite3.IntegrityError:
        row = con.execute("SELECT payment_id FROM slip_refs WHERE trans_ref=?", (ref,)).fetchone()
        con.close()
        if row and int(row["payment_id"] or 0) == int(pid):
            return True, None
        return False, "duplicate"
    con.execute("UPDATE payments SET trans_ref=? WHERE id=?", (ref, pid))
    con.commit()
    con.close()
    return True, None


def claim_image_hash(pid, raw):
    if not raw:
        return True, None
    digest = hashlib.sha256(raw).hexdigest()
    con = connect()
    _ensure_tables(con)
    row = con.execute("SELECT payment_id FROM slip_hashes WHERE sha256=?", (digest,)).fetchone()
    if row:
        owner = int(row["payment_id"] or 0)
        if owner == int(pid):
            con.close()
            return True, None
        other = con.execute("SELECT status FROM payments WHERE id=?", (owner,)).fetchone()
        if other and str(other["status"] or "") in ("paid", "pending"):
            con.close()
            return False, "duplicate"
        con.execute(
            "UPDATE slip_hashes SET payment_id=?, created_at=? WHERE sha256=?",
            (int(pid), now(), digest),
        )
        con.commit()
        con.close()
        return True, None
    con.execute(
        "INSERT INTO slip_hashes (sha256, payment_id, created_at) VALUES (?,?,?)",
        (digest, int(pid), now()),
    )
    con.commit()
    con.close()
    return True, None


def _credit(pid, trans_ref, source):
    ok, code = claim_trans_ref(pid, trans_ref)
    if not ok:
        return False, code or "duplicate"
    if not approve_payment(pid):
        return False, "approve"
    add_log("ตรวจสลิปในระบบ #%s %s %s" % (pid, source, trans_ref or "-"), "-")
    return True, "paid"


def credit_from_verified(pid, pay, info, source, payload=""):
    data = normalize_bank_info(info, payload)
    if data.get("isDuplicate"):
        return False, "duplicate"
    expected = _num(pay.get("amount"))
    bank_amt = _slip_amount(data)
    if not bank_amt or not amounts_match(expected, bank_amt):
        add_log("slip reject amount #%s" % pid, "-")
        return False, "amount"
    blob = data.get("payload") or payload
    verdict = receiver_verdict(data, pay, blob)
    if verdict == "other":
        add_log("slip reject receiver #%s" % pid, "-")
        return False, "receiver"
    trans_ref = str(data.get("transRef") or "").strip()
    if verdict == "unknown" and not (data.get("verified") and len(trans_ref) >= MIN_REF):
        add_log("slip reject receiver unclear #%s" % pid, "-")
        return False, "receiver_unclear"
    if not slip_time_ok(data, pay):
        add_log("slip reject time #%s" % pid, "-")
        return False, "stale"
    if len(trans_ref) < MIN_REF:
        add_log("slip reject no_ref #%s" % pid, "-")
        return False, "no_ref"
    return _credit(pid, trans_ref, source)


def _collect_qr(img, zbar_decode, texts):
    try:
        found = zbar_decode(img)
    except Exception:
        found = []
    for code in found or []:
        try:
            text = code.data.decode("utf-8", "replace").strip()
        except Exception:
            continue
        if text and text not in texts:
            texts.append(text)
    return bool(texts)


def _slip_views(im):
    from PIL import Image, ImageOps

    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    if max(im.size) > 1600:
        im = im.copy()
        im.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
    gray = ImageOps.autocontrast(im.convert("L"))
    w, h = im.size
    yield im
    yield gray
    yield im.crop((int(w * 0.55), int(h * 0.55), w, h))
    yield gray.crop((int(w * 0.55), int(h * 0.55), w, h))
    yield im.crop((int(w * 0.45), int(h * 0.62), w, h))


def decode_qr_texts(image_bytes):
    texts = []
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode
    except Exception:
        return texts
    try:
        im = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return texts
    for img in _slip_views(im):
        _collect_qr(img, zbar_decode, texts)
        if any(is_transfer_slip_qr(item) for item in texts):
            break
    return texts


def _usable_qrs(texts, ours):
    qrs = []
    saw_presentment = False
    for text in texts:
        blob = str(text or "").strip()
        if not blob:
            continue
        if is_our_receive_qr(blob, ours) or is_promptpay_presentment(blob):
            saw_presentment = True
            continue
        if blob not in qrs:
            qrs.append(blob)
    transfer = [item for item in qrs if is_transfer_slip_qr(item)]
    return (transfer or qrs), saw_presentment and not qrs


def auto_credit_from_slip(pid, image_path=None, payload="", count_try=True):
    pay = get_payment(pid)
    if not pay or pay.get("status") != "pending":
        return False, "not_pending"
    if not slip_api_ready():
        return False, "off"
    if count_try and too_many_tries(pid):
        return False, "limit"
    raw = b""
    disk = None
    if image_path:
        disk = ROOT / str(image_path).lstrip("/").replace("\\", "/")
        if disk.is_file():
            raw = disk.read_bytes()
        else:
            disk = None
    if not raw:
        return False, "no_slip"
    ok, code = claim_image_hash(pid, raw)
    if not ok:
        return False, code
    texts = decode_qr_texts(raw)
    ours = our_receive_payload(pay)
    qrs, only_presentment = _usable_qrs(texts, ours)
    if only_presentment:
        return False, "not_slip"
    last = "no_qr"
    easy_ready = False
    try:
        from easyslip import ready as easy_on
        from easyslip import verify_image, verify_payload

        easy_ready = easy_on()
    except Exception:
        verify_payload = None
        verify_image = None

    def bank_credit(info, source, blob):
        return credit_from_verified(pid, pay, info, source, blob)

    for text in qrs[:3]:
        if text.rfind("6304") >= 12 and not emv_crc_ok(text):
            last = "bad_qr"
            continue
        qr_amt = payload_amount(text)
        if qr_amt and not amounts_match(pay.get("amount"), qr_amt):
            return False, "amount"
        if easy_ready and verify_payload:
            info, err = verify_payload(text)
            if not err and info:
                paid, code = bank_credit(info, "easyslip", text)
                if paid:
                    return True, "paid"
                last = code
                if code in ("amount", "receiver", "duplicate", "stale", "no_ref"):
                    return False, code
            elif err:
                key = str(err).lower().replace("-", "_")
                if key in ("duplicate_slip", "duplicate"):
                    return False, "duplicate"
                if key in ("quota_exceeded",):
                    last = key
                elif key in ("slip_pending",):
                    last = key
                elif key not in ("timeout", "no_key", "fail", "bad_qr"):
                    last = key
        try:
            from oiio_slip import verify_transfer_qr

            info, err = verify_transfer_qr(text, pay.get("amount"))
            if not err and info:
                paid, code = bank_credit(info, "oiio", text)
                if paid:
                    return True, "paid"
                last = code
                if code in ("amount", "receiver", "duplicate", "stale", "no_ref"):
                    return False, code
            elif err:
                key = str(err).lower().replace("-", "_")
                if key in ("amount_not_verified", "amount"):
                    return False, "amount"
                last = key
        except Exception as err:
            add_log("slip oiio error #%s %s" % (pid, type(err).__name__), "-")
            if last == "no_qr":
                last = "timeout"

    if last in ("timeout", "fail", "no_qr") and raw:
        try:
            from oiio_slip import verify_transfer_image

            info, err = verify_transfer_image(raw, pay.get("amount"))
            if not err and info:
                paid, code = bank_credit(info, "oiio-img", info.get("payload") or (qrs[0] if qrs else ""))
                if paid:
                    return True, "paid"
                last = code
            elif err:
                key = str(err).lower().replace("-", "_")
                if key not in ("no_slip", "off"):
                    last = key
        except Exception as err:
            add_log("slip oiio image error #%s %s" % (pid, type(err).__name__), "-")

    if not qrs and easy_ready and disk and verify_image:
        info, err = verify_image(str(disk))
        if not err and info:
            paid, code = bank_credit(info, "easyslip-img", info.get("payload") or "")
            if paid:
                return True, "paid"
            last = code
        elif err:
            last = str(err).lower().replace("-", "_") or last

    key = str(last or "").lower().replace("-", "_")
    if key == "slip_pending":
        return False, "slip_pending"
    if key in ("slip_not_found", "qrcode_not_found"):
        return False, "no_qr"
    return False, last if last else "no_qr"


def verify_error_text(code):
    return {
        "off": "ปิดตรวจอัตโนมัติไว้ รอแอดมินอนุมัติ",
        "no_slip": "กรุณาอัปโหลดสลิปจากแอปธนาคาร",
        "no_qr": "อ่าน QR บนสลิปไม่เจอ ถ่ายให้เห็น QR ให้ชัด แล้วลองใหม่",
        "not_slip": "รูปนี้เป็น QR รับเงิน ไม่ใช่สลิปหลังโอน ถ่ายหน้าสลิปจากแอปธนาคาร",
        "amount": "ยอดในสลิปไม่ตรงกับรายการที่ต้องโอน",
        "receiver": "สลิปนี้โอนเข้าบัญชีอื่น",
        "receiver_unclear": "อ่านเลขบัญชีผู้รับไม่ชัด รอแอดมินตรวจสอบ",
        "duplicate": "สลิปนี้ถูกใช้แล้ว",
        "not_pending": "รายการนี้ตรวจแล้ว",
        "slip_pending": "ธนาคารยังไม่ยืนยันสลิป รอสักครู่แล้วแนบใหม่",
        "quota_exceeded": "ระบบตรวจสลิปเต็มโควต้า รอแอดมินตรวจสอบ",
        "timeout": "ธนาคารตอบช้า ระบบลองใหม่ให้แล้ว ถ้ายังไม่เข้าเครดิต รอแอดมินตรวจสอบ",
        "bad_qr": "QR บนสลิปไม่ถูกต้อง",
        "stale": "เวลาในสลิปไม่ตรงกับรายการนี้",
        "no_ref": "ธนาคารไม่ยืนยันเลขอ้างอิงสลิป รอแอดมินตรวจสอบ",
        "limit": "ส่งสลิปบ่อยเกินไป รอสักครู่แล้วลองใหม่",
    }.get(str(code or "").lower().replace("-", "_"), "ตรวจสลิปไม่ผ่าน รอแอดมินตรวจสอบ")
