from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from guard import ADMIN_FAILS, ADMIN_LOCK, admin_session_ok, client_ip, ensure_csrf, lock_left, login_block, mark_login

from db import (
    add_log,
    approve_payment,
    check_admin,
    delete_provider,
    get_provider,
    get_settings,
    init_db,
    list_admin_services,
    count_admin_services,
    list_cron_logs,
    cron_log_job_counts,
    list_providers,
    list_shop_mains,
    list_shop_subs,
    reject_payment,
    rows,
    connect,
    get_order,
    refund_order,
    save_provider,
    save_provider_balance,
    save_settings,
    stats,
    dashboard_series,
    update_order,
)
from cron_jobs import run_all
from smm_api import action

ROOT = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))
router = APIRouter(prefix="/admin")

NAV_GROUPS = [
    ("งานประจำ", [
        ("dashboard", "/admin", "ภาพรวม", "ri-home-5-line"),
        ("orders", "/admin/orders", "ออเดอร์", "ri-shopping-bag-3-line"),
        ("payments", "/admin/payments", "เติมเงิน", "ri-wallet-3-line"),
        ("tickets", "/admin/tickets", "ตั๋ว", "ri-customer-service-2-line"),
    ]),
    ("ร้านค้า", [
        ("clients", "/admin/clients", "ลูกค้า", "ri-group-line"),
        ("services", "/admin/services", "บริการ", "ri-service-line"),
        ("providers", "/admin/providers", "ผู้ให้บริการ", "ri-server-line"),
    ]),
    ("ระบบ", [
        ("crons", "/admin/crons", "บันทึกงาน", "ri-file-list-3-line"),
        ("reports", "/admin/reports", "รายได้", "ri-bar-chart-2-line"),
        ("news", "/admin/appearance/pages", "หน้าเว็บ", "ri-palette-line"),
        ("settings", "/admin/settings/general", "ตั้งค่า", "ri-settings-3-line"),
    ]),
]
NAV = [item for _, items in NAV_GROUPS for item in items]
SECTION = {
    "dripfeeds": "orders",
    "subscriptions": "orders",
    "tasks": "orders",
    "affiliates": "clients",
    "panels": "clients",
    "account": "settings",
    "staff": "settings",
    "logs": "settings",
}
ORDER_TABS = [
    ("orders", "/admin/orders", "ออเดอร์"),
    ("dripfeeds", "/admin/dripfeeds", "ส่งทีละรอบ"),
    ("subscriptions", "/admin/subscriptions", "เติมอัตโนมัติ"),
    ("tasks", "/admin/tasks", "ขอเติม"),
]
CLIENT_TABS = [
    ("clients", "/admin/clients", "ลูกค้า"),
    ("affiliates", "/admin/affiliates", "แนะนำเพื่อน"),
    ("panels", "/admin/panels", "แผงลูก"),
]
SETTING_TABS_UI = [
    ("general", "/admin/settings/general", "ทั่วไป"),
    ("currency", "/admin/settings/currency", "เรทเงิน"),
    ("payments", "/admin/settings/payments", "ช่องทางจ่าย"),
    ("banks", "/admin/settings/banks", "บัญชีธนาคาร"),
    ("bonuses", "/admin/settings/bonuses", "โบนัส"),
    ("alerts", "/admin/settings/alerts", "แจ้งเตือน"),
    ("modules", "/admin/settings/modules", "เปิด-ปิดระบบ"),
    ("integrations", "/admin/settings/integrations", "เชื่อมต่อ"),
    ("subjects", "/admin/settings/subjects", "หัวข้อตั๋ว"),
    ("account", "/admin/account", "รหัสแอดมิน"),
    ("staff", "/admin/staff", "พนักงาน"),
    ("logs", "/admin/logs", "บันทึก"),
]
APPEAR_TABS = [
    ("themes", "/admin/appearance/themes", "ธีมเว็บ"),
    ("pages", "/admin/appearance/pages", "หน้าเว็บ"),
    ("news", "/admin/news", "ประกาศ"),
    ("blog", "/admin/appearance/blog", "บล็อก"),
    ("menu", "/admin/appearance/menu", "เมนู"),
    ("files", "/admin/appearance/files", "ไฟล์"),
]
PAGE_TABS = {
    "orders": ORDER_TABS,
    "dripfeeds": ORDER_TABS,
    "subscriptions": ORDER_TABS,
    "tasks": ORDER_TABS,
    "clients": CLIENT_TABS,
    "affiliates": CLIENT_TABS,
    "panels": CLIENT_TABS,
    "news": APPEAR_TABS,
    "settings": SETTING_TABS_UI,
    "account": SETTING_TABS_UI,
    "staff": SETTING_TABS_UI,
    "logs": SETTING_TABS_UI,
}


def logged_in(request: Request) -> bool:
    return bool(request.session.get("admin"))


def require_admin(request: Request):
    if not admin_session_ok(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None


def render(request: Request, template: str, extra=None):
    extra = extra or {}
    page = extra.get("page") or "dashboard"
    section = extra.get("section") or SECTION.get(page, page)
    ctx = {
        "request": request,
        "nav": NAV,
        "nav_groups": NAV_GROUPS,
        "page": page,
        "section": section,
        "tabs": extra.get("tabs") if "tabs" in extra else PAGE_TABS.get(page),
        "tab": extra.get("tab") or page,
        "admin_name": request.session.get("admin", "admin"),
        "alerts": extra.get("alerts"),
        "csrf": "",
        "st": {
            "pending": "รอส่ง",
            "processing": "กำลังทำ",
            "inprogress": "กำลังทำ",
            "completed": "สำเร็จ",
            "partial": "บางส่วน",
            "canceled": "ยกเลิก",
            "paid": "อนุมัติแล้ว",
            "open": "เปิด",
            "answered": "ตอบแล้ว",
            "closed": "ปิด",
            "active": "ใช้งาน",
            "paused": "พัก",
            "success": "สำเร็จ",
            "failed": "ไม่สำเร็จ",
            "waiting": "รอตรวจ",
            "unpaid": "ยังไม่จ่าย",
        },
    }
    ctx.update(extra)
    if "tabs" not in extra:
        ctx["tabs"] = PAGE_TABS.get(page)
    if page != "login" and not ctx.get("alerts"):
        try:
            from store import report_data
            ctx["alerts"] = report_data()
        except Exception:
            ctx["alerts"] = {}
    ctx.setdefault("alerts", {})
    try:
        ctx["csrf"] = ensure_csrf(request)
    except Exception:
        ctx["csrf"] = ""
    return templates.TemplateResponse(request, template, ctx)


def login_page(request: Request, error="", username=""):
    left = 0
    try:
        left = lock_left("admin_login", client_ip(request))
    except Exception:
        left = 0
    return render(request, "admin/login.html", {
        "page": "login",
        "error": error or "",
        "username": username or "",
        "lock_left": left,
        "locked": left > 0,
    })


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    init_db()
    if logged_in(request):
        return RedirectResponse("/admin", status_code=303)
    return login_page(request)


@router.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...), la_hp_x9: str = Form("")):
    init_db()
    name = (username or "").strip()[:80]
    if (la_hp_x9 or "").strip():
        return login_page(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    blocked = login_block("admin_login", request, ADMIN_FAILS, ADMIN_LOCK)
    if blocked:
        return login_page(request, blocked, name)
    ip = client_ip(request)
    if check_admin(name, password):
        request.session.clear()
        request.session["admin"] = name
        request.session["admin_at"] = __import__("time").time()
        ensure_csrf(request)
        mark_login("admin_login", request, True, ADMIN_FAILS, ADMIN_LOCK)
        add_log("เข้าสู่ระบบแอดมิน", ip)
        try:
            from cms import add_guard
            add_guard(name, ip, True)
        except Exception:
            pass
        return RedirectResponse("/admin", status_code=303)
    mark_login("admin_login", request, False, ADMIN_FAILS, ADMIN_LOCK)
    try:
        from cms import add_guard
        add_guard(name, ip, False)
    except Exception:
        pass
    return login_page(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", name)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    gate = require_admin(request)
    if gate:
        return gate
    init_db()
    from store import report_data
    pays = [p for p in rows("payments", 40) if p.get("status") == "pending"][:6]
    ticks = [t for t in rows("tickets", 40) if t.get("status") in ("open", "answered")][:6]
    return render(request, "admin/dashboard.html", {
        "page": "dashboard",
        "stats": stats(),
        "report": report_data(),
        "orders": rows("orders", 8),
        "pending_pay": pays,
        "open_tickets": ticks,
        "series": dashboard_series(14),
    })


def _ord_back(q="", status="", ok="", err="", page=""):
    parts = []
    if q:
        parts.append("q=" + quote_plus(q))
    if status in ("pending", "processing", "completed", "partial", "canceled"):
        parts.append("status=" + status)
    if page and str(page) not in ("", "1"):
        parts.append("page=" + str(page))
    if ok:
        parts.append("ok=" + quote_plus(ok))
    if err:
        parts.append("err=" + quote_plus(err))
    return RedirectResponse("/admin/orders" + (("?" + "&".join(parts)) if parts else ""), status_code=303)


def _enrich_order(row):
    item = dict(row)
    st = str(item.get("status") or "")
    if st == "inprogress":
        item["status"] = "processing"
        st = "processing"
    qty = int(item.get("quantity") or 0)
    rem = None
    try:
        if item.get("remains") not in (None, "", "-"):
            rem = int(float(item.get("remains")))
    except Exception:
        rem = None
    if rem is not None and qty > 0:
        done = max(0, min(qty, qty - rem))
        item["progress"] = int(round(done * 100 / qty))
        item["done"] = done
        item["remains_n"] = rem
    elif st == "completed":
        item["progress"] = 100
        item["done"] = qty
        item["remains_n"] = 0
    elif st in ("pending", "canceled"):
        item["progress"] = 0
        item["done"] = 0
        item["remains_n"] = qty
    else:
        item["progress"] = None
        item["done"] = None
        item["remains_n"] = rem
    err = str(item.get("api_error") or "").strip()
    item["has_error"] = bool(err and err not in ("-", "None"))
    item["can_send"] = not item.get("api_orderid")
    item["can_sync"] = bool(item.get("api_orderid"))
    item["can_refund"] = not int(item.get("refunded") or 0)
    return item


@router.get("/orders", response_class=HTMLResponse)
async def orders(request: Request, q: str = "", status: str = "", ok: str = "", err: str = "", page: int = 1):
    gate = require_admin(request)
    if gate:
        return gate
    q = (q or "").strip()
    page = max(int(page or 1), 1)
    per_page = 40
    where = []
    args = []
    if status == "processing":
        where.append("o.status IN ('processing','inprogress')")
    elif status in ("pending", "completed", "partial", "canceled"):
        where.append("o.status=?")
        args.append(status)
    if q:
        like = "%" + q + "%"
        qid = q.lstrip("#")
        if qid.isdigit():
            where.append("(o.id=? OR o.client LIKE ? OR o.service LIKE ? OR IFNULL(o.link,'') LIKE ? OR IFNULL(o.api_orderid,'') LIKE ?)")
            args.extend([int(qid), like, like, like, like])
        else:
            where.append("(o.client LIKE ? OR o.service LIKE ? OR IFNULL(o.link,'') LIKE ? OR IFNULL(o.api_orderid,'') LIKE ?)")
            args.extend([like, like, like, like])
    sql_where = (" WHERE " + " AND ".join(where)) if where else ""
    con = connect()
    total = int(con.execute("SELECT COUNT(*) c FROM orders o" + sql_where, args).fetchone()["c"])
    pages = max((total + per_page - 1) // per_page, 1)
    if page > pages:
        page = pages
    counts = {"all_n": 0, "pending_n": 0, "processing_n": 0, "completed_n": 0, "partial_n": 0, "canceled_n": 0}
    for r in con.execute("SELECT status, COUNT(*) n FROM orders GROUP BY status").fetchall():
        st = r["status"] or ""
        n = int(r["n"] or 0)
        counts["all_n"] += n
        key = "processing" if st in ("processing", "inprogress") else st
        bucket = key + "_n"
        if bucket in counts:
            counts[bucket] += n
    order_sql = """
        SELECT o.*, p.name AS provider_name
        FROM orders o
        LEFT JOIN providers p ON p.id = o.provider_id
        %s
        ORDER BY CASE o.status
            WHEN 'pending' THEN 0
            WHEN 'processing' THEN 1
            WHEN 'inprogress' THEN 1
            WHEN 'partial' THEN 2
            ELSE 3 END, o.id DESC
        LIMIT ? OFFSET ?
    """ % sql_where
    items = [dict(x) for x in con.execute(order_sql, args + [per_page, (page - 1) * per_page]).fetchall()]
    con.close()
    return render(request, "admin/orders.html", {
        "page": "orders",
        "rows": [_enrich_order(r) for r in items],
        "q": q,
        "status": status,
        "ok": ok,
        "err": err,
        "ord_sum": counts,
        "page_no": page,
        "pages": pages,
        "total": total,
    })


@router.post("/orders/{oid}/status")
async def orders_status(request: Request, oid: int, status: str = Form(...), q: str = Form(""), filter_status: str = Form(""), page: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    allowed = {"pending", "processing", "completed", "partial", "canceled"}
    if status not in allowed:
        return _ord_back(q, filter_status, err="สถานะไม่ถูกต้อง", page=page)
    row = get_order(oid)
    if not row:
        return _ord_back(q, filter_status, err="ไม่พบออเดอร์", page=page)
    if str(row.get("status") or "") == status:
        return _ord_back(q, filter_status, page=page)
    update_order(oid, status=status)
    add_log("เปลี่ยนสถานะออเดอร์ #%s เป็น %s" % (oid, status), request.client.host if request.client else "-")
    return _ord_back(q, filter_status, ok="อัปเดตสถานะแล้ว", page=page)


@router.post("/orders/{oid}/resend")
async def orders_resend(request: Request, oid: int, q: str = Form(""), filter_status: str = Form(""), page: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    from cron_jobs import send_one_order
    ok, msg = send_one_order(oid)
    add_log("ส่งออเดอร์ #%s ไป API %s" % (oid, "สำเร็จ" if ok else "ไม่สำเร็จ"), request.client.host if request.client else "-")
    if ok:
        return _ord_back(q, filter_status, ok="ส่งไป API แล้ว รหัส " + str(msg), page=page)
    return _ord_back(q, filter_status, err="ส่ง API ไม่สำเร็จ: " + str(msg), page=page)


@router.post("/orders/{oid}/sync")
async def orders_sync(request: Request, oid: int, q: str = Form(""), filter_status: str = Form(""), page: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    from cron_jobs import check_one_order
    ok, msg = check_one_order(oid)
    add_log("ดึงสถานะออเดอร์ #%s %s" % (oid, msg), request.client.host if request.client else "-")
    if ok:
        return _ord_back(q, filter_status, ok="อัปเดตจากผู้ให้บริการแล้ว", page=page)
    return _ord_back(q, filter_status, err="ดึงสถานะไม่สำเร็จ: " + str(msg), page=page)


@router.post("/orders/{oid}/refund")
async def orders_refund(request: Request, oid: int, q: str = Form(""), filter_status: str = Form(""), page: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    if not refund_order(oid):
        return _ord_back(q, filter_status, err="คืนเงินไม่ได้ อาจคืนไปแล้ว", page=page)
    update_order(oid, status="canceled")
    return _ord_back(q, filter_status, ok="คืนเงินและยกเลิกออเดอร์แล้ว", page=page)


@router.get("/clients", response_class=HTMLResponse)
async def clients(request: Request, q: str = ""):
    gate = require_admin(request)
    if gate:
        return gate
    items = rows("clients")
    if q:
        needle = q.lower()
        items = [r for r in items if needle in " ".join(str(v or "") for v in r.values()).lower()]
    return render(request, "admin/clients.html", {
        "page": "clients",
        "rows": items,
        "q": q,
    })


@router.get("/services", response_class=HTMLResponse)
async def services(request: Request, added: str = "", main: str = "", q: str = "", page: int = 1, ok: str = "", n: str = ""):
    gate = require_admin(request)
    if gate:
        return gate
    init_db()
    settings = get_settings()
    page = max(int(page or 1), 1)
    per_page = 80
    main = (main or "").strip()
    total = count_admin_services(q, main)
    pages = max((total + per_page - 1) // per_page, 1)
    if page > pages:
        page = pages
    rows_all = list_admin_services(q, main, per_page, (page - 1) * per_page)
    mains = list_shop_mains()
    return render(request, "admin/services.html", {
        "page": "services",
        "rows": rows_all,
        "providers": list_providers(),
        "usd_rate": settings.get("usd_rate") or "35",
        "added": added,
        "ok": ok,
        "priced_n": n,
        "main": main,
        "q": q,
        "page_no": page,
        "pages": pages,
        "total": total,
        "mains": mains,
        "subs": list_shop_subs(main) if main else [],
    })


def _pay_back(status: str = "", ok: str = ""):
    q = []
    if status in ("pending", "paid", "canceled"):
        q.append("status=" + status)
    if ok:
        q.append("ok=" + ok)
    return RedirectResponse("/admin/payments" + (("?" + "&".join(q)) if q else ""), status_code=303)


@router.get("/payments", response_class=HTMLResponse)
async def payments(request: Request, status: str = "", ok: str = "", err: str = ""):
    gate = require_admin(request)
    if gate:
        return gate
    con = connect()
    pending = [dict(x) for x in con.execute(
        "SELECT * FROM payments WHERE status='pending' ORDER BY id DESC"
    ).fetchall()]
    counts = {r["status"]: dict(r) for r in con.execute(
        "SELECT status, COUNT(*) n, COALESCE(SUM(amount),0) s FROM payments GROUP BY status"
    ).fetchall()}
    if status in ("pending", "paid", "canceled"):
        items = [dict(x) for x in con.execute(
            "SELECT * FROM payments WHERE status=? ORDER BY id DESC LIMIT 200", (status,)
        ).fetchall()]
    else:
        items = [dict(x) for x in con.execute(
            "SELECT * FROM payments ORDER BY id DESC LIMIT 200"
        ).fetchall()]
    con.close()
    pending_n = int((counts.get("pending") or {}).get("n") or 0)
    paid_n = int((counts.get("paid") or {}).get("n") or 0)
    canceled_n = int((counts.get("canceled") or {}).get("n") or 0)
    return render(request, "admin/payments.html", {
        "page": "payments",
        "title": "ประวัติเติมเงิน",
        "rows": items,
        "pending_rows": pending,
        "status": status,
        "ok": ok,
        "err": err,
        "pay_sum": {
            "pending_n": pending_n,
            "pending_s": float((counts.get("pending") or {}).get("s") or 0),
            "paid_n": paid_n,
            "paid_s": float((counts.get("paid") or {}).get("s") or 0),
            "canceled_n": canceled_n,
            "all_n": pending_n + paid_n + canceled_n,
        },
    })


@router.post("/payments/match")
async def payments_match(request: Request, amount: str = Form(""), qr: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    return _pay_back("pending")


@router.post("/payments/{pid}/approve")
async def payments_approve(request: Request, pid: int, next: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    approve_payment(pid)
    return _pay_back(next, "paid")


@router.post("/payments/{pid}/reject")
async def payments_reject(request: Request, pid: int, note: str = Form(""), next: str = Form("")):
    gate = require_admin(request)
    if gate:
        return gate
    reject_payment(pid, note)
    return _pay_back(next, "canceled")


@router.get("/tickets", response_class=HTMLResponse)
async def tickets(request: Request, status: str = ""):
    gate = require_admin(request)
    if gate:
        return gate
    from store import all_ticket_replies
    items = rows("tickets")
    if status:
        items = [r for r in items if (r.get("status") or "") == status]
    return render(request, "admin/tickets.html", {
        "page": "tickets",
        "rows": items,
        "status": status,
        "replies": all_ticket_replies(),
    })


@router.get("/logs", response_class=HTMLResponse)
async def logs(request: Request):
    gate = require_admin(request)
    if gate:
        return gate
    return render(request, "admin/simple.html", {
        "page": "settings",
        "tab": "logs",
        "tabs": SETTING_TABS_UI,
        "title": "บันทึกระบบ",
        "columns": ["id", "action", "ip", "created_at"],
        "labels": ["ID", "รายการ", "IP", "เวลา"],
        "rows": rows("logs"),
        "log_kind": "system",
    })


@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    gate = require_admin(request)
    if gate:
        return gate
    from store import report_data
    return render(request, "admin/reports.html", {
        "page": "reports",
        "stats": stats(),
        "report": report_data(),
        "orders": rows("orders", 20),
        "pending_pays": [p for p in rows("payments", 80) if p.get("status") == "pending"][:20],
        "paid_pays": [p for p in rows("payments", 80) if p.get("status") == "paid"][:20],
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    gate = require_admin(request)
    if gate:
        return gate
    return RedirectResponse("/admin/settings/general", status_code=303)


@router.post("/settings")
async def settings_post(
    request: Request,
    site_name: str = Form(""),
    currency: str = Form(""),
    support_email: str = Form(""),
    announcement: str = Form(""),
    affiliate_percent: str = Form("5"),
    child_panel_price: str = Form("500"),
    min_deposit: str = Form("20"),
    promptpay: str = Form(""),
    bank_name: str = Form(""),
    bank_account: str = Form(""),
    bank_holder: str = Form(""),
    maintenance: str = Form("0"),
):
    gate = require_admin(request)
    if gate:
        return gate
    save_settings({
        "site_name": site_name,
        "currency": currency,
        "support_email": support_email,
        "announcement": announcement,
        "affiliate_percent": affiliate_percent,
        "child_panel_price": child_panel_price,
        "min_deposit": min_deposit,
        "promptpay": promptpay,
        "bank_name": bank_name,
        "bank_account": bank_account,
        "bank_holder": bank_holder,
        "maintenance": maintenance,
    })
    add_log("บันทึกตั้งค่า", request.client.host if request.client else "-")
    return render(request, "admin/settings.html", {"page": "settings", "settings": get_settings(), "saved": True})


@router.get("/providers", response_class=HTMLResponse)
async def providers_page(request: Request, saved: str = "", imported: str = "", edit: str = ""):
    gate = require_admin(request)
    if gate:
        return gate
    editing = get_provider(int(edit)) if str(edit).isdigit() else None
    return render(request, "admin/providers.html", {
        "page": "providers",
        "providers": list_providers(),
        "saved": saved == "1",
        "imported": imported,
        "editing": editing,
    })


@router.post("/providers")
async def providers_save(
    request: Request,
    name: str = Form(""),
    api_url: str = Form(""),
    api_key: str = Form(""),
    pid: str = Form(""),
):
    gate = require_admin(request)
    if gate:
        return gate
    save_provider(pid or None, name, api_url, api_key)
    add_log("บันทึกผู้ให้บริการ", request.client.host if request.client else "-")
    return RedirectResponse("/admin/providers?saved=1", status_code=303)


@router.post("/providers/balance")
async def providers_balance(request: Request, pid: int = Form(...)):
    gate = require_admin(request)
    if gate:
        return gate
    p = get_provider(pid)
    if p:
        result = action(p["api_url"], {"key": p["api_key"], "action": "balance"})
        if isinstance(result, dict) and "balance" in result:
            save_provider_balance(pid, result.get("balance"), result.get("currency") or "")
    return RedirectResponse("/admin/providers?saved=1", status_code=303)


@router.post("/providers/import")
async def providers_import(request: Request, pid: int = Form(...)):
    gate = require_admin(request)
    if gate:
        return gate
    return RedirectResponse("/admin/services/import?pid=%s" % pid, status_code=303)


@router.post("/providers/delete")
async def providers_delete(request: Request, pid: int = Form(...)):
    gate = require_admin(request)
    if gate:
        return gate
    delete_provider(pid)
    return RedirectResponse("/admin/providers", status_code=303)


CRON_JOB_META = {
    "pull": {"label": "ดึงงานรอบหลัก", "tone": "pull", "icon": "ri-refresh-line", "hint": "ส่งออเดอร์ · เช็คสถานะ · ยอดเงิน · ซิงก์แคตตาล็อก"},
    "sync": {"label": "ซิงก์บริการ", "tone": "sync", "icon": "ri-store-2-line", "hint": "อัปเดตราคาและเปิด/ปิดตามต้นทาง"},
    "shop": {"label": "คัดร้าน", "tone": "shop", "icon": "ri-shopping-bag-3-line", "hint": "คัดบริการแนะนำเข้าหน้าร้าน"},
    "catalog": {"label": "แคตตาล็อก", "tone": "catalog", "icon": "ri-database-2-line", "hint": "ดึงรายการจาก API ผู้ให้บริการ"},
}

CRON_FIELD_LABELS = {
    "send": "ส่งออเดอร์",
    "err": "ส่งไม่สำเร็จ",
    "status": "อัปเดตสถานะ",
    "balance": "เช็คยอด API",
    "drip": "ดริปฟีด",
    "sub": "สมาชิกภาพ",
    "task": "งานคิว",
    "catalog": "รายการต้นทาง",
    "blog": "บทความ",
    "pid": "ผู้ให้บริการ #",
    "listed": "ในร้าน",
    "active": "เปิดขาย",
    "inactive": "ปิดแล้ว",
    "dead": "ปิด (ต้นทางเสีย)",
    "dead_marked": "ปิด (ต้นทางเสีย)",
    "removed": "ปิดเพราะไม่มีต้นทาง",
    "picked": "คัดแล้ว",
    "added": "เพิ่มใหม่",
    "updated": "อัปเดต",
    "cats": "หมวด",
    "sync_active": "ซิงก์เปิดขาย",
    "sync_inactive": "ซิงก์ปิดแล้ว",
}


def _parse_cron_kv(detail):
    out = []
    text = str(detail or "").strip()
    if not text:
        return out
    # key=value pairs
    if "=" in text and " " in text.replace("=", " "):
        for part in text.split():
            if "=" not in part:
                continue
            key, val = part.split("=", 1)
            key = key.strip().lower()
            val = val.strip()
            label = CRON_FIELD_LABELS.get(key, key)
            out.append({"key": key, "label": label, "value": val})
        if out:
            return out
    return [{"key": "msg", "label": "ข้อความ", "value": text}]


def format_cron_logs(rows):
    formatted = []
    for row in rows:
        job = str(row.get("job") or "").strip().lower() or "other"
        meta = CRON_JOB_META.get(job, {
            "label": job or "อื่นๆ",
            "tone": "other",
            "icon": "ri-file-list-line",
            "hint": "",
        })
        fields = _parse_cron_kv(row.get("detail"))
        summary = " · ".join("%s %s" % (f["label"], f["value"]) for f in fields[:6])
        is_error = job == "catalog" and "error" in str(row.get("detail") or "").lower()
        if not is_error:
            for f in fields:
                if f["key"] in ("err",) and str(f["value"]) not in ("0", "", "-"):
                    try:
                        if float(f["value"]) > 0:
                            is_error = True
                    except (TypeError, ValueError):
                        is_error = True
        formatted.append({
            **row,
            "job_key": job,
            "job_label": meta["label"],
            "job_tone": meta["tone"],
            "job_icon": meta["icon"],
            "job_hint": meta["hint"],
            "fields": fields,
            "summary": summary or str(row.get("detail") or "-"),
            "is_error": is_error,
            "raw": str(row.get("detail") or ""),
        })
    return formatted


@router.get("/crons", response_class=HTMLResponse)
async def crons_page(request: Request, ran: str = "", job: str = "all"):
    gate = require_admin(request)
    if gate:
        return gate
    init_db()
    job = (job or "all").strip().lower() or "all"
    raw_logs = list_cron_logs(80, job if job != "all" else "")
    logs = format_cron_logs(raw_logs)
    settings = get_settings()
    counts = cron_log_job_counts(300)
    latest = format_cron_logs(list_cron_logs(8))
    last_pull = next((x for x in latest if x["job_key"] == "pull"), None)
    last_sync = next((x for x in latest if x["job_key"] == "sync"), None)
    last_shop = next((x for x in latest if x["job_key"] == "shop"), None)
    ran_text = ""
    if ran:
        ran_text = str(ran).replace("_", " ")
    return render(request, "admin/crons.html", {
        "page": "crons",
        "logs": logs,
        "ran": ran_text,
        "job": job,
        "job_counts": counts,
        "job_meta": CRON_JOB_META,
        "last_pull": last_pull,
        "last_sync": last_sync,
        "last_shop": last_shop,
        "shop_synced_at": settings.get("shop_synced_at") or settings.get("catalog_synced_at") or "-",
        "catalog_synced_at": settings.get("catalog_synced_at") or "-",
        "shop_rebuild_at": settings.get("shop_rebuild_at") or "-",
    })


@router.post("/crons/run")
async def crons_run(request: Request):
    gate = require_admin(request)
    if gate:
        return gate
    detail = run_all()
    return RedirectResponse("/admin/crons?ran=" + detail.replace(" ", "_"), status_code=303)


@router.post("/crons/shop")
async def crons_shop(request: Request):
    gate = require_admin(request)
    if gate:
        return gate
    from cron_jobs import refresh_shop
    n = refresh_shop()
    return RedirectResponse("/admin/crons?ran=shop_" + str(n), status_code=303)