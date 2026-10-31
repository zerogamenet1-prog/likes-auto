from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

from admin import APPEAR_TABS, SETTING_TABS_UI, render, require_admin
from cms import add_staff, cms_migrate, delete_staff, q_all, q_one, q_run
from db import MOD_KEYS, add_log, get_settings, save_settings, ROOT, list_cron_logs
from store import fetch_all
from theme import public_theme_ctx, save_theme
from google_oauth import google_status

router = APIRouter(prefix="/admin")

SETTING_TABS = SETTING_TABS_UI


def ok(request):
    return require_admin(request)


def settings_ctx(tab, extra=None):
    data = {
        "page": "settings",
        "section": "settings",
        "tabs": SETTING_TABS,
        "tab": tab,
        "settings": get_settings(),
        "saved": False,
    }
    if extra:
        data.update(extra)
    return data


def appear_ctx(tab, extra=None):
    data = {"page": "news", "section": "news", "tabs": APPEAR_TABS, "tab": tab}
    if extra:
        data.update(extra)
    return data


@router.get("/settings/general", response_class=HTMLResponse)
async def general_get(request: Request, saved: str = ""):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    return render(request, "admin/settings_hub.html", settings_ctx("general", {"saved": saved == "1"}))


@router.post("/settings/general")
async def general_post(request: Request):
    g = ok(request)
    if g:
        return g
    form = dict(await request.form())
    keys = [
        "site_name", "currency", "usd_rate", "profit_percent", "support_email", "timezone", "announcement",
        "fundstransfer_fees", "max_ticket", "google_client_id",
        "affiliate_percent", "child_panel_price", "child_ns1", "child_ns2", "min_deposit",
        "promptpay", "truemoney", "alert_balance", "custom_header", "custom_footer",
        "pay_merchant", "admin_allow_ips",
    ]
    values = {k: str(form.get(k) or "") for k in keys}
    for flag in (
        "maintenance", "enable_transfer_funds", "ticket_system",
        "registration_page", "resetpass", "google_login", "auto_refill",
    ):
        values[flag] = "1" if form.get(flag) else "0"
    secret = str(form.get("google_client_secret") or "").strip()
    if secret:
        values["google_client_secret"] = secret
    save_settings(values)
    add_log("บันทึกตั้งค่าทั่วไป", request.client.host if request.client else "-")
    return RedirectResponse("/admin/settings/general?saved=1", status_code=303)


@router.get("/settings/currency", response_class=HTMLResponse)
async def currency_get(request: Request, saved: str = ""):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/settings_hub.html", settings_ctx("currency", {"saved": saved == "1"}))


@router.post("/settings/currency")
async def currency_post(request: Request, currency: str = Form("THB"), usd_rate: str = Form("35"), profit_percent: str = Form("100")):
    g = ok(request)
    if g:
        return g
    save_settings({"currency": currency, "usd_rate": usd_rate, "profit_percent": profit_percent})
    return RedirectResponse("/admin/settings/currency?saved=1", status_code=303)


@router.get("/settings/payments", response_class=HTMLResponse)
async def payments_set(request: Request):
    g = ok(request)
    if g:
        return g
    from content import SITE
    from pay import pay_notify_token
    tok = pay_notify_token()
    return render(request, "admin/settings_hub.html", settings_ctx("payments", {
        "methods": fetch_all("SELECT * FROM methods ORDER BY id"),
        "pay_notify_token": tok,
        "pay_notify_url": (SITE.get("url") or "https://likes-auto.com").rstrip("/") + "/internal/pay/in?token=" + tok,
    }))


@router.post("/settings/payments")
async def payments_add(request: Request, name: str = Form(...), detail: str = Form(""), kind: str = Form("other"), pay_to: str = Form("")):
    g = ok(request)
    if g:
        return g
    q_run("INSERT INTO methods (name, detail, status, kind, pay_to) VALUES (?,?,?,?,?)", (name, detail, "active", kind, pay_to.strip()))
    return RedirectResponse("/admin/settings/payments", status_code=303)


@router.post("/settings/payments/options")
async def payments_options(
    request: Request,
    promptpay: str = Form(""),
    truemoney: str = Form(""),
    pay_merchant: str = Form("LIKES AUTO"),
    pay_unique_satang: str = Form(""),
    auto_approve_slip: str = Form(""),
    easyslip_key: str = Form(""),
):
    g = ok(request)
    if g:
        return g
    values = {
        "promptpay": promptpay.strip(),
        "truemoney": truemoney.strip(),
        "pay_merchant": pay_merchant.strip() or "LIKES AUTO",
        "pay_unique_satang": "1",
        "auto_approve_slip": "1" if auto_approve_slip else "0",
    }
    key = easyslip_key.strip()
    if key:
        values["easyslip_key"] = key
    save_settings(values)
    return RedirectResponse("/admin/settings/payments", status_code=303)


@router.post("/settings/payments/telegram")
async def payments_telegram(request: Request, pay_tg_token: str = Form("")):
    g = ok(request)
    if g:
        return g
    from inbound import set_telegram_webhook
    from pay import pay_notify_token
    token = pay_tg_token.strip()
    if token:
        save_settings({"pay_tg_token": token})
        set_telegram_webhook(token, pay_notify_token())
    return RedirectResponse("/admin/settings/payments", status_code=303)


@router.post("/settings/payments/notify-token")
async def pay_notify_regen(request: Request):
    g = ok(request)
    if g:
        return g
    import secrets
    save_settings({"pay_notify_token": secrets.token_hex(16)})
    return RedirectResponse("/admin/settings/payments", status_code=303)


@router.post("/settings/payments/{mid}/edit")
async def payments_edit(request: Request, mid: int, pay_to: str = Form("")):
    g = ok(request)
    if g:
        return g
    q_run("UPDATE methods SET pay_to=? WHERE id=?", (pay_to.strip(), mid))
    return RedirectResponse("/admin/settings/payments", status_code=303)


@router.post("/settings/payments/{mid}/toggle")
async def payments_toggle(request: Request, mid: int):
    g = ok(request)
    if g:
        return g
    row = q_one("SELECT status FROM methods WHERE id=?", (mid,))
    if row:
        q_run("UPDATE methods SET status=? WHERE id=?", ("paused" if row["status"] == "active" else "active", mid))
    return RedirectResponse("/admin/settings/payments", status_code=303)


@router.get("/settings/bonuses", response_class=HTMLResponse)
async def bonuses_get(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/settings_hub.html", settings_ctx("bonuses", {"bonuses": fetch_all("SELECT * FROM bonuses ORDER BY min_amount")}))


@router.post("/settings/bonuses")
async def bonuses_add(request: Request, min_amount: float = Form(...), percent: float = Form(...)):
    g = ok(request)
    if g:
        return g
    q_run("INSERT INTO bonuses (min_amount, percent, status) VALUES (?,?,?)", (min_amount, percent, "active"))
    return RedirectResponse("/admin/settings/bonuses", status_code=303)


@router.post("/settings/bonuses/{bid}/delete")
async def bonuses_del(request: Request, bid: int):
    g = ok(request)
    if g:
        return g
    q_run("DELETE FROM bonuses WHERE id=?", (bid,))
    return RedirectResponse("/admin/settings/bonuses", status_code=303)


@router.get("/settings/banks", response_class=HTMLResponse)
async def banks_get(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/settings_hub.html", settings_ctx("banks", {"banks": fetch_all("SELECT * FROM banks ORDER BY id")}))


@router.post("/settings/banks")
async def banks_add(request: Request, bank: str = Form(...), account: str = Form(...), holder: str = Form(...)):
    g = ok(request)
    if g:
        return g
    q_run("INSERT INTO banks (bank, account, holder, status) VALUES (?,?,?,?)", (bank, account, holder, "active"))
    return RedirectResponse("/admin/settings/banks", status_code=303)


@router.post("/settings/banks/{bid}/delete")
async def banks_del(request: Request, bid: int):
    g = ok(request)
    if g:
        return g
    q_run("DELETE FROM banks WHERE id=?", (bid,))
    return RedirectResponse("/admin/settings/banks", status_code=303)


@router.get("/settings/modules", response_class=HTMLResponse)
async def modules_get(request: Request, saved: str = ""):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    return render(request, "admin/settings_hub.html", settings_ctx("modules", {"saved": saved == "1"}))


@router.post("/settings/modules")
async def modules_post(request: Request):
    g = ok(request)
    if g:
        return g
    form = dict(await request.form())
    keys = [
        "mod_neworder", "mod_dripfeed", "mod_services", "mod_orders", "mod_subscription",
        "mod_addfunds", "mod_affiliate", "mod_child", "mod_tickets", "mod_faq",
        "mod_account", "mod_api", "mod_logout", "mod_transfer",
    ]
    save_settings({k: ("1" if form.get(k) == "1" else "0") for k in keys})
    return RedirectResponse("/admin/settings/modules?saved=1", status_code=303)


@router.get("/settings/integrations", response_class=HTMLResponse)
async def integ_get(request: Request, saved: str = ""):
    g = ok(request)
    if g:
        return g
    s = get_settings()
    return render(request, "admin/settings_hub.html", settings_ctx("integrations", {
        "saved": saved == "1",
        "google_status": google_status(s),
    }))


@router.post("/settings/integrations")
async def integ_post(request: Request):
    g = ok(request)
    if g:
        return g
    form = dict(await request.form())
    save_settings({
        "smtp_host": form.get("smtp_host") or "",
        "smtp_user": form.get("smtp_user") or "",
        "smtp_port": form.get("smtp_port") or "587",
        "recaptcha_key": form.get("recaptcha_key") or "",
        "analytics_id": form.get("analytics_id") or "",
        "gsc_verify": form.get("gsc_verify") or "",
        "bing_verify": form.get("bing_verify") or "",
        "google_client_id": form.get("google_client_id") or "",
        "google_login": "1" if form.get("google_login") else "0",
    })
    secret = str(form.get("smtp_pass") or "").strip()
    if secret:
        save_settings({"smtp_pass": secret})
    gsecret = str(form.get("google_client_secret") or "").strip()
    if gsecret:
        save_settings({"google_client_secret": gsecret})
    return RedirectResponse("/admin/settings/integrations?saved=1", status_code=303)


@router.post("/settings/integrations/test-mail")
async def integ_test_mail(request: Request):
    g = ok(request)
    if g:
        return g
    from mail import send_mail, smtp_ready
    s = get_settings()
    to_addr = (s.get("support_email") or s.get("smtp_user") or "").strip()
    if not smtp_ready(s) or not to_addr:
        return RedirectResponse("/admin/settings/integrations?saved=1", status_code=303)
    send_mail(to_addr, "Likes Auto SMTP test", "SMTP from Likes Auto admin is working.", s)
    add_log("ทดสอบ SMTP", request.client.host if request.client else "-")
    return RedirectResponse("/admin/settings/integrations?saved=1", status_code=303)


@router.get("/settings/alerts", response_class=HTMLResponse)
async def alerts_get(request: Request, saved: str = ""):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/settings_hub.html", settings_ctx("alerts", {"saved": saved == "1"}))


@router.post("/settings/alerts")
async def alerts_post(request: Request, alert_balance: str = Form("10"), support_email: str = Form("")):
    g = ok(request)
    if g:
        return g
    save_settings({"alert_balance": alert_balance, "support_email": support_email})
    return RedirectResponse("/admin/settings/alerts?saved=1", status_code=303)


@router.get("/settings/subjects", response_class=HTMLResponse)
async def subjects_get(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/settings_hub.html", settings_ctx("subjects", {"subjects": fetch_all("SELECT * FROM subjects ORDER BY id")}))


@router.post("/settings/subjects")
async def subjects_add(request: Request, name: str = Form(...)):
    g = ok(request)
    if g:
        return g
    q_run("INSERT INTO subjects (name) VALUES (?)", (name,))
    return RedirectResponse("/admin/settings/subjects", status_code=303)


@router.post("/settings/subjects/{sid}/delete")
async def subjects_del(request: Request, sid: int):
    g = ok(request)
    if g:
        return g
    q_run("DELETE FROM subjects WHERE id=?", (sid,))
    return RedirectResponse("/admin/settings/subjects", status_code=303)


@router.get("/appearance/pages", response_class=HTMLResponse)
async def pages_get(request: Request, edit: str = ""):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    editing = q_one("SELECT * FROM pages WHERE id=?", (int(edit),)) if str(edit).isdigit() else None
    return render(request, "admin/appear_hub.html", appear_ctx("pages", {
        "pages": fetch_all("SELECT * FROM pages ORDER BY id"),
        "editing": editing,
    }))


@router.post("/appearance/pages")
async def pages_save(request: Request, pid: str = Form(""), slug: str = Form(...), title: str = Form(...), body: str = Form("")):
    g = ok(request)
    if g:
        return g
    if pid:
        q_run("UPDATE pages SET slug=?, title=?, body=? WHERE id=?", (slug, title, body, int(pid)))
    else:
        q_run("INSERT INTO pages (slug, title, body) VALUES (?,?,?)", (slug, title, body))
    return RedirectResponse("/admin/appearance/pages", status_code=303)


@router.post("/appearance/pages/{pid}/delete")
async def pages_del(request: Request, pid: int):
    g = ok(request)
    if g:
        return g
    q_run("DELETE FROM pages WHERE id=?", (pid,))
    return RedirectResponse("/admin/appearance/pages", status_code=303)


@router.get("/appearance/blog", response_class=HTMLResponse)
async def blog_get(request: Request, edit: str = "", new: str = "", q: str = "", st: str = "", saved: str = "", uploaded: str = ""):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    from blog_content import decorate
    from cms import blog_media
    rows = fetch_all("SELECT * FROM blog ORDER BY id DESC")
    q = (q or "").strip()
    st = (st or "").strip()
    if q:
        low = q.lower()
        rows = [r for r in rows if low in (r.get("title") or "").lower() or low in (r.get("slug") or "").lower() or low in (r.get("tags") or "").lower()]
    if st == "on":
        rows = [r for r in rows if int(r.get("published") if r.get("published") is not None else 1) == 1]
    elif st == "off":
        rows = [r for r in rows if int(r.get("published") or 0) == 0]
    editing = q_one("SELECT * FROM blog WHERE id=?", (int(edit),)) if str(edit).isdigit() else None
    show_form = bool(editing) or new == "1"
    pub_n = sum(1 for r in fetch_all("SELECT published FROM blog") if int(r.get("published") if r.get("published") is not None else 1) == 1)
    all_n = q_one("SELECT COUNT(*) AS n FROM blog") or {"n": 0}
    return render(request, "admin/blog.html", appear_ctx("blog", {
        "posts": decorate(rows),
        "editing": editing,
        "show_form": show_form,
        "q": q,
        "st": st,
        "saved": saved == "1",
        "uploaded": uploaded,
        "media": blog_media(),
        "pub_n": pub_n,
        "all_n": all_n.get("n") or 0,
        "draft_n": max(0, (all_n.get("n") or 0) - pub_n),
    }))


@router.post("/appearance/blog")
async def blog_save(
    request: Request,
    pid: str = Form(""),
    title: str = Form(...),
    body: str = Form(""),
    tags: str = Form(""),
    slug: str = Form(""),
    excerpt: str = Form(""),
    created_at: str = Form(""),
    published: str = Form(""),
):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    from blog_content import excerpt_text, first_img, unique_blog_slug
    stamp = (created_at or "").strip() or __import__("store").now()
    pub = 1 if str(published) == "1" else 0
    html = body or ""
    cover = first_img(html)
    summary = (excerpt or "").strip() or excerpt_text(html)
    exclude = int(pid) if str(pid).isdigit() else None
    slug = unique_blog_slug(title, slug, exclude)
    if exclude:
        q_run(
            "UPDATE blog SET title=?, body=?, created_at=?, slug=?, tags=?, excerpt=?, published=?, cover=? WHERE id=?",
            (title, html, stamp, slug, (tags or "").strip(), summary, pub, cover, exclude),
        )
        add_log("แก้บล็อก #%s" % exclude, request.client.host if request.client else "-")
        return RedirectResponse("/admin/appearance/blog?edit=%s&saved=1" % exclude, status_code=303)
    lid = q_run(
        "INSERT INTO blog (title, body, created_at, slug, tags, excerpt, published, cover) VALUES (?,?,?,?,?,?,?,?)",
        (title, html, stamp, slug, (tags or "").strip(), summary, pub, cover),
    )
    add_log("เพิ่มบล็อก #%s" % lid, request.client.host if request.client else "-")
    return RedirectResponse("/admin/appearance/blog?edit=%s&saved=1" % lid, status_code=303)


@router.post("/appearance/blog/upload")
async def blog_upload(request: Request, pid: str = Form(""), upload: UploadFile = File(...)):
    g = ok(request)
    if g:
        return g
    from db import ROOT
    folder = ROOT / "static" / "uploads" / "blog"
    folder.mkdir(parents=True, exist_ok=True)
    raw = Path(upload.filename or "image.jpg").name
    ext = Path(raw).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    name = "b%s%s" % (__import__("store").now().replace(" ", "").replace(":", "").replace("-", "")[:14], ext)
    dest = folder / name
    data = await upload.read()
    dest.write_bytes(data)
    url = "/static/uploads/blog/" + name
    q_run("INSERT INTO uploads (name, path, created_at) VALUES (?,?,?)", (name, url, __import__("store").now()))
    from urllib.parse import quote
    qs = "uploaded=" + quote(url, safe="")
    if str(pid).isdigit():
        return RedirectResponse("/admin/appearance/blog?edit=%s&%s" % (pid, qs), status_code=303)
    return RedirectResponse("/admin/appearance/blog?new=1&%s" % qs, status_code=303)


@router.post("/appearance/blog/{bid}/toggle")
async def blog_toggle(request: Request, bid: int):
    g = ok(request)
    if g:
        return g
    row = q_one("SELECT id, published FROM blog WHERE id=?", (bid,))
    if row:
        nxt = 0 if int(row.get("published") if row.get("published") is not None else 1) == 1 else 1
        q_run("UPDATE blog SET published=? WHERE id=?", (nxt, bid))
    return RedirectResponse("/admin/appearance/blog", status_code=303)


@router.post("/appearance/blog/{bid}/copy")
async def blog_copy(request: Request, bid: int):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    from blog_content import unique_blog_slug
    row = q_one("SELECT * FROM blog WHERE id=?", (bid,))
    if not row:
        return RedirectResponse("/admin/appearance/blog", status_code=303)
    title = (row.get("title") or "บทความ") + " (สำเนา)"
    slug = unique_blog_slug(title, (row.get("slug") or "") + "-copy")
    lid = q_run(
        "INSERT INTO blog (title, body, created_at, slug, tags, excerpt, published, cover) VALUES (?,?,?,?,?,?,0,?)",
        (
            title,
            row.get("body") or "",
            __import__("store").now(),
            slug,
            row.get("tags") or "",
            row.get("excerpt") or "",
            row.get("cover") or "",
        ),
    )
    return RedirectResponse("/admin/appearance/blog?edit=%s&saved=1" % lid, status_code=303)


@router.post("/appearance/blog/{bid}/delete")
async def blog_del(request: Request, bid: int):
    g = ok(request)
    if g:
        return g
    q_run("DELETE FROM blog WHERE id=?", (bid,))
    add_log("ลบบล็อก #%s" % bid, request.client.host if request.client else "-")
    return RedirectResponse("/admin/appearance/blog", status_code=303)


@router.get("/appearance/menu", response_class=HTMLResponse)
async def menu_get(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/appear_hub.html", appear_ctx("menu", {"menus": fetch_all("SELECT * FROM menus ORDER BY sort, id")}))


@router.post("/appearance/menu")
async def menu_add(request: Request, label: str = Form(...), href: str = Form(...), sort: int = Form(0)):
    g = ok(request)
    if g:
        return g
    q_run("INSERT INTO menus (label, href, sort, visible) VALUES (?,?,?,1)", (label, href, sort))
    return RedirectResponse("/admin/appearance/menu", status_code=303)


@router.post("/appearance/menu/{mid}/delete")
async def menu_del(request: Request, mid: int):
    g = ok(request)
    if g:
        return g
    q_run("DELETE FROM menus WHERE id=?", (mid,))
    return RedirectResponse("/admin/appearance/menu", status_code=303)


@router.get("/appearance/files", response_class=HTMLResponse)
async def files_get(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/appear_hub.html", appear_ctx("files", {"files": fetch_all("SELECT * FROM uploads ORDER BY id DESC")}))


@router.post("/appearance/files")
async def files_up(request: Request, upload: UploadFile = File(...)):
    g = ok(request)
    if g:
        return g
    folder = ROOT / "static" / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    name = Path(upload.filename or "file.bin").name
    dest = folder / name
    dest.write_bytes(await upload.read())
    q_run("INSERT INTO uploads (name, path, created_at) VALUES (?,?,?)", (name, "/static/uploads/" + name, __import__("store").now()))
    return RedirectResponse("/admin/appearance/files", status_code=303)


@router.post("/appearance/files/{fid}/delete")
async def files_del(request: Request, fid: int):
    g = ok(request)
    if g:
        return g
    row = q_one("SELECT * FROM uploads WHERE id=?", (fid,))
    if row:
        q_run("DELETE FROM uploads WHERE id=?", (fid,))
        try:
            rel = str(row.get("path") or "").lstrip("/")
            if rel.startswith("static/"):
                path = ROOT / rel
                if path.is_file() and "uploads" in path.parts:
                    path.unlink()
        except Exception:
            pass
    return RedirectResponse("/admin/appearance/files", status_code=303)


@router.get("/appearance/themes", response_class=HTMLResponse)
async def themes_get(request: Request, saved: str = ""):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    s = get_settings()
    extra = public_theme_ctx(s)
    extra["settings"] = s
    extra["saved"] = saved == "1"
    return render(request, "admin/appear_hub.html", appear_ctx("themes", extra))


@router.post("/appearance/themes")
async def themes_post(request: Request):
    g = ok(request)
    if g:
        return g
    form = dict(await request.form())
    save_theme(form)
    add_log("บันทึกธีมเว็บ", request.client.host if request.client else "-")
    return RedirectResponse("/admin/appearance/themes?saved=1", status_code=303)


@router.get("/staff", response_class=HTMLResponse)
async def staff_get(request: Request, saved: str = "", error: str = ""):
    g = ok(request)
    if g:
        return g
    cms_migrate()
    return render(request, "admin/staff.html", settings_ctx("staff", {
        "staff": fetch_all("SELECT id, username FROM admins"),
        "saved": saved == "1",
        "error": error,
    }))


@router.post("/staff")
async def staff_add(request: Request, username: str = Form(...), password: str = Form(...)):
    g = ok(request)
    if g:
        return g
    if len(password) < 8 or not add_staff(username.strip(), password):
        return RedirectResponse("/admin/staff?error=1", status_code=303)
    add_log("เพิ่มพนักงาน %s" % username, request.client.host if request.client else "-")
    return RedirectResponse("/admin/staff?saved=1", status_code=303)


@router.post("/staff/{sid}/delete")
async def staff_del(request: Request, sid: int):
    g = ok(request)
    if g:
        return g
    if not delete_staff(sid, request.session.get("admin") or ""):
        return RedirectResponse("/admin/staff?error=1", status_code=303)
    add_log("ลบพนักงาน #%s" % sid, request.client.host if request.client else "-")
    return RedirectResponse("/admin/staff?saved=1", status_code=303)


@router.get("/logs/guard", response_class=HTMLResponse)
async def guard_logs(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/simple.html", settings_ctx("logs", {
        "title": "บันทึกเข้าสู่ระบบ",
        "columns": ["id", "username", "ip", "ok", "created_at"],
        "labels": ["ID", "ยูส", "IP", "สำเร็จ", "เวลา"],
        "rows": fetch_all("SELECT * FROM guard_logs ORDER BY id DESC LIMIT 200"),
        "log_kind": "guard",
    }))


@router.get("/logs/providers", response_class=HTMLResponse)
async def provider_logs(request: Request):
    g = ok(request)
    if g:
        return g
    return render(request, "admin/simple.html", settings_ctx("logs", {
        "title": "บันทึกดึงงาน",
        "columns": ["id", "job", "detail", "created_at"],
        "labels": ["ID", "งาน", "รายละเอียด", "เวลา"],
        "rows": list_cron_logs(100),
        "log_kind": "providers",
    }))
