import hmac
import secrets
import threading
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse, Response

_lock = threading.Lock()
_hits = defaultdict(list)
_fails = defaultdict(int)
_lock_until = {}

ADMIN_FAILS = 5
ADMIN_LOCK = 30 * 60
USER_FAILS = 8
USER_LOCK = 20 * 60
ADMIN_IDLE = 4 * 60 * 60
SKIP_CSRF = (
    "/api/v2",
    "/internal/",
    "/google-login",
    "/css/",
    "/assets/",
    "/static/",
    "/health",
)


def client_ip(request):
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded[:80]
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


def _prune(bucket, window):
    now = time.time()
    keep = [t for t in bucket if now - t < window]
    bucket[:] = keep
    return len(keep)


def too_many(scope, ip, limit, window):
    key = "%s:%s" % (scope, ip)
    now = time.time()
    with _lock:
        bucket = _hits[key]
        n = _prune(bucket, window)
        if n >= limit:
            return True
        bucket.append(now)
        return False


def locked(scope, ip):
    key = "%s:%s" % (scope, ip)
    with _lock:
        until = _lock_until.get(key) or 0
        return time.time() < until


def lock_left(scope, ip):
    key = "%s:%s" % (scope, ip)
    with _lock:
        until = _lock_until.get(key) or 0
        left = int(until - time.time())
        return max(0, left)


def note_fail(scope, ip, limit, lock_secs):
    key = "%s:%s" % (scope, ip)
    with _lock:
        _fails[key] = _fails.get(key, 0) + 1
        if _fails[key] >= limit:
            _lock_until[key] = time.time() + lock_secs
            _fails[key] = 0


def note_ok(scope, ip):
    key = "%s:%s" % (scope, ip)
    with _lock:
        _fails.pop(key, None)
        _lock_until.pop(key, None)


def ensure_csrf(request):
    tok = request.session.get("_csrf")
    if not tok:
        tok = secrets.token_urlsafe(32)
        request.session["_csrf"] = tok
    return tok


def csrf_ok(request, token):
    saved = request.session.get("_csrf") or ""
    got = (token or "").strip()
    if not saved or not got or len(saved) != len(got):
        return False
    return hmac.compare_digest(saved, got)


def honeypot_filled(form):
    if form is None:
        return False
    for name in ("la_hp_x9", "fax_number"):
        val = str(form.get(name) or "").strip()
        if val:
            return True
    return False


def admin_ip_allowed(request, settings=None):
    try:
        if settings is None:
            from db import get_settings
            settings = get_settings()
        raw = str((settings or {}).get("admin_allow_ips") or "").strip()
    except Exception:
        raw = ""
    if not raw:
        return True
    ip = client_ip(request)
    allowed = [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]
    return ip in allowed


def admin_session_ok(request):
    if not request.session.get("admin"):
        return False
    started = float(request.session.get("admin_at") or 0)
    if started and (time.time() - started) > ADMIN_IDLE:
        request.session.pop("admin", None)
        request.session.pop("admin_at", None)
        return False
    request.session["admin_at"] = time.time()
    return True


def login_block(scope, request, fails, lock_secs):
    ip = client_ip(request)
    if locked(scope, ip):
        return "พยายามเข้าสู่ระบบบ่อยเกินไป กรุณารอสักครู่แล้วลองใหม่"
    return ""


def mark_login(scope, request, ok, fails, lock_secs):
    ip = client_ip(request)
    if ok:
        note_ok(scope, ip)
    else:
        note_fail(scope, ip, fails, lock_secs)


def _skip_csrf(path):
    if path == "/api/v2":
        return True
    for prefix in SKIP_CSRF:
        if path.startswith(prefix):
            return True
    return False


def _need_csrf(path, method):
    if method not in ("POST", "PUT", "PATCH", "DELETE"):
        return False
    if _skip_csrf(path):
        return False
    if path.startswith("/admin"):
        return True
    if path in ("/signin", "/signup", "/forgot", "/reset", "/neworder"):
        return True
    for prefix in ("/account", "/tickets", "/addfunds", "/orders/", "/dripfeeds", "/subscriptions", "/panels", "/affiliates"):
        if path.startswith(prefix):
            return True
    return False


def security_headers(response, path):
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
    if path.startswith("/admin") or path.startswith("/account") or path.startswith("/neworder"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    if path.startswith("/admin"):
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:; "
            "img-src 'self' data: blob: https:; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'",
        )
    return response


def _deny(request, status=403, text="ไม่สามารถทำรายการได้"):
    path = request.url.path or ""
    accept = (request.headers.get("accept") or "").lower()
    if path.startswith("/api") or "application/json" in accept:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=status)
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;padding:40px;background:#070512;color:#fff'>"
        "<h1>%s</h1><p><a href='/' style='color:#c4b5fd'>กลับหน้าแรก</a></p></body></html>" % text,
        status_code=status,
    )


class GuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path or "/"
        ip = client_ip(request)
        method = request.method.upper()

        if path.startswith("/admin") and not admin_ip_allowed(request):
            return _deny(request, 404, "ไม่พบหน้านี้")

        if path.startswith("/admin/login") and too_many("admin_login_hit", ip, 40, 60):
            return _deny(request, 429, "พยายามบ่อยเกินไป")

        if path == "/signin" and method == "POST" and too_many("signin_hit", ip, 30, 60):
            return _deny(request, 429, "พยายามบ่อยเกินไป")

        if path == "/signup" and method == "POST" and too_many("signup_hit", ip, 8, 3600):
            return _deny(request, 429, "สมัครบ่อยเกินไป กรุณารอสักครู่")

        if path == "/forgot" and method == "POST" and too_many("forgot_hit", ip, 6, 3600):
            return _deny(request, 429, "ขอรีเซ็ตบ่อยเกินไป")

        if path == "/api/v2" and too_many("api_hit", ip, 80, 60):
            return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

        response = await call_next(request)
        return security_headers(response, path)
