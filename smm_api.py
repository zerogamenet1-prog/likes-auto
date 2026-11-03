import json
import re
import urllib.error
import urllib.parse
import urllib.request


def looks_like_masked_key(api_key: str) -> bool:
    """True for placeholder keys like **** or •••• that panels show in UI."""
    key = (api_key or "").strip()
    if not key:
        return True
    if re.fullmatch(r"[*\u2022•·xX.]{6,}", key):
        return True
    if key.lower() in {"your_api_key", "api_key", "xxxx", "null", "undefined"}:
        return True
    return False


def action(api_url, payload, timeout=60):
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("User-Agent", "LIKES-AUTO/1.0")
    req.add_header("Accept", "application/json, text/plain, */*")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        try:
            parsed = json.loads(body) if body else None
        except Exception:
            parsed = None
        if isinstance(parsed, dict) and parsed.get("error"):
            return {"error": str(parsed.get("error")), "http_status": int(exc.code)}
        msg = str(parsed.get("message") or "") if isinstance(parsed, dict) else ""
        return {
            "error": msg or ("HTTP %s: %s" % (exc.code, exc.reason)),
            "http_status": int(exc.code),
            "raw": (body or "")[:400],
        }
    except Exception as exc:
        return {"error": str(exc)}
    try:
        return json.loads(raw)
    except Exception:
        return {"error": "invalid_json", "raw": raw[:400]}


def normalize_services(result):
    if isinstance(result, list):
        return result, ""
    if isinstance(result, dict):
        if result.get("error") and not any(k in result for k in ("service", "services", "data")):
            return [], str(result.get("error"))
        for key in ("services", "data", "result"):
            if isinstance(result.get(key), list):
                return result[key], ""
        if "service" in result and "rate" in result:
            return [result], ""
    return [], "รูปแบบรายการบริการไม่ถูกต้อง"