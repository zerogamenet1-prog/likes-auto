# Thin client for the public OIIO Slip Verify API.
# Source: https://github.com/OIIOIOIIIOOOIOIO/slip-verify
# Hosted checker: https://slip-c.oiio.download
# This verifies a COMPLETED transfer QR, not our PromptPay receive QR.

import json
import time
import urllib.error
import urllib.request
import uuid

from db import get_settings
from pay import get_payment

OIIO_URL = "https://slip-c.oiio.download"
TIMEOUT = 32
TRIES = 3


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_amount(amount):
    amt = round(_num(amount), 2)
    if amt <= 0:
        return ""
    if abs(amt - int(amt)) < 0.001:
        return str(int(amt))
    return "%.2f" % amt


def _parse(status, raw):
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    if not (200 <= int(status or 0) < 300):
        slug = str(data.get("slug") or data.get("code") or data.get("error") or "")
        if int(status or 0) in (0, 408, 502, 503, 504) or not slug:
            return None, "timeout"
        return None, slug.replace("-", "_")
    info = data.get("data") if isinstance(data, dict) else None
    if not isinstance(info, dict):
        return None, "fail"
    return info, None


def _post(url, data, headers, timeout=TIMEOUT):
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        try:
            raw = err.read().decode("utf-8", "replace")
        except Exception:
            raw = ""
        return err.code, raw
    except Exception:
        return 0, ""


def _retrying(make_call):
    last = "timeout"
    for attempt in range(TRIES):
        status, raw = make_call()
        info, err = _parse(status, raw)
        if not err:
            return info, None
        last = err
        if err in ("slip_not_found", "qrcode_not_found", "amount_not_verified", "amount", "bad_qr", "off"):
            return None, err
        if attempt + 1 < TRIES:
            time.sleep(1.6 * (attempt + 1))
    return None, last


def verify_transfer_qr(qr_text, amount):
    payload = str(qr_text or "").strip()
    amt = _format_amount(amount)
    if len(payload) < 20 or not amt:
        return None, "bad_qr"
    if str(get_settings().get("oiio_slip_on") or "1") == "0":
        return None, "off"
    body = json.dumps({
        "tos": True,
        "privacy": True,
        "eula": True,
        "qrcode_data": payload,
        "qr_code_data": payload,
    }).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "likes-auto-pay/1.1",
    }

    def send():
        return _post("%s/api/slip/%s/no_slip" % (OIIO_URL, amt), body, headers)

    return _retrying(send)


def verify_transfer_image(image_bytes, amount):
    raw = image_bytes or b""
    amt = _format_amount(amount)
    if len(raw) < 32 or not amt:
        return None, "no_slip"
    if str(get_settings().get("oiio_slip_on") or "1") == "0":
        return None, "off"
    boundary = "----likesauto" + uuid.uuid4().hex
    head = (
        "--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"slip.jpg\"\r\n"
        "Content-Type: image/jpeg\r\n\r\n"
    ) % boundary
    body = head.encode("ascii") + raw + ("\r\n--%s--\r\n" % boundary).encode("ascii")
    headers = {
        "Accept": "application/json",
        "Content-Type": "multipart/form-data; boundary=" + boundary,
        "User-Agent": "likes-auto-pay/1.1",
    }

    def send():
        return _post("%s/api/slip/%s" % (OIIO_URL, amt), body, headers, timeout=40)

    return _retrying(send)


def credit_from_transfer_qr(pid, qr_text):
    from slip_verify import (
        credit_from_verified,
        is_our_receive_qr,
        is_promptpay_presentment,
        our_receive_payload,
    )

    pay = get_payment(pid)
    if not pay or pay.get("status") != "pending":
        return False, "not_pending"
    text = str(qr_text or "").strip()
    ours = our_receive_payload(pay)
    if is_our_receive_qr(text, ours) or is_promptpay_presentment(text):
        return False, "not_slip"
    info, err = verify_transfer_qr(text, pay.get("amount"))
    if err:
        return False, err
    return credit_from_verified(pid, pay, info, "oiio", text)
