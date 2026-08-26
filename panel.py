from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
import threading

from content import COPY, FAQ, SITE
from google_oauth import (
    MSG,
    google_auth_url,
    google_error_message,
    google_on,
    google_profile,
    google_ready,
    google_redirect_uri,
    login_or_create_google,
    new_state,
    safe_next,
)
from db import (
    add_log,
    check_client,
    client_dash,
    client_orders,
    client_payments,
    client_tickets,
    create_client,
    create_order,
    create_payment,
    create_ticket,
    get_client,
    get_settings,
    init_db,
    mods_map,
    first_open_path,
    mod_on,
    shop_nav,
    shop_services,
)
from th_shop import th_text
from store import (
    all_ticket_replies,
    change_client_password,
    create_child_panel,
    create_dripfeed,
    create_subscription,
    create_task,
    fetch_all,
    fetch_one,
    list_news,
    regenerate_api_key,
    reply_ticket,
    transfer_funds,
)
from guard import USER_FAILS, USER_LOCK, client_ip, ensure_csrf, login_block, mark_login

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))
templates.env.filters["th"] = th_text
router = APIRouter()

DASH_TITLES = {
    "neworder": "คำสั่งซื้อใหม่",
    "orders": "ประวัติคำสั่งซื้อ",
    "addfunds": "เติมเครดิต",
    "tickets": "ซัพพอร์ต",
    "account": "บัญชี",
    "services": "บริการทั้งหมด",
    "dripfeeds": "ส่งทีละรอบ",
    "subscriptions": "เติมอัตโนมัติ",
    "affiliates": "เชิญเพื่อน",
    "panels": "แผงลูก",
    "api": "API",
    "faq": "คำถามที่พบบ่อย",
}


def current_user(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return get_client(client_id=uid)


def ctx(request: Request, page: str, extra=None):
    data = {
        "request": request,
        "site": SITE,
        "t": COPY,
        "page": page,
        "faq": FAQ if page == "faq" else [],
        "user": current_user(request),
        "error": "",
        "ok": "",
        "catalog": [],
        "platforms": [],
        "categories": [],
        "news": list_news(5) if page == "neworder" else [],
        "settings": get_settings(),
        "google_on": google_on(),
        "google_ready": google_ready(),
        "google_redirect": google_redirect_uri(),
        "st": {
            "pending": "รอส่ง",
            "processing": "กำลังทำ",
            "inprogress": "กำลังทำ",
            "completed": "สำเร็จ",
            "partial": "บางส่วน",
            "canceled": "ยกเลิก",
            "paid": "อนุมัติแล้ว",
            "waiting": "รอตรวจ",
            "open": "เปิด",
            "answered": "ตอบแล้ว",
            "closed": "ปิด",
            "active": "ใช้งาน",
            "paused": "พัก",
            "success": "สำเร็จ",
            "failed": "ไม่สำเร็จ",
        },
        "dash": {"orders": 0, "spent": 0},
        "dash_title": DASH_TITLES.get(page, SITE.get("name") or "Likes Auto"),
        "dash_mode": False,
        "csrf": "",
    }
    if data["user"] and page not in ("signin", "signup"):
        data["dash_mode"] = True
        data["dash"] = client_dash(data["user"]["username"])
    if page in ("neworder", "dripfeeds", "subscriptions", "services"):
        nav = shop_nav()
        data["platforms"] = nav["platforms"]
        data["categories"] = nav["categories"]
    if extra:
        data.update(extra)
    try:
        from cms import q_all
        data["menus"] = []
        if page == "addfunds":
            data["methods"] = q_all("SELECT * FROM methods WHERE status='active'")
            data["banks"] = q_all("SELECT * FROM banks WHERE status='active'")
            data["bonuses"] = q_all("SELECT * FROM bonuses WHERE status='active' ORDER BY min_amount")
        else:
            data["methods"] = []
            data["banks"] = []
            data["bonuses"] = []
        data["subjects"] = q_all("SELECT * FROM subjects ORDER BY id") if page == "tickets" else []
    except Exception:
        data.setdefault("menus", [])
        data.setdefault("methods", [])
        data.setdefault("banks", [])
        data.setdefault("subjects", [])
        data.setdefault("bonuses", [])
    data["mods"] = mods_map(data.get("settings"))
    data["shop_home"] = first_open_path(data.get("settings"))
    try:
        from theme import public_theme_ctx
        data.update(public_theme_ctx(data.get("settings")))
    except Exception:
        data.setdefault("theme_pack", "violet")
        data.setdefault("theme_switch", True)
        data.setdefault("theme_css", "")
        data.setdefault("theme_packs", [])
    try:
        data["csrf"] = ensure_csrf(request)
    except Exception:
        data["csrf"] = ""
    return data


def render(request: Request, template: str, page: str, extra=None):
    return templates.TemplateResponse(request, template, ctx(request, page, extra))


def need_user(request: Request):
    if not current_user(request):
        return RedirectResponse("/signin", status_code=303)
    return None


def need_mod(request: Request, *keys: str):
    gate = need_user(request)
    if gate:
        return gate
    s = get_settings()
    for key in keys:
        if key and not mod_on(s, key):
            return RedirectResponse(first_open_path(s), status_code=303)
    return None


def _norm_status(value):
    s = (value or "").lower()
    if s == "inprogress":
        return "processing"
    if s in {"cancelled", "canceled"}:
        return "canceled"
    return s


def enrich_orders(items):
    from db import get_service
    from service_fields import service_refill_ok

    svc_cache = {}
    out = []
    for item in items:
        row = dict(item)
        qty = int(row.get("quantity") or 0)
        rem_raw = row.get("remains")
        rem = None
        try:
            if rem_raw not in (None, "", "-"):
                rem = int(float(rem_raw))
        except Exception:
            rem = None
        st = _norm_status(row.get("status"))
        if rem is not None and qty > 0:
            done = max(0, min(qty, qty - rem))
            row["progress"] = int(round(done * 100 / qty))
            row["done"] = done
        elif st == "completed":
            row["progress"] = 100
            row["done"] = qty
        elif st in {"pending", "canceled"}:
            row["progress"] = 0
            row["done"] = 0
        else:
            row["progress"] = None
            row["done"] = 0
        sid = row.get("service_id")
        svc = None
        if sid:
            try:
                sid_n = int(sid)
            except (TypeError, ValueError):
                sid_n = 0
            if sid_n:
                if sid_n not in svc_cache:
                    svc_cache[sid_n] = get_service(sid_n)
                svc = svc_cache[sid_n]
        row["can_refill"] = service_refill_ok(svc, row.get("service") or "")
        row["service_plat"] = (svc or {}).get("platform") or ""
        out.append(row)
    return out


def order_counts(items):
    data = {"all": len(items), "pending": 0, "processing": 0, "completed": 0, "partial": 0, "canceled": 0}
    for item in items:
        key = _norm_status(item.get("status"))
        if key in data:
            data[key] += 1
    return data


def filter_orders(items, q="", status=""):
    q = (q or "").strip().lower()
    status = _norm_status(status)
    out = []
    for item in items:
        if status and _norm_status(item.get("status")) != status:
            continue
        if q:
            blob = " ".join([
                str(item.get("id") or ""),
                str(item.get("service") or ""),
                str(item.get("link") or ""),
                str(item.get("status") or ""),
            ]).lower()
            if q not in blob:
                continue
        out.append(item)
    return out


@router.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    if current_user(request):
        return RedirectResponse("/neworder", status_code=303)
    settings = get_settings()
    if str(settings.get("registration_page") or "1") == "0":
        return render(request, "signin.html", "signin", {"error": "ปิดรับสมัครชั่วคราว"})
    return render(request, "signup.html", "signup", {"ref": request.query_params.get("ref", "")})


@router.post("/signup")
async def signup_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm: str = Form(...), ref: str = Form("")):
    init_db()
    blocked = login_block("signup", request, 6, 3600)
    if blocked:
        return render(request, "signup.html", "signup", {"error": blocked, "ref": ref})
    if password != confirm:
        return render(request, "signup.html", "signup", {"error": "รหัสผ่านไม่ตรงกัน", "ref": ref})
    if len(password) < 6:
        return render(request, "signup.html", "signup", {"error": "รหัสผ่านอย่างน้อย 6 ตัว", "ref": ref})
    user, err = create_client(username.strip(), email.strip(), password, referred_by=ref.strip() or None)
    if err:
        mark_login("signup", request, False, 6, 3600)
        return render(request, "signup.html", "signup", {"error": err, "ref": ref})
    request.session["user_id"] = user["id"]
    mark_login("signup", request, True, 6, 3600)
    add_log("สมัครสมาชิก %s" % user["username"], client_ip(request))
    return RedirectResponse("/neworder", status_code=303)


@router.get("/signin", response_class=HTMLResponse)
async def signin_get(request: Request):
    if current_user(request):
        return RedirectResponse("/neworder", status_code=303)
    err = request.session.pop("auth_error", "")
    return render(request, "signin.html", "signin", {"error": err or ""})


@router.get("/google-login")
async def google_login(request: Request):
    nxt = safe_next(request.query_params.get("next") or request.session.get("google_oauth_next") or "")
    if current_user(request):
        return RedirectResponse(nxt, status_code=303)
    if not google_on():
        request.session["auth_error"] = MSG["off"]
        return RedirectResponse("/signin", status_code=303)
    if not google_ready():
        request.session["auth_error"] = MSG["not_ready"]
        return RedirectResponse("/signin", status_code=303)
    gerr = request.query_params.get("error")
    if gerr:
        request.session["auth_error"] = google_error_message(gerr)
        return RedirectResponse("/signin", status_code=303)
    code = request.query_params.get("code")
    if not code:
        state = new_state()
        redirect_uri = google_redirect_uri(request)
        request.session["google_oauth_state"] = state
        request.session["google_oauth_redirect"] = redirect_uri
        request.session["google_oauth_next"] = nxt
        return RedirectResponse(google_auth_url(state, redirect_uri), status_code=302)
    saved = request.session.pop("google_oauth_state", "")
    state = request.query_params.get("state") or ""
    redirect_uri = request.session.pop("google_oauth_redirect", "") or google_redirect_uri(request)
    nxt = request.session.pop("google_oauth_next", "") or nxt
    if not saved or state != saved:
        request.session["auth_error"] = MSG["bad_state"]
        return RedirectResponse("/signin", status_code=303)
    try:
        profile = google_profile(code, redirect_uri)
    except Exception as exc:
        request.session["auth_error"] = google_error_message(getattr(exc, "args", [""])[0] if exc.args else "")
        return RedirectResponse("/signin", status_code=303)
    user, err = login_or_create_google(profile)
    if err or not user:
        request.session["auth_error"] = err or MSG["fail"]
        return RedirectResponse("/signin", status_code=303)
    request.session["user_id"] = user["id"]
    add_log("เข้าสู่ระบบด้วย Google %s" % user["username"], request.client.host if request.client else "-")
    return RedirectResponse(nxt or "/neworder", status_code=303)


@router.post("/signin")
async def signin_post(request: Request, username: str = Form(...), password: str = Form(...)):
    blocked = login_block("user_login", request, USER_FAILS, USER_LOCK)
    if blocked:
        return render(request, "signin.html", "signin", {"error": blocked})
    user = check_client(username.strip(), password)
    if not user:
        mark_login("user_login", request, False, USER_FAILS, USER_LOCK)
        return render(request, "signin.html", "signin", {"error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"})
    mark_login("user_login", request, True, USER_FAILS, USER_LOCK)
    request.session["user_id"] = user["id"]
    add_log("เข้าสู่ระบบ %s" % user["username"], client_ip(request))
    return RedirectResponse("/neworder", status_code=303)


@router.get("/forgot", response_class=HTMLResponse)
async def forgot_get(request: Request):
    if current_user(request):
        return RedirectResponse("/neworder", status_code=303)
    s = get_settings()
    if str(s.get("resetpass") or "1") == "0":
        return render(request, "signin.html", "signin", {"error": "ปิดรีเซ็ตรหัสผ่านชั่วคราว"})
    return render(request, "forgot.html", "signin")


@router.post("/forgot")
async def forgot_post(request: Request, email: str = Form(...)):
    from mail import send_mail, smtp_ready
    from pay import new_reset_token
    from content import SITE
    s = get_settings()
    if str(s.get("resetpass") or "1") == "0":
        return render(request, "signin.html", "signin", {"error": "ปิดรีเซ็ตรหัสผ่านชั่วคราว"})
    user = get_client(email=email.strip())
    msg = "ถ้าอีเมลนี้มีในระบบ เราจะส่งลิงก์รีเซ็ตให้"
    if user and smtp_ready(s):
        token = new_reset_token(user["email"])
        link = "%s/reset?token=%s" % (SITE.get("url") or "https://likes-auto.com", token)
        send_mail(user["email"], "รีเซ็ตรหัสผ่าน Likes Auto", "กดลิงก์นี้ภายใน 6 ชั่วโมง:\n%s\n" % link, s)
    return render(request, "forgot.html", "signin", {"ok": msg})


@router.get("/reset", response_class=HTMLResponse)
async def reset_get(request: Request, token: str = ""):
    if not token:
        return RedirectResponse("/forgot", status_code=303)
    return render(request, "reset.html", "signin", {"token": token})


@router.post("/reset")
async def reset_post(request: Request, token: str = Form(...), password: str = Form(...), confirm: str = Form(...)):
    from pay import use_reset_token
    from db import _hash, connect
    if password != confirm or len(password) < 6:
        return render(request, "reset.html", "signin", {"token": token, "error": "รหัสผ่านอย่างน้อย 6 ตัว และต้องตรงกัน"})
    row = use_reset_token(token)
    if not row:
        return render(request, "reset.html", "signin", {"token": token, "error": "ลิงก์หมดอายุหรือถูกใช้แล้ว"})
    con = connect()
    con.execute("UPDATE clients SET password_hash=? WHERE email=?", (_hash(password), row["email"]))
    con.commit()
    con.close()
    return render(request, "signin.html", "signin", {"ok": "ตั้งรหัสใหม่แล้ว เข้าสู่ระบบได้เลย"})


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse("/", status_code=303)


@router.get("/shop/services.json")
async def shop_services_json(
    request: Request,
    platform: str = "",
    category: str = "",
    q: str = "",
    sid: str = "",
    limit: int = 80,
):
    items = shop_services(platform, category, q, limit, 0, sid)
    return JSONResponse({"items": items}, headers={"Cache-Control": "public, max-age=15"})


@router.get("/neworder", response_class=HTMLResponse)
async def neworder_get(request: Request, cat: str = "", sid: str = ""):
    gate = need_mod(request, "mod_neworder")
    if gate:
        return gate
    user = current_user(request)
    return render(request, "neworder.html", "neworder", {
        "cat": cat,
        "sid": sid,
        "recent": enrich_orders(client_orders(user["username"])[:5]),
    })


@router.post("/neworder")
async def neworder_post(
    request: Request,
    service_id: int = Form(...),
    link: str = Form(""),
    quantity: int = Form(...),
    comments: str = Form(""),
):
    gate = need_mod(request, "mod_neworder")
    if gate:
        return gate
    user = current_user(request)
    oid, err = create_order(user["username"], service_id, link.strip(), quantity, comments.strip())
    extra = {"recent": enrich_orders(client_orders(user["username"])[:5])}
    if err:
        extra["error"] = err
        return render(request, "neworder.html", "neworder", extra)
    extra["ok"] = "สั่งซื้อแล้ว หมายเลขออเดอร์ #%s" % oid
    extra["oid"] = oid
    extra["user"] = get_client(client_id=user["id"])
    extra["recent"] = enrich_orders(client_orders(user["username"])[:5])
    return render(request, "neworder.html", "neworder", extra)


@router.get("/orders", response_class=HTMLResponse)
async def orders(request: Request, q: str = "", status: str = "", p: int = 1):
    gate = need_mod(request, "mod_orders")
    if gate:
        return gate
    user = current_user(request)
    items = enrich_orders(client_orders(user["username"]))
    counts = order_counts(items)
    filtered = filter_orders(items, q, status)
    per = 20
    total = len(filtered)
    pages = max(1, (total + per - 1) // per)
    page_n = max(1, min(int(p or 1), pages))
    start = (page_n - 1) * per
    return render(request, "orders.html", "orders", {
        "orders": filtered[start:start + per],
        "q": q,
        "status": _norm_status(status),
        "counts": counts,
        "total": total,
        "page_n": page_n,
        "pages": pages if total > per else 1,
    })


def _pay_extra(user, extra=None):
    from pay import KIND_LABEL, active_methods, checkout_info
    data = {
        "payments": client_payments(user["username"]),
        "pay_methods": active_methods(),
        "pay_st": {
            "pending": "รอแนบสลิป",
            "paid": "อนุมัติแล้ว",
            "canceled": "ปฏิเสธ",
        },
        "kind_label": KIND_LABEL,
        "auto_check": True,
        "pp_method": None,
    }
    methods = data["pay_methods"] or []
    data["pp_method"] = next((m for m in methods if (m.get("kind") or "") == "promptpay"), methods[0] if methods else None)
    try:
        from slip_verify import slip_api_ready
        data["auto_check"] = slip_api_ready(get_settings())
    except Exception:
        pass
    if extra:
        data.update(extra)
    if data.get("pay"):
        data["checkout"] = checkout_info(data["pay"], get_settings(), data.get("banks") or [])
    return data


def _slip_check_job(pid, path):
    import time

    from pay import get_payment, set_pay_note
    from slip_verify import auto_credit_from_slip, verify_error_text

    last = "timeout"
    try:
        for attempt in range(3):
            pay = get_payment(pid)
            if not pay or pay.get("status") != "pending":
                set_pay_note(pid, "")
                return
            paid, code = auto_credit_from_slip(pid, path, "", count_try=(attempt == 0))
            last = code
            if paid:
                set_pay_note(pid, "")
                return
            if code in ("amount", "receiver", "duplicate", "stale", "no_ref", "not_slip", "no_qr", "not_pending", "off", "no_slip"):
                break
            time.sleep(2.5 * (attempt + 1))
        set_pay_note(pid, verify_error_text(last))
    except Exception:
        set_pay_note(pid, "ตรวจสลิปไม่ผ่าน รอแอดมินตรวจสอบ")


@router.get("/addfunds", response_class=HTMLResponse)
async def addfunds_get(request: Request):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return gate
    from pay import get_payment
    user = current_user(request)
    extra = {}
    wait = str(request.query_params.get("wait") or "").strip()
    if request.query_params.get("paid"):
        extra["pay_result"] = "paid"
        extra["ok"] = "ระบบตรวจสลิปแล้ว เข้ากระเป๋าแล้ว"
    elif wait.isdigit():
        pay = get_payment(int(wait))
        extra["wait_pid"] = int(wait)
        if pay and pay.get("client") == user["username"]:
            extra["pay"] = pay
            note = str(pay.get("note") or "")
            if pay.get("status") == "paid":
                extra["pay_result"] = "paid"
                extra["ok"] = "เติมเครดิตสำเร็จ %.2f บาท" % float(pay.get("amount") or 0)
            elif note.startswith("กำลังตรวจ"):
                extra["pay_result"] = "checking"
                extra["ok"] = "รับสลิปแล้ว กำลังตรวจยอด ผลจะขึ้นที่ประวัติด้านล่าง"
            elif note:
                extra["pay_result"] = "fail"
                extra["error"] = note
            else:
                extra["pay_result"] = "checking"
                extra["ok"] = "รับสลิปแล้ว กำลังตรวจยอด ผลจะขึ้นที่ประวัติด้านล่าง"
    return render(request, "addfunds.html", "addfunds", _pay_extra(user, extra))


@router.post("/addfunds")
async def addfunds_post(request: Request, amount: float = Form(...), method_id: int = Form(0), method: str = Form("")):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return gate
    user = current_user(request)
    if not method_id:
        from pay import active_methods
        methods = active_methods()
        pp = next((m for m in methods if (m.get("kind") or "") == "promptpay"), None)
        method_id = (pp or (methods[0] if methods else {})).get("id") or 0
    pid, err = create_payment(user["username"], method, amount, method_id or None)
    if err:
        return render(request, "addfunds.html", "addfunds", _pay_extra(user, {"error": err}))
    return RedirectResponse("/addfunds/pay/%s" % pid, status_code=303)


@router.get("/addfunds/pay/{pid}", response_class=HTMLResponse)
async def addfunds_pay(request: Request, pid: int):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return gate
    from pay import get_payment
    user = current_user(request)
    pay = get_payment(pid)
    if not pay or pay.get("client") != user["username"]:
        return RedirectResponse("/addfunds", status_code=303)
    extra = {"pay": pay}
    if request.query_params.get("paid"):
        extra["ok"] = "ระบบตรวจสลิปแล้ว เข้ากระเป๋าแล้ว"
    elif request.query_params.get("ok"):
        extra["ok"] = "รับสลิปแล้ว หากยังไม่เข้าเครดิต ให้แนบใหม่ให้เห็น QR บนสลิป"
    return render(request, "addfunds.html", "addfunds", _pay_extra(user, extra))


@router.post("/addfunds/pay/{pid}/slip")
async def addfunds_slip(request: Request, pid: int, background_tasks: BackgroundTasks):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return gate
    from pay import attach_slip, get_payment, save_slip_bytes
    user = current_user(request)
    pay = get_payment(pid)
    wants_json = "application/json" in (request.headers.get("accept") or "").lower()

    def fail(msg, code="error"):
        if wants_json:
            return JSONResponse({"ok": False, "code": code, "message": msg})
        return render(request, "addfunds.html", "addfunds", _pay_extra(user, {"pay": get_payment(pid), "error": msg}))

    def done(paid, code=""):
        if paid:
            if wants_json:
                return JSONResponse({"ok": True, "paid": True, "code": "paid"})
            return RedirectResponse("/addfunds/pay/%s?paid=1" % pid, status_code=303)
        msg = ""
        try:
            from slip_verify import verify_error_text
            msg = verify_error_text(code)
        except Exception:
            msg = "รับสลิปแล้ว รอแอดมินตรวจสอบ"
        if wants_json:
            return JSONResponse({"ok": True, "paid": False, "code": code or "wait", "message": msg})
        extra = {"pay": get_payment(pid), "ok": "รับสลิปแล้ว"}
        if msg:
            extra["error"] = msg
        return render(request, "addfunds.html", "addfunds", _pay_extra(user, extra))

    if not pay or pay.get("client") != user["username"] or pay.get("status") != "pending":
        if wants_json:
            return JSONResponse({"ok": False, "code": "not_pending", "message": "รายการนี้ใช้ไม่ได้แล้ว"})
        return RedirectResponse("/addfunds", status_code=303)
    form = await request.form()
    note = "กำลังตรวจสลิป"
    slip = form.get("slip")
    err = ""
    path = pay.get("slip") or ""
    has_file = slip is not None and (getattr(slip, "filename", None) or getattr(slip, "size", 0))
    if has_file:
        raw = b""
        try:
            raw = await slip.read()
        except Exception:
            raw = slip.file.read() if hasattr(slip, "file") else b""
        path, ferr = save_slip_bytes(raw, pid, getattr(slip, "filename", "") or "")
        if ferr:
            err = {
                "file_type": "อัปโหลดได้เฉพาะรูป JPG PNG WEBP หรือไฟล์ PDF",
                "file_size": "ไฟล์ใหญ่เกิน 8MB",
                "file_read": "อ่านไฟล์ไม่สำเร็จ",
                "file_bad": "ไฟล์ไม่ถูกต้อง",
            }.get(ferr, "อัปโหลดไม่สำเร็จ")
    elif not path:
        err = "กรุณาอัปโหลดสลิปจากแอปธนาคาร"
    if not err:
        if not attach_slip(pid, user["username"], path, note):
            err = "บันทึกสลิปไม่สำเร็จ"
    if err:
        return fail(err)
    add_log("อัปโหลดสลิปเติมเงิน #%s" % pid, request.client.host if request.client else "-")
    threading.Thread(target=_slip_check_job, args=(pid, path), daemon=True).start()
    if wants_json:
        return JSONResponse({
            "ok": True,
            "paid": False,
            "code": "checking",
            "message": "รับสลิปแล้ว กำลังตรวจยอด ผลจะขึ้นที่ประวัติด้านล่าง",
            "redirect": "/addfunds?wait=%s" % pid,
        })
    return RedirectResponse("/addfunds?wait=%s" % pid, status_code=303)


@router.get("/addfunds/pay/{pid}/qr.png")
async def addfunds_qr_png(request: Request, pid: int):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return gate
    from pay import checkout_info, get_payment, qr_png_bytes
    user = current_user(request)
    pay = get_payment(pid)
    if not pay or pay.get("client") != user["username"]:
        return Response(status_code=404)
    info = checkout_info(pay, get_settings())
    payload = info.get("payload") or ""
    if not payload:
        return Response(status_code=404)
    try:
        png = qr_png_bytes(payload)
    except Exception:
        return Response(status_code=500)
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/addfunds/pay/{pid}/status")
async def addfunds_status(request: Request, pid: int):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return JSONResponse({"status": "auth"}, status_code=401)
    from pay import get_payment
    user = current_user(request)
    pay = get_payment(pid)
    if not pay or pay.get("client") != user["username"]:
        return JSONResponse({"status": "missing"}, status_code=404)
    note = str(pay.get("note") or "")
    pending = pay.get("status") == "pending"
    checking = pending and bool(pay.get("slip")) and (note.startswith("กำลังตรวจ") or not note)
    return JSONResponse({
        "status": pay.get("status"),
        "amount": pay.get("amount"),
        "balance": user.get("balance") or 0,
        "checking": checking,
        "message": note if pending and note and not note.startswith("กำลังตรวจ") else "",
    })


@router.post("/addfunds/pay/{pid}/confirm")
async def addfunds_confirm(request: Request, pid: int):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return JSONResponse({"ok": False, "code": "auth"}, status_code=401)
    return JSONResponse({
        "ok": False,
        "code": "slip_only",
        "message": "กรุณาแนบสลิปจากแอปธนาคาร เพื่อให้ระบบตรวจยอด",
    })


@router.post("/addfunds/pay/{pid}/cancel")
async def addfunds_cancel(request: Request, pid: int):
    gate = need_mod(request, "mod_addfunds")
    if gate:
        return gate
    from pay import cancel_own_payment
    user = current_user(request)
    cancel_own_payment(pid, user["username"])
    return RedirectResponse("/addfunds", status_code=303)


@router.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    gate = need_mod(request, "mod_account")
    if gate:
        return gate
    return render(request, "account.html", "account")


@router.get("/tickets", response_class=HTMLResponse)
async def tickets_get(request: Request):
    gate = need_mod(request, "mod_tickets")
    if gate:
        return gate
    user = current_user(request)
    tickets = client_tickets(user["username"])
    return render(request, "tickets.html", "tickets", {
        "tickets": tickets,
        "replies": all_ticket_replies(),
        "ticket_open": sum(1 for t in tickets if (t.get("status") or "") in {"open", "answered"}),
        "ticket_closed": sum(1 for t in tickets if (t.get("status") or "") == "closed"),
    })


@router.post("/tickets")
async def tickets_post(request: Request, subject: str = Form(...), message: str = Form(...)):
    gate = need_mod(request, "mod_tickets")
    if gate:
        return gate
    user = current_user(request)
    create_ticket(user["username"], subject.strip(), message.strip())
    tickets = client_tickets(user["username"])
    return render(request, "tickets.html", "tickets", {
        "ok": "เปิดตั๋วแล้ว",
        "tickets": tickets,
        "replies": all_ticket_replies(),
        "ticket_open": sum(1 for t in tickets if (t.get("status") or "") in {"open", "answered"}),
        "ticket_closed": sum(1 for t in tickets if (t.get("status") or "") == "closed"),
    })


@router.post("/tickets/{tid}/reply")
async def tickets_user_reply(request: Request, tid: int, message: str = Form(...)):
    gate = need_mod(request, "mod_tickets")
    if gate:
        return gate
    user = current_user(request)
    row = fetch_one("SELECT * FROM tickets WHERE id=? AND client=?", (tid, user["username"]))
    extra = {
        "tickets": client_tickets(user["username"]),
        "replies": all_ticket_replies(),
    }
    extra["ticket_open"] = sum(1 for t in extra["tickets"] if (t.get("status") or "") in {"open", "answered"})
    extra["ticket_closed"] = sum(1 for t in extra["tickets"] if (t.get("status") or "") == "closed")
    if not row or row.get("status") == "closed":
        extra["error"] = "ตอบตั๋วนี้ไม่ได้"
        return render(request, "tickets.html", "tickets", extra)
    reply_ticket(tid, user["username"], message.strip(), "open")
    extra["ok"] = "ส่งข้อความแล้ว"
    extra["tickets"] = client_tickets(user["username"])
    extra["replies"] = all_ticket_replies()
    extra["ticket_open"] = sum(1 for t in extra["tickets"] if (t.get("status") or "") in {"open", "answered"})
    extra["ticket_closed"] = sum(1 for t in extra["tickets"] if (t.get("status") or "") == "closed")
    return render(request, "tickets.html", "tickets", extra)


@router.get("/dripfeeds", response_class=HTMLResponse)
async def drip_get(request: Request):
    gate = need_mod(request, "mod_dripfeed")
    if gate:
        return gate
    user = current_user(request)
    return render(request, "dripfeeds.html", "dripfeeds", {"items": fetch_all("SELECT * FROM dripfeeds WHERE client=? ORDER BY id DESC", (user["username"],))})


@router.post("/dripfeeds")
async def drip_post(request: Request, service_id: int = Form(...), link: str = Form(...), quantity: int = Form(...), runs: int = Form(...), interval_min: int = Form(...)):
    gate = need_mod(request, "mod_dripfeed")
    if gate:
        return gate
    user = current_user(request)
    did, err = create_dripfeed(user["username"], service_id, link.strip(), quantity, runs, interval_min)
    items = fetch_all("SELECT * FROM dripfeeds WHERE client=? ORDER BY id DESC", (user["username"],))
    extra = {"items": items, "user": get_client(client_id=user["id"])}
    if err:
        extra["error"] = err
    else:
        extra["ok"] = "เปิด Drip-feed #%s แล้ว" % did
    return render(request, "dripfeeds.html", "dripfeeds", extra)


@router.get("/subscriptions", response_class=HTMLResponse)
async def sub_get(request: Request):
    gate = need_mod(request, "mod_subscription")
    if gate:
        return gate
    user = current_user(request)
    return render(request, "subscriptions.html", "subscriptions", {"items": fetch_all("SELECT * FROM subscriptions WHERE client=? ORDER BY id DESC", (user["username"],))})


@router.post("/subscriptions")
async def sub_post(request: Request, service_id: int = Form(...), target: str = Form(...), min_qty: int = Form(...), max_qty: int = Form(...), posts: int = Form(...), delay: int = Form(...)):
    gate = need_mod(request, "mod_subscription")
    if gate:
        return gate
    user = current_user(request)
    sid, err = create_subscription(user["username"], service_id, target.strip(), min_qty, max_qty, posts, delay)
    items = fetch_all("SELECT * FROM subscriptions WHERE client=? ORDER BY id DESC", (user["username"],))
    extra = {"items": items, "user": get_client(client_id=user["id"])}
    if err:
        extra["error"] = err
    else:
        extra["ok"] = "เปิด Subscription #%s แล้ว" % sid
    return render(request, "subscriptions.html", "subscriptions", extra)


@router.get("/affiliates", response_class=HTMLResponse)
async def aff_get(request: Request):
    gate = need_mod(request, "mod_affiliate")
    if gate:
        return gate
    user = current_user(request)
    ref_count = 0
    if user:
        row = fetch_one(
            "SELECT COUNT(*) c FROM clients WHERE referred_by=? OR referred_by=?",
            (user.get("username"), user.get("ref_code")),
        )
        ref_count = int((row or {}).get("c") or 0)
    return render(request, "affiliates.html", "affiliates", {"ref_count": ref_count})


@router.get("/panels", response_class=HTMLResponse)
async def panels_get(request: Request):
    gate = need_mod(request, "mod_child")
    if gate:
        return gate
    user = current_user(request)
    items = fetch_all("SELECT * FROM child_panels WHERE client=? ORDER BY id DESC", (user["username"],))
    return render(request, "panels.html", "panels", {
        "items": items,
        "panel_open": sum(1 for x in items if (x.get("status") or "") in {"pending", "active"}),
        "panel_active": sum(1 for x in items if (x.get("status") or "") == "active"),
        "panel_st": {
            "pending": "รออนุมัติ",
            "active": "เปิดใช้งานแล้ว",
            "canceled": "ยกเลิก/คืนเงิน",
        },
    })


@router.post("/panels")
async def panels_post(
    request: Request,
    domain: str = Form(...),
    admin_user: str = Form(...),
    admin_pass: str = Form(...),
    admin_pass2: str = Form(...),
    currency: str = Form("THB"),
):
    gate = need_mod(request, "mod_child")
    if gate:
        return gate
    user = current_user(request)
    extra = {
        "panel_st": {
            "pending": "รออนุมัติ",
            "active": "เปิดใช้งานแล้ว",
            "canceled": "ยกเลิก/คืนเงิน",
        },
    }
    if (admin_pass or "").strip() != (admin_pass2 or "").strip():
        items = fetch_all("SELECT * FROM child_panels WHERE client=? ORDER BY id DESC", (user["username"],))
        extra.update({
            "error": "รหัสผ่านยืนยันไม่ตรงกัน",
            "items": items,
            "panel_open": sum(1 for x in items if (x.get("status") or "") in {"pending", "active"}),
            "panel_active": sum(1 for x in items if (x.get("status") or "") == "active"),
            "user": get_client(client_id=user["id"]),
        })
        return render(request, "panels.html", "panels", extra)
    pid, err = create_child_panel(
        user["username"],
        domain.strip().lower(),
        admin_user=admin_user,
        admin_pass=admin_pass,
        currency=currency,
    )
    items = fetch_all("SELECT * FROM child_panels WHERE client=? ORDER BY id DESC", (user["username"],))
    extra.update({
        "items": items,
        "user": get_client(client_id=user["id"]),
        "panel_open": sum(1 for x in items if (x.get("status") or "") in {"pending", "active"}),
        "panel_active": sum(1 for x in items if (x.get("status") or "") == "active"),
    })
    if err:
        extra["error"] = err
    else:
        extra["ok"] = "ส่งคำขอแผงลูก #%s แล้ว — ตั้ง Nameserver ตามคู่มือด้านล่าง แล้วรอทีมเปิดภายใน 2–24 ชม." % pid
        extra["focus_form"] = False
    return render(request, "panels.html", "panels", extra)


@router.post("/account/password")
async def account_password(request: Request, old_password: str = Form(...), new_password: str = Form(...)):
    gate = need_mod(request, "mod_account")
    if gate:
        return gate
    user = current_user(request)
    ok, err = change_client_password(user["username"], old_password, new_password)
    extra = {}
    if ok:
        extra["ok"] = "เปลี่ยนรหัสแล้ว"
    else:
        extra["error"] = err
    return render(request, "account.html", "account", extra)


@router.post("/account/apikey")
async def account_apikey(request: Request):
    gate = need_mod(request, "mod_account", "mod_api")
    if gate:
        return gate
    user = current_user(request)
    regenerate_api_key(user["id"])
    return render(request, "account.html", "account", {"ok": "สร้าง API key ใหม่แล้ว", "user": get_client(client_id=user["id"])})


@router.post("/account/transfer")
async def account_transfer(request: Request, receiver: str = Form(...), amount: float = Form(...)):
    gate = need_mod(request, "mod_account", "mod_transfer")
    if gate:
        return gate
    user = current_user(request)
    ok, err = transfer_funds(user["username"], receiver.strip(), amount)
    extra = {"user": get_client(client_id=user["id"])}
    if ok:
        extra["ok"] = "โอนเงินแล้ว"
    else:
        extra["error"] = err
    return render(request, "account.html", "account", extra)


@router.post("/orders/{oid}/refill")
async def order_refill(request: Request, oid: int):
    gate = need_mod(request, "mod_orders")
    if gate:
        return gate
    user = current_user(request)
    order = None
    for row in client_orders(user["username"]):
        if row["id"] == oid:
            order = row
            break
    if not order:
        return RedirectResponse("/orders", status_code=303)
    enriched = enrich_orders([order])[0]
    if not enriched.get("can_refill"):
        extra = {
            "orders": enrich_orders(client_orders(user["username"]))[:20],
            "counts": order_counts(enrich_orders(client_orders(user["username"]))),
            "q": "",
            "status": "",
            "total": len(client_orders(user["username"])),
            "page_n": 1,
            "pages": 1,
            "error": "บริการนี้ไม่รองรับการเติมยอด (ไม่มีรับประกัน)",
        }
        return render(request, "orders.html", "orders", extra)
    _, err = create_task(oid, user["username"], "refill")
    extra = {
        "orders": enrich_orders(client_orders(user["username"]))[:20],
        "counts": order_counts(enrich_orders(client_orders(user["username"]))),
        "q": "",
        "status": "",
        "total": len(client_orders(user["username"])),
        "page_n": 1,
        "pages": 1,
    }
    extra["ok" if not err else "error"] = "ส่งคำขอเติมแล้ว" if not err else err
    return render(request, "orders.html", "orders", extra)


@router.post("/orders/{oid}/cancel")
async def order_cancel(request: Request, oid: int):
    gate = need_mod(request, "mod_orders")
    if gate:
        return gate
    user = current_user(request)
    items = enrich_orders(client_orders(user["username"]))
    extra = {
        "orders": items[:20],
        "counts": order_counts(items),
        "q": "",
        "status": "",
        "total": len(items),
        "page_n": 1,
        "pages": 1,
    }
    order = None
    for row in items:
        if row["id"] == oid:
            order = row
            break
    if not order:
        return RedirectResponse("/orders", status_code=303)
    if order.get("status") not in {"pending", "processing", "inprogress"}:
        extra["error"] = "ยกเลิกสถานะนี้ไม่ได้"
        return render(request, "orders.html", "orders", extra)
    _, err = create_task(oid, user["username"], "cancel")
    items = enrich_orders(client_orders(user["username"]))
    extra["orders"] = items[:20]
    extra["counts"] = order_counts(items)
    extra["ok" if not err else "error"] = "ส่งคำขอยกเลิกแล้ว" if not err else err
    return render(request, "orders.html", "orders", extra)