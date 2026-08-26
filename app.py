import hmac
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware

from admin import router as admin_router
from api_v2 import router as api_router
from content import COPY, FAQ, LIVE_TICKER, REVIEWS, SITE
from seo import attach_seo, robots_txt, rss_xml, sitemap_xml, site_url
from cron_jobs import run_all
from google_oauth import google_on as _google_on, google_ready as _google_ready
from db import client_dash, first_open_path, get_client, get_settings, init_db, mod_on, mods_map, plat_meta as _plat_meta, public_stats, shop_nav, shop_services, stats
from th_shop import th_text
from more import router as more_router
from hub import router as hub_router
from panel import DASH_TITLES, router as panel_router
from store import list_news
from guard import GuardMiddleware, ensure_csrf

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))
templates.env.filters["th"] = th_text
# Faster Jinja on repeat renders (autoescape stays on)
try:
    templates.env.auto_reload = os.environ.get("LA_DEV") == "1"
except Exception:
    pass

_HOME_BUNDLE = {"t": 0.0, "data": None}
_HOME_BUNDLE_TTL = 45.0
_TICKER_JSON = json.dumps(LIVE_TICKER, ensure_ascii=False, separators=(",", ":"))

app = FastAPI(title="LIKES AUTO")
app.add_middleware(GuardMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "likes-auto-session-change-me"),
    same_site="lax",
    https_only=False,
    max_age=60 * 60 * 12,
)
app.add_middleware(GZipMiddleware, minimum_size=400)


@app.middleware("http")
async def seo_url_mw(request: Request, call_next):
    path = request.url.path or "/"
    host = (request.headers.get("host") or "").split(":")[0].lower()
    is_head = request.method == "HEAD"
    if is_head:
        request.scope["method"] = "GET"
    if host == "www.likes-auto.com":
        dest = site_url() + path
        if request.url.query:
            dest += "?" + request.url.query
        return RedirectResponse(dest, status_code=301)
    skip = path.startswith("/static") or path.startswith("/css") or path.startswith("/assets")
    if (not skip) and path != "/" and path.endswith("/"):
        dest = path.rstrip("/")
        if request.url.query:
            dest += "?" + request.url.query
        return RedirectResponse(dest, status_code=301)
    response = await call_next(request)
    if is_head:
        return Response(status_code=response.status_code, headers=dict(response.headers))
    path_l = path.lower()
    if path_l.endswith((".css", ".js", ".jpg", ".jpeg", ".png", ".svg", ".webp", ".woff2", ".ico")):
        response.headers.setdefault("Cache-Control", "public, max-age=604800, immutable")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


app.include_router(admin_router)
app.include_router(more_router)
app.include_router(hub_router)
app.include_router(panel_router)
app.include_router(api_router)
app.mount("/css", StaticFiles(directory=ROOT / "static" / "css"), name="css")
app.mount("/assets", StaticFiles(directory=ROOT / "static" / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.on_event("startup")
def startup():
    init_db()
    try:
        from inbound import migrate as inbound_migrate
        inbound_migrate()
        from pay import pay_notify_token
        pay_notify_token()
    except Exception:
        pass


@app.middleware("http")
async def maintenance_mw(request: Request, call_next):
    path = request.url.path
    if path.startswith("/admin") or path.startswith("/css") or path.startswith("/assets") or path.startswith("/static") or path in ("/health", "/internal/cron", "/internal/pay/in", "/internal/pay/tg"):
        return await call_next(request)
    try:
        s = get_settings()
        if str(s.get("maintenance") or "0") == "1" and not request.session.get("admin"):
            return HTMLResponse("<html><body style='background:#070512;color:#fff;font-family:sans-serif;padding:40px'><h1>ปิดปรับปรุงชั่วคราว</h1></body></html>", status_code=503)
    except Exception:
        pass
    return await call_next(request)


def current_user(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return get_client(client_id=uid)


def page(request: Request, template: str, name: str, extra=None, status_code=200):
    data = {
        "request": request,
        "site": SITE,
        "t": COPY,
        "page": name,
        "faq": FAQ if name == "faq" else [],
        "user": current_user(request),
        "catalog": [],
        "platforms": [],
        "categories": [],
        "news": list_news(5) if name == "neworder" else [],
        "settings": get_settings(),
        "google_on": _google_on(),
        "google_ready": _google_ready(),
        "menus": [],
        "error": "",
        "ok": "",
        "st": {
            "pending": "รอส่ง",
            "processing": "กำลังทำ",
            "completed": "สำเร็จ",
            "partial": "บางส่วน",
            "canceled": "ยกเลิก",
            "paid": "อนุมัติแล้ว",
            "active": "ใช้งาน",
        },
        "dash": {"orders": 0, "spent": 0},
        "dash_title": DASH_TITLES.get(name, SITE.get("name") or "Likes Auto"),
        "dash_mode": False,
        "reviews": REVIEWS,
        "csrf": "",
    }
    if extra:
        data.update(extra)
    try:
        data["csrf"] = ensure_csrf(request)
    except Exception:
        data["csrf"] = ""
    if data.get("user") and name not in ("home", "signin", "signup", "blog", "terms"):
        data["dash_mode"] = True
        data["dash"] = client_dash(data["user"]["username"])
    data["menus"] = []
    data["mods"] = mods_map(data.get("settings"))
    data["shop_home"] = first_open_path(data.get("settings"))
    data["google_on"] = _google_on(data.get("settings"))
    data["google_ready"] = _google_ready(data.get("settings"))
    try:
        from theme import public_theme_ctx
        data.update(public_theme_ctx(data.get("settings")))
    except Exception:
        data.setdefault("theme_pack", "violet")
        data.setdefault("theme_switch", True)
        data.setdefault("theme_css", "")
        data.setdefault("theme_packs", [])
    attach_seo(request, data)
    resp = templates.TemplateResponse(request, template, data, status_code=status_code)
    resp.headers["Content-Language"] = "th"
    robots = (data.get("seo") or {}).get("robots") or "index, follow"
    if "noindex" in robots:
        resp.headers["X-Robots-Tag"] = robots
    else:
        resp.headers["X-Robots-Tag"] = robots + ", max-image-preview:large, max-snippet:-1, max-video-preview:-1"
    if status_code >= 400 or name == "notfound" or data.get("user") or data.get("dash_mode"):
        resp.headers["Cache-Control"] = "no-store"
    elif name == "home":
        resp.headers["Cache-Control"] = "public, max-age=120, s-maxage=300, stale-while-revalidate=60"
    else:
        resp.headers["Cache-Control"] = "public, max-age=60, s-maxage=180"
    return resp


def _mod_gate(request: Request, key: str):
    s = get_settings()
    if mod_on(s, key):
        return None
    if request.session.get("user_id"):
        return RedirectResponse(first_open_path(s), status_code=303)
    return RedirectResponse("/", status_code=303)


def _home_plats(plats):
    merged = {}
    for row in plats:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in merged:
            merged[key]["count"] += int(row.get("count") or 0)
            if int(row.get("count") or 0) > merged[key]["_best"]:
                merged[key]["name"] = name
                merged[key]["_best"] = int(row.get("count") or 0)
                merged[key]["icon"] = row.get("icon")
                merged[key]["color"] = row.get("color")
                merged[key]["logo"] = row.get("logo")
        else:
            merged[key] = {
                "name": name,
                "count": int(row.get("count") or 0),
                "_best": int(row.get("count") or 0),
                "icon": row.get("icon"),
                "color": row.get("color"),
                "logo": row.get("logo"),
            }
    preferred_keys = (
        "instagram", "facebook", "tiktok", "youtube", "line", "twitter", "telegram", "threads", "spotify"
    )
    preferred, rest = [], []
    for key, item in merged.items():
        first = item["name"][:1]
        noisy = (
            key in {"jap", "coinmarketcap"}
            or (first and (ord(first) > 0x1F000 or 0x1F1E6 <= ord(first) <= 0x1F1FF))
        )
        if noisy:
            continue
        if any(p in key for p in preferred_keys):
            preferred.append(item)
        else:
            rest.append(item)
    preferred.sort(key=lambda x: -x["count"])
    rest.sort(key=lambda x: -x["count"])
    out = []
    for item in (preferred + rest)[:12]:
        icon, color = _plat_meta(item["name"])
        out.append({
            "name": item["name"],
            "count": item["count"],
            "icon": icon,
            "color": color,
            "logo": item.get("logo") or "/static/assets/plats/app.svg",
            "blurb": _plat_blurb(item["name"]),
        })
    return out


_PLAT_BLURB = (
    ("instagram", "ig_s"),
    ("facebook", "fb_s"),
    ("tiktok", "tt_s"),
    ("youtube", "yt_s"),
    ("twitter", "x_s"),
    ("telegram", "tg_s"),
    ("line", "line_s"),
    ("shopee", "shopee_s"),
    ("spotify", "spot_s"),
)


def _plat_blurb(name):
    key = (name or "").lower()
    for needle, ck in _PLAT_BLURB:
        if needle in key:
            return COPY.get(ck, "")
    return ""


def _home_samples(plats):
    samples = []
    for row in plats[:6]:
        items = shop_services(platform=row.get("name") or "", limit=1)
        if not items:
            continue
        item = items[0]
        row["from_rate"] = item.get("rate")
        samples.append(item)
    return samples


def _home_bundle():
    """Cached homepage data — avoids repeated SQLite work on hot path."""
    now = time.monotonic()
    hit = _HOME_BUNDLE["data"]
    if hit is not None and (now - _HOME_BUNDLE["t"]) < _HOME_BUNDLE_TTL:
        return hit
    plats = _home_plats(shop_nav()["platforms"])
    data = {
        "shop_plats": plats,
        "live_stats": public_stats(),
        "home_samples": _home_samples(plats),
    }
    _HOME_BUNDLE["t"] = now
    _HOME_BUNDLE["data"] = data
    return data


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    extra = {
        "shop_plats": [],
        "live_stats": {"orders": 0, "clients": 0, "services": 0},
        "home_samples": [],
        "ticker_json": _TICKER_JSON,
    }
    try:
        extra.update(_home_bundle())
        extra["ticker_json"] = _TICKER_JSON
    except Exception:
        pass
    # Full reviews — slider needs complete set
    extra["reviews"] = REVIEWS
    return page(request, "home.html", "home", extra)


@app.get("/services", response_class=HTMLResponse)
async def services(request: Request, cat: str = "", q: str = ""):
    blocked = _mod_gate(request, "mod_services")
    if blocked:
        return blocked
    nav = shop_nav()
    items = shop_services(platform=cat, q=q, limit=80)
    return page(request, "services.html", "services", {
        "catalog": items,
        "platforms": nav["platforms"],
        "categories": nav["categories"],
        "cat": cat,
        "q": q,
    })


@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    blocked = _mod_gate(request, "mod_faq")
    if blocked:
        return blocked
    return page(request, "faq.html", "faq")


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return page(request, "terms.html", "terms")


@app.get("/api", response_class=HTMLResponse)
async def api_page(request: Request):
    blocked = _mod_gate(request, "mod_api")
    if blocked:
        return blocked
    return page(request, "api.html", "api")


@app.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request, tag: str = ""):
    from cms import q_all
    from blog_content import FEATURED_TAGS, decorate, seed_blog, tag_list
    try:
        seed_blog()
    except Exception:
        pass
    tag = (tag or "").strip()
    rows = q_all("SELECT * FROM blog WHERE COALESCE(published,1)=1 ORDER BY id DESC")
    found = []
    seen = set()
    for row in rows:
        for item in tag_list(row):
            if item not in seen:
                seen.add(item)
                found.append(item)
    tags = list(FEATURED_TAGS)
    for item in found:
        if item not in tags:
            tags.append(item)
    if tag:
        rows = [row for row in rows if tag in tag_list(row)]
    return page(request, "blog.html", "blog", {"posts": decorate(rows), "tag": tag, "all_tags": tags})


@app.get("/rss.xml")
@app.get("/blog/rss.xml")
async def blog_rss():
    posts = []
    try:
        from cms import q_all
        posts = q_all("SELECT * FROM blog WHERE COALESCE(published,1)=1 ORDER BY id DESC LIMIT 40")
    except Exception:
        posts = []
    return Response(rss_xml(posts), media_type="application/rss+xml; charset=utf-8", headers={"Cache-Control": "public, max-age=300"})


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_one(request: Request, slug: str):
    from cms import q_all, q_one
    from blog_content import decorate, post_href, tag_list
    if slug.isdigit():
        post = q_one("SELECT * FROM blog WHERE id=?", (int(slug),))
        if post and (post.get("slug") or "").strip():
            return RedirectResponse(post_href(post), status_code=301)
    else:
        post = q_one("SELECT * FROM blog WHERE slug=?", (slug,))
    if not post or int(post.get("published") if post.get("published") is not None else 1) == 0:
        return page(request, "notfound.html", "notfound", status_code=404)
    related = q_all(
        "SELECT * FROM blog WHERE COALESCE(published,1)=1 AND id!=? ORDER BY id DESC LIMIT 24",
        (post["id"],),
    )
    mine = set(tag_list(post))
    scored = []
    for row in related:
        overlap = len(mine.intersection(tag_list(row)))
        scored.append((overlap, row.get("id") or 0, row))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    picked = [row for _, _, row in scored[:4]]
    return page(request, "blog_post.html", "blog", {"post": decorate([post])[0], "related": decorate(picked)})


@app.get("/p/{slug}", response_class=HTMLResponse)
async def custom_page(request: Request, slug: str):
    from cms import q_one
    item = q_one("SELECT * FROM pages WHERE slug=?", (slug,))
    if not item:
        return page(request, "notfound.html", "notfound", status_code=404)
    return page(request, "page.html", "page", {"item": item})


@app.get("/robots.txt")
async def robots():
    return PlainTextResponse(robots_txt(), media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml")
async def sitemap():
    urls = [
        {"loc": site_url() + "/", "priority": "1.0", "changefreq": "daily"},
        {"loc": site_url() + "/services", "priority": "0.9", "changefreq": "daily"},
        {"loc": site_url() + "/faq", "priority": "0.8", "changefreq": "weekly"},
        {"loc": site_url() + "/terms", "priority": "0.4", "changefreq": "monthly"},
        {"loc": site_url() + "/api", "priority": "0.6", "changefreq": "weekly"},
        {"loc": site_url() + "/blog", "priority": "0.8", "changefreq": "daily"},
        {"loc": site_url() + "/signup", "priority": "0.7", "changefreq": "monthly"},
        {"loc": site_url() + "/rss.xml", "priority": "0.4", "changefreq": "weekly"},
    ]
    try:
        nav = shop_nav()
        seen = set()
        for row in nav.get("platforms") or []:
            name = (row.get("name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            from urllib.parse import urlencode
            urls.append({
                "loc": site_url() + "/services?" + urlencode({"cat": name}),
                "priority": "0.8",
                "changefreq": "daily",
            })
        from cms import q_all
        from blog_content import post_href
        for post in q_all("SELECT id, slug, created_at FROM blog WHERE COALESCE(published,1)=1 ORDER BY id DESC"):
            urls.append({
                "loc": site_url() + post_href(post),
                "lastmod": str(post.get("created_at") or "")[:10],
                "priority": "0.7",
                "changefreq": "weekly",
            })
        for item in q_all("SELECT slug FROM pages"):
            slug = (item.get("slug") or "").strip()
            if slug:
                urls.append({"loc": "%s/p/%s" % (site_url(), slug), "priority": "0.5", "changefreq": "monthly"})
    except Exception:
        pass
    xml = sitemap_xml(urls)
    return Response(xml, media_type="application/xml; charset=utf-8", headers={"Cache-Control": "public, max-age=300"})


@app.get("/health")
async def health():
    return {"ok": True, "engine": "python"}


@app.get("/manifest.webmanifest")
async def web_manifest():
    path = ROOT / "static" / "manifest.webmanifest"
    return FileResponse(path, media_type="application/manifest+json", headers={"Cache-Control": "public, max-age=86400"})


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    path = request.url.path or ""
    if exc.status_code == 404 and not path.startswith("/api") and not path.startswith("/internal"):
        accept = (request.headers.get("accept") or "").lower()
        if "application/json" not in accept:
            return page(request, "notfound.html", "notfound", status_code=404)
    if exc.status_code == 404:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return HTMLResponse(str(exc.detail or "error"), status_code=exc.status_code)


@app.get("/internal/cron")
async def internal_cron(token: str = ""):
    expected = os.environ.get("CRON_TOKEN", "")
    got = token or ""
    if not expected or len(str(got)) != len(str(expected)) or not hmac.compare_digest(str(got), str(expected)):
        return HTMLResponse("forbidden", status_code=403)
    return {"ok": True, "detail": run_all()}


@app.api_route("/internal/pay/in", methods=["GET", "POST"])
async def internal_pay_in(request: Request, token: str = "", amount: str = "", text: str = ""):
    from inbound import process_inbound
    from pay import pay_notify_token
    expected = pay_notify_token()
    got = token or request.query_params.get("token") or request.headers.get("x-pay-token") or ""
    if not expected or len(str(got)) != len(str(expected)) or not hmac.compare_digest(str(got), str(expected)):
        return JSONResponse({"ok": False}, status_code=403)
    body_text = text or request.query_params.get("text") or ""
    amt_raw = amount or request.query_params.get("amount") or ""
    source = request.query_params.get("source") or "notify"
    sender = request.query_params.get("sender") or ""
    if request.method == "POST":
        ctype = (request.headers.get("content-type") or "").lower()
        if "json" in ctype:
            try:
                data = await request.json()
            except Exception:
                data = {}
            if isinstance(data, dict):
                amt_raw = amt_raw or str(data.get("amount") or data.get("amt") or "")
                body_text = body_text or str(data.get("text") or data.get("message") or data.get("sms") or data.get("body") or "")
                source = str(data.get("source") or source or "notify")
                sender = str(data.get("sender") or data.get("from") or sender or "")
        else:
            form = await request.form()
            amt_raw = amt_raw or str(form.get("amount") or form.get("amt") or "")
            body_text = body_text or str(form.get("text") or form.get("message") or form.get("sms") or form.get("body") or "")
            source = str(form.get("source") or source or "notify")
            sender = str(form.get("sender") or form.get("from") or sender or "")
            if not body_text:
                try:
                    raw = await request.body()
                    body_text = raw.decode("utf-8", "replace")
                except Exception:
                    body_text = ""
    pid, amt, last = process_inbound(body_text, amt_raw, source or "notify", sender)
    if last == "paid":
        return {"ok": True, "payment_id": pid, "amount": amt}
    return {"ok": False, "reason": last}


@app.post("/internal/pay/tg")
async def internal_pay_tg(request: Request, token: str = ""):
    from inbound import process_inbound, telegram_text
    from pay import pay_notify_token
    expected = pay_notify_token()
    got = token or request.query_params.get("token") or request.headers.get("x-telegram-bot-api-secret-token") or ""
    if not expected or len(str(got)) != len(str(expected)) or not hmac.compare_digest(str(got), str(expected)):
        return JSONResponse({"ok": False}, status_code=403)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    text = telegram_text(payload)
    if not text:
        return {"ok": True, "ignored": True}
    pid, amt, last = process_inbound(text, "", "telegram")
    if last == "paid":
        return {"ok": True, "payment_id": pid, "amount": amt}
    return {"ok": False, "reason": last}
