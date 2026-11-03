from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from admin import render, require_admin
from db import (
    add_log,
    bump_service_rates,
    apply_rates_from_cost,
    catalog_all_filtered,
    catalog_by_ids,
    catalog_categories,
    catalog_count,
    catalog_mains,
    catalog_types,
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
    norm_currency,
    is_thb_currency,
    move_shop_sort,
    rename_shop_main,
    rename_shop_sub,
    reorder_shop_sort,
    add_shop_main,
    add_shop_sub,
    delete_shop_main,
    delete_shop_sub,
    delete_all_shop_mains,
    delete_all_shop_subs,
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


def _services_back(main="", q="", ok="1"):
    from urllib.parse import urlencode
    params = {}
    if main:
        params["main"] = main
    if q:
        params["q"] = q
    if ok:
        params["ok"] = ok
    return RedirectResponse("/admin/services" + (("?" + urlencode(params)) if params else ""), status_code=303)


@router.post("/services/main/rename")
async def services_main_rename(
    request: Request,
    old_name: str = Form(...),
    new_name: str = Form(...),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    ok = rename_shop_main(old_name, new_name)
    target = (new_name or "").strip() if ok else (old_name or "").strip()
    add_log("เปลี่ยนชื่อหมวดหลัก: %s → %s" % (old_name, new_name), request.client.host if request.client else "-")
    return _services_back(target, q, "renamed" if ok else "1")


@router.post("/services/main/move")
async def services_main_move(
    request: Request,
    name: str = Form(...),
    direction: int = Form(0),
    main: str = Form(""),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    move_shop_sort("main", name, direction)
    return _services_back(main or "", q, "moved")


@router.post("/services/sub/rename")
async def services_sub_rename(
    request: Request,
    platform: str = Form(...),
    old_name: str = Form(...),
    new_name: str = Form(...),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    rename_shop_sub(platform, old_name, new_name)
    add_log(
        "เปลี่ยนชื่อหมวดย่อย (%s): %s → %s" % (platform, old_name, new_name),
        request.client.host if request.client else "-",
    )
    return _services_back(platform, q, "renamed")


@router.post("/services/sub/move")
async def services_sub_move(
    request: Request,
    platform: str = Form(...),
    name: str = Form(...),
    direction: int = Form(0),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    move_shop_sort("sub", name, direction, platform)
    return _services_back(platform, q, "moved")


@router.post("/services/sort")
async def services_sort(
    request: Request,
    kind: str = Form("main"),
    order: str = Form(""),
    platform: str = Form(""),
):
    from fastapi.responses import JSONResponse
    g = gate(request)
    if g:
        return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
    names = []
    raw = (order or "").strip()
    if raw.startswith("["):
        import json
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                names = [str(x) for x in parsed]
        except Exception:
            names = []
    if not names:
        names = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
    ok = reorder_shop_sort(kind, names, platform)
    return JSONResponse({"ok": bool(ok)})


@router.post("/services/main/add")
async def services_main_add(request: Request, name: str = Form(...), q: str = Form("")):
    g = gate(request)
    if g:
        return g
    ok = add_shop_main(name)
    if ok:
        add_log("เพิ่มหมวดหลัก: %s" % name, request.client.host if request.client else "-")
    return _services_back((name or "").strip(), q, "added" if ok else "1")


@router.post("/services/main/delete")
async def services_main_delete(request: Request, name: str = Form(...), q: str = Form("")):
    g = gate(request)
    if g:
        return g
    n = delete_shop_main(name)
    add_log("ลบหมวดหลัก %s (%s บริการ)" % (name, n), request.client.host if request.client else "-")
    return _services_back("", q, "deleted")


@router.post("/services/main/delete-all")
async def services_main_delete_all(request: Request, q: str = Form("")):
    g = gate(request)
    if g:
        return g
    n = delete_all_shop_mains()
    add_log("ลบหมวดหลักทั้งหมด (%s บริการ)" % n, request.client.host if request.client else "-")
    return _services_back("", q, "deleted")


@router.post("/services/sub/add")
async def services_sub_add(
    request: Request,
    platform: str = Form(...),
    name: str = Form(...),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    ok = add_shop_sub(platform, name)
    if ok:
        add_log("เพิ่มหมวดย่อย (%s): %s" % (platform, name), request.client.host if request.client else "-")
    return _services_back(platform, q, "added" if ok else "1")


@router.post("/services/sub/delete")
async def services_sub_delete(
    request: Request,
    platform: str = Form(...),
    name: str = Form(...),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    n = delete_shop_sub(platform, name)
    add_log("ลบหมวดย่อย (%s/%s) %s บริการ" % (platform, name, n), request.client.host if request.client else "-")
    return _services_back(platform, q, "deleted")


@router.post("/services/sub/delete-all")
async def services_sub_delete_all(
    request: Request,
    platform: str = Form(...),
    q: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    n = delete_all_shop_subs(platform)
    add_log("ลบหมวดย่อยทั้งหมดใน %s (%s บริการ)" % (platform, n), request.client.host if request.client else "-")
    return _services_back(platform, q, "deleted")


def _import_rows(provider_id, items, usd_rate, percent, fixed, picks=None, main="", cat="", skip_existing=False, default_currency="USD"):
    have = imported_api_ids(provider_id) if skip_existing else set()
    fallback = norm_currency(default_currency, "USD")
    rows = []
    for item in items:
        api_sid = str(item.get("api_service") or "")
        if not api_sid:
            continue
        if skip_existing and api_sid in have:
            continue
        currency = norm_currency(item.get("currency") or fallback, fallback)
        cost = item.get("rate") or 0
        if picks and api_sid in picks:
            try:
                rate = float(picks[api_sid])
            except (TypeError, ValueError):
                rate = sell_thb(item.get("rate") or 0, currency, usd_rate, percent, fixed)
        else:
            rate = sell_thb(item.get("rate") or 0, currency, usd_rate, percent, fixed)
        raw_cat = str(item.get("category") or item.get("main_cat") or "").strip()
        plat_guess, sub_guess = split_category(raw_cat or "อื่น ๆ")
        plat = (main or item.get("main_cat") or plat_guess or "อื่น ๆ").strip() or "อื่น ๆ"
        shop_sub = (cat or sub_guess or "").strip()
        rows.append({
            "platform": plat,
            "name": item.get("name") or ("Service %s" % api_sid),
            "rate": rate,
            "min_qty": item.get("min_qty") or 1,
            "max_qty": item.get("max_qty") or 100000,
            "api_service": api_sid,
            "cost_rate": cost,
            "category": shop_sub,
            "currency": currency,
        })
        if skip_existing:
            have.add(api_sid)
    from db import import_shop_rows
    return import_shop_rows(provider_id, rows)


def _import_scope_query(scope, q, cat, main, stype):
    scope = (scope or "filtered").strip().lower()
    skip_existing = scope in {"new", "all_new", "main_new", "filtered_new"}
    if scope in {"all", "all_new"}:
        return "", "", "", "", skip_existing
    if scope in {"main", "main_new"}:
        return "", "", main, "", skip_existing
    return q, cat, main, stype, skip_existing


@router.get("/services/import", response_class=HTMLResponse)
async def services_import(
    request: Request,
    pid: int = 0,
    q: str = "",
    cat: str = "",
    main: str = "",
    stype: str = "",
    view: str = "",
    per: int = 80,
    page: int = 1,
    loaded: str = "",
    added: str = "",
    error: str = "",
    synced: str = "",
    inactive: str = "",
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
    try:
        per_page = int(per or 80)
    except (TypeError, ValueError):
        per_page = 80
    if per_page not in (50, 80, 150, 300):
        per_page = 80
    page = max(int(page or 1), 1)
    q = (q or "").strip()
    cat = (cat or "").strip()
    main = (main or "").strip()
    stype = (stype or "").strip()
    show_all = str(view or "").strip().lower() in {"1", "true", "yes", "all"}
    mains = catalog_mains(pid) if pid else []
    cats = catalog_categories(pid, main) if pid else []
    catalog_total = catalog_count(pid) if pid else 0
    browse = bool(pid and (cat or (main and show_all) or q))
    total = catalog_count(pid, q, cat, main, stype) if browse else 0
    pages = max((total + per_page - 1) // per_page, 1) if browse else 1
    if page > pages:
        page = pages
    catalog = (
        list_provider_catalog(pid, q, cat, per_page, (page - 1) * per_page, main, stype)
        if browse
        else []
    )
    types = catalog_types(pid, cat, main) if pid and (cat or main or q) else []
    currency = norm_currency((provider or {}).get("currency") or "", "")
    if pid and not currency:
        sample = list_provider_catalog(pid, limit=1)
        if sample:
            currency = norm_currency(sample[0].get("currency") or "", "USD")
    if catalog:
        currency = norm_currency(catalog[0].get("currency") or currency, currency or "USD")
    currency = currency or "USD"
    priced = []
    for item in catalog:
        row = dict(item)
        row_cur = norm_currency(row.get("currency") or currency, currency)
        row["currency"] = row_cur
        row["cost_thb"] = to_thb(row.get("rate") or 0, row_cur, usd_rate)
        row["sell_thb"] = sell_thb(row.get("rate") or 0, row_cur, usd_rate, 100, 0)
        priced.append(row)
    return render(request, "admin/service_import.html", {
        "page": "services",
        "providers": providers,
        "provider": provider,
        "pid": pid,
        "q": q,
        "cat": cat,
        "main": main,
        "stype": stype,
        "show_all": show_all,
        "browse": browse,
        "mains": mains,
        "catalog": priced,
        "categories": cats,
        "types": types,
        "catalog_total": catalog_total,
        "total": total,
        "page_no": page,
        "pages": pages,
        "per_page": per_page,
        "usd_rate": usd_rate,
        "currency": currency,
        "is_thb": is_thb_currency(currency),
        "imported": imported_api_ids(pid) if pid else set(),
        "loaded": loaded,
        "added": added,
        "error": error,
        "synced": synced,
        "inactive_n": inactive,
        "shop_synced_at": settings.get("shop_synced_at") or settings.get("catalog_synced_at") or "",
        "catalog_synced_at": settings.get("catalog_synced_at") or "",
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
    currency = norm_currency(p.get("currency") or "", "")
    bal = action(p["api_url"], {"key": p["api_key"], "action": "balance"}, timeout=20)
    bal_amt = p.get("balance")
    if isinstance(bal, dict):
        if bal.get("currency"):
            currency = norm_currency(bal.get("currency"), currency or "USD")
        if bal.get("balance") is not None:
            bal_amt = bal.get("balance")
    if err:
        add_log("ดึงบริการไม่สำเร็จ: %s" % err, request.client.host if request.client else "-")
        return RedirectResponse("/admin/services/import?pid=%s&error=1" % pid, status_code=303)
    # If API items carry currency, prefer first non-empty; else balance / provider
    for it in items:
        if isinstance(it, dict) and (it.get("currency") or it.get("Currency")):
            currency = norm_currency(it.get("currency") or it.get("Currency"), currency or "USD")
            break
    currency = currency or "USD"
    count = replace_provider_catalog(pid, items, currency)
    save_provider_balance(pid, bal_amt, currency)
    from db import sync_listed_from_catalog, set_shop_manual_lock, now as db_now
    sync_stats = sync_listed_from_catalog(pid) or {}
    # Keep curated/imported shop — only price+status sync on cron
    set_shop_manual_lock(True)
    save_settings({
        "catalog_synced_at": db_now(),
        "shop_synced_at": db_now(),
    })
    add_log(
        "โหลดรายการบริการจาก API %s รายการ · ซิงก์ร้าน active=%s inactive=%s removed=%s"
        % (count, sync_stats.get("active") or 0, sync_stats.get("inactive") or 0, sync_stats.get("removed") or 0),
        request.client.host if request.client else "-",
    )
    return RedirectResponse(
        "/admin/services/import?pid=%s&loaded=%s&synced=%s&inactive=%s"
        % (pid, count, sync_stats.get("active") or 0, sync_stats.get("inactive") or 0),
        status_code=303,
    )


@router.post("/services/import/sync")
async def services_import_sync(request: Request, pid: int = Form(...)):
    g = gate(request)
    if g:
        return g
    init_db()
    from smm_api import action, normalize_services
    from db import sync_listed_from_catalog, set_shop_manual_lock, now as db_now
    p = get_provider(pid)
    if not p:
        return RedirectResponse("/admin/services/import?error=1", status_code=303)
    result = action(p["api_url"], {"key": p["api_key"], "action": "services"}, timeout=90)
    items, err = normalize_services(result)
    if err or not items:
        add_log("ซิงก์บริการไม่สำเร็จ: %s" % (err or "empty"), request.client.host if request.client else "-")
        return RedirectResponse("/admin/services/import?pid=%s&error=1" % pid, status_code=303)
    currency = norm_currency(p.get("currency") or "", "USD")
    for it in items:
        if isinstance(it, dict) and (it.get("currency") or it.get("Currency")):
            currency = norm_currency(it.get("currency") or it.get("Currency"), currency)
            break
    count = replace_provider_catalog(pid, items, currency)
    sync_stats = sync_listed_from_catalog(pid) or {}
    set_shop_manual_lock(True)
    save_settings({"catalog_synced_at": db_now(), "shop_synced_at": db_now()})
    add_log(
        "ซิงก์ตามต้นทาง catalog=%s active=%s inactive=%s dead=%s removed=%s"
        % (
            count,
            sync_stats.get("active") or 0,
            sync_stats.get("inactive") or 0,
            sync_stats.get("dead_marked") or 0,
            sync_stats.get("removed") or 0,
        ),
        request.client.host if request.client else "-",
    )
    return RedirectResponse(
        "/admin/services/import?pid=%s&loaded=%s&synced=%s&inactive=%s"
        % (pid, count, sync_stats.get("active") or 0, sync_stats.get("inactive") or 0),
        status_code=303,
    )


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
    stype: str = Form(""),
):
    g = gate(request)
    if g:
        return g
    import json
    provider = get_provider(pid)
    if not provider:
        return RedirectResponse("/admin/services/import?error=1", status_code=303)
    try:
        usd = float(usd_rate or 35)
        pct = float(percent or 0)
        extra = float(fixed or 0)
    except (TypeError, ValueError):
        usd, pct, extra = 35.0, 20.0, 0.0
    save_settings({"usd_rate": str(usd)})
    scope = (scope or "selected").strip().lower()
    max_n = 20000
    skip_existing = scope in {"new", "all_new", "main_new", "filtered_new"}
    data = {}
    if scope in {"all", "all_new"}:
        items = catalog_all_filtered(pid, "", "", "", "")[:max_n]
    elif scope in {"main", "main_new"}:
        items = catalog_all_filtered(pid, "", "", main, "")[:max_n]
    elif scope in {"filtered", "filtered_new"}:
        items = catalog_all_filtered(pid, q, cat, main, stype)[:max_n]
    else:
        try:
            data = json.loads(picks or "{}")
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        items = catalog_by_ids(pid, list(data.keys()))
        skip_existing = False
    default_cur = norm_currency(provider.get("currency") or "", "USD")
    count = _import_rows(
        pid,
        items,
        usd,
        pct,
        extra,
        {str(k): v for k, v in data.items()},
        main,
        cat,
        skip_existing=skip_existing,
        default_currency=default_cur,
    )
    from db import clear_shop_blocks, unblock_shop_main, set_shop_manual_lock
    if scope in {"all", "all_new"}:
        clear_shop_blocks()
    elif main:
        unblock_shop_main(main)
    # Imported/curated list — keep syncing prices/status, do not auto-rebuild cull
    set_shop_manual_lock(True)
    add_log("เพิ่มบริการจาก API %s รายการ (scope=%s)" % (count, scope), request.client.host if request.client else "-")
    return RedirectResponse("/admin/services?added=%s" % count, status_code=303)


@router.post("/services/import/batch")
async def services_import_batch(
    request: Request,
    pid: int = Form(...),
    scope: str = Form("all_new"),
    usd_rate: str = Form("35"),
    percent: str = Form("100"),
    fixed: str = Form("0"),
    q: str = Form(""),
    cat: str = Form(""),
    main: str = Form(""),
    stype: str = Form(""),
    offset: int = Form(0),
    batch: int = Form(120),
):
    from fastapi.responses import JSONResponse
    g = gate(request)
    if g:
        return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
    if not get_provider(pid):
        return JSONResponse({"ok": False, "error": "provider"}, status_code=400)
    provider = get_provider(pid)
    try:
        usd = float(usd_rate or 35)
        pct = float(percent or 0)
        extra = float(fixed or 0)
    except (TypeError, ValueError):
        usd, pct, extra = 35.0, 20.0, 0.0
    try:
        offset = max(int(offset or 0), 0)
    except (TypeError, ValueError):
        offset = 0
    try:
        batch = int(batch or 120)
    except (TypeError, ValueError):
        batch = 120
    batch = max(40, min(batch, 200))
    save_settings({"usd_rate": str(usd)})
    q2, cat2, main2, stype2, skip_existing = _import_scope_query(scope, q, cat, main, stype)
    total = catalog_count(pid, q2, cat2, main2, stype2)
    items = list_provider_catalog(pid, q2, cat2, batch, offset, main2, stype2) if total else []
    default_cur = norm_currency((provider or {}).get("currency") or "", "USD")
    added = _import_rows(
        pid, items, usd, pct, extra, None, main2, cat2,
        skip_existing=skip_existing, default_currency=default_cur,
    )
    processed = min(offset + batch, total)
    done = processed >= total or total == 0
    from db import clear_shop_blocks, unblock_shop_main, set_shop_manual_lock
    if done:
        if (scope or "").strip().lower() in {"all", "all_new"}:
            clear_shop_blocks()
        elif main2:
            unblock_shop_main(main2)
        set_shop_manual_lock(True)
        add_log(
            "นำเข้าแบบชุดเสร็จ %s/%s (เพิ่มจริงในรอบท้าย +%s, scope=%s)" % (processed, total, added, scope),
            request.client.host if request.client else "-",
        )
    percent_done = int(round((processed * 100.0 / total), 0)) if total else 100
    return JSONResponse({
        "ok": True,
        "added": int(added),
        "offset": offset,
        "next_offset": offset + batch,
        "batch": batch,
        "total": int(total),
        "processed": int(processed),
        "done": bool(done),
        "percent": percent_done,
    })


@router.post("/services/bulk-rate")
async def service_bulk_rate(request: Request, ids: str = Form(""), percent: float = Form(0), fixed: float = Form(0)):
    g = gate(request)
    if g:
        return g
    sid_list = []
    for part in (ids or "").split(","):
        part = part.strip()
        if part.isdigit():
            sid_list.append(int(part))
    if sid_list:
        apply_rates_from_cost(percent, fixed, sid_list)
        save_settings({"profit_percent": str(percent)})
    return RedirectResponse("/admin/services", status_code=303)


@router.post("/services/bulk-rate-all")
async def service_bulk_rate_all(request: Request, percent: float = Form(0), fixed: float = Form(0)):
    g = gate(request)
    if g:
        return g
    count = apply_rates_from_cost(percent, fixed, None)
    save_settings({"profit_percent": str(percent)})
    add_log("ปรับราคาจากต้นทุน %s%% ทั้งร้าน %s รายการ" % (percent, count), request.client.host if request.client else "-")
    return RedirectResponse("/admin/services?ok=priced&n=%s" % count, status_code=303)


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
