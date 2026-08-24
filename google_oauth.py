import json
import os
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request

from content import SITE
from db import connect, create_client, get_client, get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
REDIRECT_PATH = "/google-login"

MSG = {
    "no_email": "ไม่พบอีเมลจากบัญชี Google",
    "unverified": "อีเมล Google ยังไม่ได้ยืนยัน",
    "disabled": "บัญชีถูกปิดใช้งาน กรุณาติดต่อผู้ดูแลระบบ",
    "closed": "ปิดรับสมัครชั่วคราว",
    "create_fail": "สมัครด้วย Google ไม่สำเร็จ",
    "canceled": "ยกเลิกการเข้าสู่ระบบด้วย Google",
    "off": "ปิดเข้าสู่ระบบด้วย Google ชั่วคราว",
    "not_ready": "ยังไม่ได้ตั้งค่า Google ในแอดมิน > ตั้งค่า > เชื่อมต่อ",
    "bad_state": "การยืนยัน Google ไม่ถูกต้อง กรุณาลองใหม่",
    "mismatch": "Redirect URI ไม่ตรงกับที่ใส่ใน Google Cloud Console",
    "bad_client": "Client ID หรือ Client Secret ไม่ถูกต้อง",
    "expired": "รหัสจาก Google หมดอายุ กรุณาลองใหม่",
    "fail": "เชื่อมต่อ Google ไม่สำเร็จ กรุณาลองใหม่",
}


def google_creds(settings=None):
    s = settings or get_settings()
    cid = (s.get("google_client_id") or os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    secret = (s.get("google_client_secret") or os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    return cid, secret


def google_on(settings=None):
    s = settings or get_settings()
    return str(s.get("google_login") or "0") != "0"


def google_ready(settings=None):
    s = settings or get_settings()
    cid, secret = google_creds(s)
    return google_on(s) and bool(cid and secret)


def _origin(url):
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return "%s://%s" % (parsed.scheme, parsed.netloc)


def google_origins():
    base = SITE["url"].rstrip("/")
    host = urllib.parse.urlparse(base).netloc
    items = [base]
    if host.startswith("www."):
        items.append(base.replace("://www.", "://", 1))
    else:
        items.append(base.replace("://", "://www.", 1))
    out = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out


def google_redirects():
    return [item + REDIRECT_PATH for item in google_origins()]


def google_redirect_uri(request=None):
    return SITE["url"].rstrip("/") + REDIRECT_PATH


def google_status(settings=None):
    s = settings or get_settings()
    cid, secret = google_creds(s)
    on = google_on(s)
    return {
        "on": on,
        "ready": on and bool(cid and secret),
        "has_id": bool(cid),
        "has_secret": bool(secret),
        "client_id": cid,
        "redirects": google_redirects(),
        "origins": google_origins(),
    }


def safe_next(value, fallback="/neworder"):
    raw = urllib.parse.unquote((value or "").strip())
    if not raw.startswith("/") or raw.startswith("//") or "://" in raw:
        return fallback
    path = raw.split("?")[0].split("#")[0]
    if path in ("", "/", "/signin", "/signup", "/google-login") or path.startswith("/admin"):
        return fallback
    return path[:180] or fallback


def google_error_message(code):
    key = str(code or "").strip()
    if key in ("access_denied", "canceled"):
        return MSG["canceled"]
    if "redirect_uri" in key:
        return MSG["mismatch"]
    if key in ("invalid_client", "google_http_401"):
        return MSG["bad_client"]
    if key in ("google_http_400", "invalid_grant", "expired"):
        return MSG["expired"]
    return MSG.get(key) or MSG["fail"]


def new_state():
    return secrets.token_urlsafe(24)


def google_auth_url(state, redirect_uri=None):
    cid, _ = google_creds()
    query = urllib.parse.urlencode(
        {
            "client_id": cid,
            "redirect_uri": redirect_uri or google_redirect_uri(),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
            "include_granted_scopes": "true",
        }
    )
    return AUTH_URL + "?" + query


def _json_request(url, data=None, headers=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    hdrs = {"Accept": "application/json"}
    if data is not None:
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=body, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = ""
        try:
            raw = exc.read().decode("utf-8", "replace")[:400]
        except Exception:
            raw = ""
        low = raw.lower()
        if "redirect_uri" in low:
            raise RuntimeError("redirect_uri_mismatch") from exc
        if exc.code == 401 or "invalid_client" in low:
            raise RuntimeError("invalid_client") from exc
        if "invalid_grant" in low:
            raise RuntimeError("invalid_grant") from exc
        raise RuntimeError("google_http_%s" % exc.code) from exc


def google_profile(code, redirect_uri=None):
    cid, secret = google_creds()
    token = _json_request(
        TOKEN_URL,
        {
            "code": code,
            "client_id": cid,
            "client_secret": secret,
            "redirect_uri": redirect_uri or google_redirect_uri(),
            "grant_type": "authorization_code",
        },
    )
    access = token.get("access_token")
    if not access:
        raise RuntimeError("no_access_token")
    return _json_request(USERINFO_URL, headers={"Authorization": "Bearer " + access})


def _unique_username(email):
    base = re.sub(r"[^a-z0-9]", "", (email.split("@")[0] or "").lower()) or "guser"
    base = base[:18]
    con = connect()
    name = base
    n = 0
    while con.execute("SELECT id FROM clients WHERE username=?", (name,)).fetchone():
        n += 1
        name = "%s%s" % (base[:14], n)
    con.close()
    return name


def login_or_create_google(profile):
    email = str(profile.get("email") or "").strip().lower()
    gid = str(profile.get("sub") or "").strip()
    verified = profile.get("email_verified")
    if not email or not gid:
        return None, MSG["no_email"]
    if verified in (False, "false", "False"):
        return None, MSG["unverified"]

    con = connect()
    row = con.execute("SELECT * FROM clients WHERE google_id=?", (gid,)).fetchone()
    if not row:
        row = con.execute("SELECT * FROM clients WHERE lower(email)=?", (email,)).fetchone()
        if row:
            con.execute("UPDATE clients SET google_id=? WHERE id=?", (gid, row["id"]))
            con.commit()
    if row:
        if str(row["status"] or "active") != "active":
            con.close()
            return None, MSG["disabled"]
        cid = row["id"]
        con.close()
        return get_client(client_id=cid), None
    con.close()

    settings = get_settings()
    if str(settings.get("registration_page") or "1") == "0":
        return None, MSG["closed"]

    user, err = create_client(_unique_username(email), email, secrets.token_urlsafe(18))
    if err or not user:
        return None, err or MSG["create_fail"]
    con = connect()
    con.execute("UPDATE clients SET google_id=? WHERE id=?", (gid, user["id"]))
    con.commit()
    con.close()
    return get_client(client_id=user["id"]), None
