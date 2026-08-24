import json
import urllib.error
import urllib.parse
import urllib.request


def action(api_url, payload, timeout=60):
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(api_url, data=data, method="POST")
    req.add_header("User-Agent", "LIKES-AUTO/1.0")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8", "replace")
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