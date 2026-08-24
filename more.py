from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from admin import render, require_admin
from db import (
    add_log,
    bump_service_rates,
    catalog_all_filtered,
    catalog_by_ids,
    catalog_categories,
    catalog_count,
    catalog_mains,
    get_provider,
    get_settings,
    import_provider_service,
    imported_api_ids,
    init_db,
    list_provider_catalog,
    list_providers,
    replace_provider_catalog,
    rows,
    save_provider_balance,
    save_settings,
    sell_thb,
    set_service_status,
    set_service_subcategory,
    split_category,
    stats,
    to_thb,
    update_service_rate,
)
from store import (
    add_news,
    adjust_balance,
    all_ticket_replies,
    close_ticket,
    delete_news,
    delete_service,
    fetch_all,
    fetch_one,
    list_news,
    process_one_task,
    regenerate_api_key,
    reply_ticket,
    report_data,
    save_service,
    set_admin_password,
    set_child_status,
    set_client_password,
    set_client_status,
    set_task_status,
)

router = APIRouter(prefix="/admin")


def gate(request):
    return require_admin(request)


@router.get("/dripfeeds", response_class=HTMLResponse)
async def dripfeeds(request: Request):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/simple.html", {
        "page": "dripfeeds",
        "title": "ส่งทีละรอบ",
        "columns": ["id", "client", "service", "quantity", "runs", "delivered", "interval_min", "charge", "status", "created_at"],
        "labels": ["ID", "ลูกค้า", "บริการ", "จำนวน/รอบ", "รอบ", "ส่งแล้ว", "นาที", "ยอด", "สถานะ", "เวลา"],
        "rows": fetch_all("SELECT * FROM dripfeeds ORDER BY id DESC LIMIT 200"),
    })


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions(request: Request):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/simple.html", {
        "page": "subscriptions",
        "title": "เติมอัตโนมัติ",
        "columns": ["id", "client", "service", "username", "min_qty", "max_qty", "posts", "delivered", "status", "created_at"],
        "labels": ["ID", "ลูกค้า", "บริการ", "ยูส", "ต่ำสุด", "สูงสุด", "โพสต์", "ส่งแล้ว", "สถานะ", "เวลา"],
        "rows": fetch_all("SELECT * FROM subscriptions ORDER BY id DESC LIMIT 200"),
    })


@router.post("/subscriptions/{sid}/status")
async def sub_status(request: Request, sid: int, status: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if status in {"active", "paused", "canceled", "completed"}:
        from store import execute
        execute("UPDATE subscriptions SET status=? WHERE id=?", (status, sid))
    return RedirectResponse("/admin/subscriptions", status_code=303)


@router.post("/dripfeeds/{did}/status")
async def drip_status(request: Request, did: int, status: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if status in {"active", "paused", "canceled", "completed"}:
        from store import execute
        execute("UPDATE dripfeeds SET status=? WHERE id=?", (status, did))
    return RedirectResponse("/admin/dripfeeds", status_code=303)


@router.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/simple.html", {
        "page": "tasks",
        "title": "ขอเติม",
        "columns": ["id", "order_id", "client", "kind", "status", "detail", "created_at"],
        "labels": ["ID", "ออเดอร์", "ลูกค้า", "ประเภท", "สถานะ", "รายละเอียด", "เวลา"],
        "rows": fetch_all("SELECT * FROM tasks ORDER BY id DESC LIMIT 200"),
    })


@router.post("/tasks/{tid}/status")
async def task_status(request: Request, tid: int, status: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if status == "run":
        process_one_task(tid)
    elif status == "retry":
        set_task_status(tid, "pending")
        process_one_task(tid)
    elif status == "canceled":
        set_task_status(tid, "canceled")
    return RedirectResponse("/admin/tasks", status_code=303)


@router.get("/panels", response_class=HTMLResponse)
async def panels(request: Request):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/panels.html", {
        "page": "panels",
        "rows": fetch_all("SELECT * FROM child_panels ORDER BY id DESC LIMIT 200"),
    })


@router.post("/panels/{pid}/status")
async def panels_status(request: Request, pid: int, status: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if status in {"pending", "active", "canceled"}:
        set_child_status(pid, status)
        add_log("แผงลูก #%s เป็น %s" % (pid, status), request.client.host if request.client else "-")
    return RedirectResponse("/admin/panels", status_code=303)


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/news.html", {"page": "news", "tab": "news", "rows": list_news(50)})


@router.post("/news")
async def news_add(request: Request, title: str = Form(...), body: str = Form(...)):
    g = gate(request)
    if g:
        return g
    add_news(title.strip(), body.strip())
    return RedirectResponse("/admin/news", status_code=303)


@router.post("/news/{nid}/delete")
async def news_del(request: Request, nid: int):
    g = gate(request)
    if g:
        return g
    delete_news(nid)
    return RedirectResponse("/admin/news", status_code=303)


@router.get("/affiliates", response_class=HTMLResponse)
async def affiliates(request: Request, saved: str = "", error: str = ""):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/affiliates.html", {
        "page": "affiliates",
        "saved": saved == "1",
        "error": error,
        "rows": fetch_all("SELECT id, username, ref_code, referred_by, IFNULL(ref_earn,0) ref_earn, balance FROM clients ORDER BY IFNULL(ref_earn,0) DESC LIMIT 200"),
    })


@router.post("/affiliates/{cid}/payout")
async def affiliate_payout(request: Request, cid: int, amount: float = Form(0)):
    g = gate(request)
    if g:
        return g
    row = fetch_one("SELECT username, IFNULL(ref_earn,0) ref_earn FROM clients WHERE id=?", (cid,))
    if not row:
        return RedirectResponse("/admin/affiliates?error=1", status_code=303)
    earn = float(row["ref_earn"] or 0)
    amt = float(amount or earn)
    if amt <= 0 or amt > earn + 0.0001:
        return RedirectResponse("/admin/affiliates?error=1", status_code=303)
    from store import execute
    execute("UPDATE clients SET balance = balance + ?, ref_earn = IFNULL(ref_earn,0) - ? WHERE id=?", (amt, amt, cid))
    add_log("โอนรายได้แนะนำ %s ให้ %s" % (amt, row["username"]), request.client.host if request.client else "-")
    return RedirectResponse("/admin/affiliates?saved=1", status_code=303)


@router.post("/affiliates/{cid}/adjust")
async def affiliate_adjust(request: Request, cid: int, amount: float = Form(...)):
    g = gate(request)
    if g:
        return g
    row = fetch_one("SELECT username FROM clients WHERE id=?", (cid,))
    if not row:
        return RedirectResponse("/admin/affiliates?error=1", status_code=303)
    from store import execute
    execute("UPDATE clients SET ref_earn = IFNULL(ref_earn,0) + ? WHERE id=?", (amount, cid))
    add_log("ปรับรายได้แนะนำ %s ของ %s" % (amount, row["username"]), request.client.host if request.client else "-")
    return RedirectResponse("/admin/affiliates?saved=1", status_code=303)


@router.get("/account", response_class=HTMLResponse)
async def account_get(request: Request, saved: str = "", error: str = ""):
    g = gate(request)
    if g:
        return g
    return render(request, "admin/account.html", {
        "page": "settings",
        "tab": "account",
        "saved": saved == "1",
        "error": error,
    })


@router.post("/account")
async def account_post(request: Request, password: str = Form(...), confirm: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if password != confirm or len(password) < 8:
        return RedirectResponse("/admin/account?error=1", status_code=303)
    set_admin_password(request.session.get("admin"), password)
    add_log("เปลี่ยนรหัสแอดมิน", request.client.host if request.client else "-")
    return RedirectResponse("/admin/account?saved=1", status_code=303)


@router.post("/clients/{cid}/balance")
async def client_balance(request: Request, cid: int, amount: float = Form(...), note: str = Form("")):
    g = gate(request)
    if g:
        return g
    row = fetch_one("SELECT username FROM clients WHERE id=?", (cid,))
    if row:
        adjust_balance(row["username"], amount, note or "แอดมิน")
    return RedirectResponse("/admin/clients", status_code=303)


@router.post("/clients/{cid}/status")
async def client_status(request: Request, cid: int, status: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if status in {"active", "paused"}:
        set_client_status(cid, status)
    return RedirectResponse("/admin/clients", status_code=303)


@router.post("/clients/{cid}/password")
async def client_password(request: Request, cid: int, password: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if len(password) >= 6:
        set_client_password(cid, password)
    return RedirectResponse("/admin/clients", status_code=303)


@router.post("/clients/{cid}/apikey")
async def client_apikey(request: Request, cid: int):
    g = gate(request)
    if g:
        return g
    regenerate_api_key(cid)
    return RedirectResponse("/admin/clients", status_code=303)


@router.post("/services/save")
async def service_save(
    request: Request,
    sid: str = Form(""),
    platform: str = Form(...),
    name: str = Form(...),
    rate: float = Form(0),
    min_qty: int = Form(10),
    max_qty: int = Form(10000),
    status: str = Form("active"),
    provider_id: str = Form(""),
    api_service: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    save_service(sid or None, platform, name, rate, min_qty, max_qty, status, provider_id or None, api_service)
    return RedirectResponse("/admin/services", status_code=303)


def _import_rows(provider_id, items, usd_rate, percent, fixed, picks=None, main="", cat=""):
    count = 0
    shop_cat = (cat or main or "").strip()
    for item in items:
        api_sid = str(item.get("api_service") or "")
        if not api_sid:
            continue
        currency = item.get("currency") or "USD"
        cost = item.get("rate") or 0
        if picks and api_sid in picks:
            try:
                rate = float(picks[api_sid])
            except (TypeError, ValueError):
                rate = sell_thb(item.get("rate") or 0, currency, usd_rate, percent, fixed)
        else:
            rate = sell_thb(item.get("rate") or 0, currency, usd_rate, percent, fixed)
        plat = shop_cat or str(item.get("category") or "อื่น ๆ")
        import_provider_service(
            provider_id,
            plat,
            item.get("name") or ("Service %s" % api_sid),
            rate,
            item.get("min_qty") or 1,
            item.get("max_qty") or 100000,
            api_sid,
            cost,
            "",
            currency,
        )
        count += 1
    return count


@router.get("/services/import", response_class=HTMLResponse)
async def services_import(
    request: Request,
    pid: int = 0,
    q: str = "",
    cat: str = "",
    main: str = "",
    page: int = 1,
    loaded: str = "",
    added: str = "",
    error: str = "",
):
    g = gate(request)
    if g:
        return g
    init_db()
    providers = list_providers()
    provider = get_provider(pid) if pid else (providers[0] if providers else None)
    pid = int(provider["id"]) if provider else 0
    settings = get_settings()
    usd_rate = settings.get("usd_rate") or "35"
    per_page = 80
    page = max(int(page or 1), 1)
    cats = catalog_categories(pid) if pid else []
    total = catalog_count(pid, q, cat) if pid and cat else 0
    pages = max((total + per_page - 1) // per_page, 1)
    if page > pages:
        page = pages
    catalog = list_provider_catalog(pid, q, cat, per_page, (page - 1) * per_page) if pid and cat else []
    currency = (provider or {}).get("currency") or ""
    if pid and not currency:
        sample = list_provider_catalog(pid, limit=1)
        if sample:
            currency = sample[0].get("currency") or ""
    if catalog:
        currency = catalog[0].get("currency") or currency
    priced = []
    for item in catalog:
        row = dict(item)
        row["cost_thb"] = to_thb(row.get("rate") or 0, row.get("currency") or currency or "USD", usd_rate)
        row["sell_thb"] = sell_thb(row.get("rate") or 0, row.get("currency") or currency or "USD", usd_rate, 100, 0)
        priced.append(row)
    return render(request, "admin/service_import.html", {
        "page": "services",
        "providers": providers,
        "provider": provider,
        "pid": pid,
        "q": q,
        "cat": cat,
        "main": main,
        "mains": catalog_mains(pid) if pid else [],
        "catalog": priced,
        "categories": cats,
        "total": total,
        "page_no": page,
        "pages": pages,
        "usd_rate": usd_rate,
        "currency": currency or "USD",
        "imported": imported_api_ids(pid) if pid else set(),
        "loaded": loaded,
        "added": added,
        "error": error,
    })


@router.post("/services/import/fetch")
async def services_import_fetch(request: Request, pid: int = Form(...)):
    g = gate(request)
    if g:
        return g
    init_db()
    from smm_api import action, normalize_services
    p = get_provider(pid)
    if not p:
        return RedirectResponse("/admin/services/import?error=1", status_code=303)
    result = action(p["api_url"], {"key": p["api_key"], "action": "services"}, timeout=70)
    items, err = normalize_services(result)
    currency = (p.get("currency") or "").strip()
    bal = action(p["api_url"], {"key": p["api_key"], "action": "balance"}, timeout=20)
    if isinstance(bal, dict) and bal.get("currency"):
        currency = str(bal.get("currency"))
        save_provider_balance(pid, bal.get("balance"), currency)
    if err:
        add_log("ดึงบริการไม่สำเร็จ: %s" % err, request.client.host if request.client else "-")
        return RedirectResponse("/admin/services/import?pid=%s&error=1" % pid, status_code=303)
    count = replace_provider_catalog(pid, items, currency or "USD")
    add_log("โหลดรายการบริการจาก API %s รายการ" % count, request.client.host if request.client else "-")
    return RedirectResponse("/admin/services/import?pid=%s&loaded=%s" % (pid, count), status_code=303)


@router.post("/services/import/add")
async def services_import_add(
    request: Request,
    pid: int = Form(...),
    picks: str = Form("{}"),
    usd_rate: str = Form("35"),
    percent: str = Form("100"),
    fixed: str = Form("0"),
    scope: str = Form("selected"),
    q: str = Form(""),
    cat: str = Form(""),
    main: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    import json
    if not get_provider(pid):
        return RedirectResponse("/admin/services/import?error=1", status_code=303)
    try:
        usd = float(usd_rate or 35)
        pct = float(percent or 0)
        extra = float(fixed or 0)
    except (TypeError, ValueError):
        usd, pct, extra = 35.0, 20.0, 0.0
    save_settings({"usd_rate": str(usd)})
    if scope == "filtered":
        items = catalog_all_filtered(pid, q, cat)[:1000]
        data = {}
    else:
        try:
            data = json.loads(picks or "{}")
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        items = catalog_by_ids(pid, list(data.keys()))
    count = _import_rows(pid, items, usd, pct, extra, {str(k): v for k, v in data.items()}, main, cat)
    add_log("เพิ่มบริการจาก API %s รายการ" % count, request.client.host if request.client else "-")
    return RedirectResponse("/admin/services?added=%s" % count, status_code=303)


@router.post("/services/bulk-rate")
async def service_bulk_rate(request: Request, ids: str = Form(""), percent: float = Form(0)):
    g = gate(request)
    if g:
        return g
    sid_list = []
    for part in (ids or "").split(","):
        part = part.strip()
        if part.isdigit():
            sid_list.append(int(part))
    if sid_list:
        bump_service_rates(sid_list, percent)
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/services/bulk-category")
async def service_bulk_category(request: Request, ids: str = Form(""), category: str = Form("")):
    g = gate(request)
    if g:
        return g
    sid_list = []
    for part in (ids or "").split(","):
        part = part.strip()
        if part.isdigit():
            sid_list.append(int(part))
    if sid_list:
        set_service_subcategory(sid_list, category)
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/services/bulk-status")
async def service_bulk_status(request: Request, ids: str = Form(""), status: str = Form("paused")):
    g = gate(request)
    if g:
        return g
    if status not in {"active", "paused"}:
        status = "paused"
    for part in (ids or "").split(","):
        part = part.strip()
        if part.isdigit():
            set_service_status(int(part), status)
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/services/{sid}/rate")
async def service_rate(request: Request, sid: int, rate: float = Form(...)):
    g = gate(request)
    if g:
        return g
    update_service_rate(sid, rate)
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/services/{sid}/status")
async def service_status(request: Request, sid: int, status: str = Form(...)):
    g = gate(request)
    if g:
        return g
    if status in {"active", "paused"}:
        set_service_status(sid, status)
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/services/{sid}/delete")
async def service_delete(request: Request, sid: int):
    g = gate(request)
    if g:
        return g
    delete_service(sid)
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/tickets/{tid}/reply")
async def ticket_reply(request: Request, tid: int, message: str = Form(...)):
    g = gate(request)
    if g:
        return g
    reply_ticket(tid, request.session.get("admin") or "admin", message.strip())
    return RedirectResponse("/admin/tickets", status_code=303)


@router.post("/tickets/{tid}/close")
async def ticket_close(request: Request, tid: int):
    g = gate(request)
    if g:
        return g
    close_ticket(tid)
    return RedirectResponse("/admin/tickets", status_code=303)
