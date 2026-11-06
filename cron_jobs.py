from datetime import datetime

from db import (
    add_cron_log,
    add_log,
    get_order,
    get_provider,
    get_service,
    init_db,
    pending_send_orders,
    active_status_orders,
    refund_order,
    save_provider_balance,
    update_order,
    update_service_api,
)
from smm_api import action

SHOP_REBUILD_HOURS = 24


def resolve_fallback_service(order, original_svc, provider):
    """
    Finds and dispatches to the closest available service on the provider with a similar price rate
    when the mapped service ID is invalid or rejected ('Incorrect service ID').
    """
    try:
        from db import connect
        con = connect()
        target_rate = float(original_svc.get("rate") or 0)
        target_platform = (original_svc.get("platform") or "").strip().lower()
        target_name = (original_svc.get("name") or "").strip().lower()
        qty = int(order.get("quantity") or 0)
        
        keywords = []
        for kw in ["likes", "views", "followers", "subscribers", "comments", "shares", "reposts", "members", "hours"]:
            if kw in target_name:
                keywords.append(kw)
        
        candidates = con.execute("""
            SELECT id, name, platform, rate, cost_rate, api_service, min_qty, max_qty
            FROM services
            WHERE provider_id = ? 
              AND LOWER(platform) = ?
              AND api_service IS NOT NULL 
              AND api_service != ''
              AND api_service != ?
              AND status = 'active'
        """, (provider["id"], target_platform, str(original_svc.get("api_service") or ""))).fetchall()
        con.close()
        
        matched = []
        for c in candidates:
            c_dict = dict(c)
            c_name = c_dict["name"].lower()
            if keywords and not any(kw in c_name for kw in keywords):
                continue
            if ("brazil" in c_name or "russia" in c_name or "ukraine" in c_name or "turkey" in c_name or "indonesia" in c_name or "india" in c_name) and not any(country in target_name for country in ["brazil", "russia", "ukraine", "turkey", "indonesia", "india"]):
                continue
            if c_dict.get("min_qty") and qty < int(c_dict["min_qty"]):
                continue
            if c_dict.get("max_qty") and qty > int(c_dict["max_qty"]):
                continue
                
            diff = abs(float(c_dict["rate"] or 0) - target_rate)
            matched.append((diff, c_dict))
            
        matched.sort(key=lambda x: x[0])
        
        for _, candidate in matched[:6]:
            cand_api_id = str(candidate["api_service"])
            test_payload = {
                "key": provider["api_key"],
                "action": "add",
                "service": cand_api_id,
                "quantity": qty,
            }
            if order.get("link"):
                test_payload["link"] = order["link"]
            if order.get("comments"):
                test_payload["comments"] = order["comments"]
                
            res = action(provider["api_url"], test_payload, timeout=20)
            if isinstance(res, dict) and res.get("order"):
                update_service_api(original_svc["id"], cand_api_id, candidate.get("cost_rate"))
                add_log(f"สลับบริการอัตโนมัติสำหรับบริการ #{original_svc['id']} ไปใช้ Provider Service #{cand_api_id} ({candidate['name']})", "-")
                return res.get("order"), cand_api_id, candidate
            if isinstance(res, dict) and res.get("error") and "Incorrect service ID" not in str(res.get("error")):
                update_service_api(original_svc["id"], cand_api_id, candidate.get("cost_rate"))
                return None, cand_api_id, candidate
    except Exception as exc:
        pass
    return None, None, None


def send_order_row(order):
    if not order:
        return False, "no_order"
    svc = get_service(order.get("service_id")) if order.get("service_id") else None
    pid = (svc or {}).get("provider_id") or order.get("provider_id")
    if not pid or not svc:
        update_order(order["id"], api_error="no_service")
        return False, "no_service"
    provider = get_provider(pid)
    if not provider:
        update_order(order["id"], api_error="no_provider")
        return False, "no_provider"
    
    api_svc_id = svc.get("api_service")
    payload = {
        "key": provider["api_key"],
        "action": "add",
        "service": api_svc_id,
        "quantity": order["quantity"],
    }
    if order.get("link"):
        payload["link"] = order["link"]
    if order.get("comments"):
        payload["comments"] = order["comments"]
        
    result = None
    if api_svc_id:
        result = action(provider["api_url"], payload)
    
    api_oid = None
    if isinstance(result, dict):
        api_oid = result.get("order")
    if api_oid:
        update_order(order["id"], api_orderid=str(api_oid), status="processing", api_error="-")
        return True, str(api_oid)
        
    # Auto-Fallback: If Incorrect service ID or missing service ID, find closest active service with similar rate
    err_str = str(result.get("error") if isinstance(result, dict) else result or "")
    if "Incorrect service ID" in err_str or not api_svc_id:
        fallback_oid, fallback_sid, cand = resolve_fallback_service(order, svc, provider)
        if fallback_oid:
            update_order(order["id"], api_orderid=str(fallback_oid), status="processing", api_error="-")
            return True, str(fallback_oid)
        elif fallback_sid:
            payload["service"] = fallback_sid
            retry_res = action(provider["api_url"], payload)
            if isinstance(retry_res, dict) and retry_res.get("order"):
                update_order(order["id"], api_orderid=str(retry_res["order"]), status="processing", api_error="-")
                return True, str(retry_res["order"])
                
    update_order(order["id"], api_error=str(result)[:400], status="pending")
    return False, str(result)[:400]


def send_orders():
    sent = 0
    errors = 0
    for order in pending_send_orders():
        ok, _msg = send_order_row(order)
        if ok:
            sent += 1
        else:
            errors += 1
    return sent, errors


def send_one_order(oid):
    order = get_order(oid)
    if not order:
        return False, "ไม่พบออเดอร์"
    if order.get("api_orderid") and str(order.get("status") or "") not in ("pending",):
        return False, "มีรหัส API แล้ว ให้กดดึงสถานะ"
    return send_order_row(order)


def sync_order_status(order):
    if not order:
        return False, "ไม่พบออเดอร์"
    pid = order.get("provider_id")
    if not pid:
        svc = get_service(order.get("service_id")) if order.get("service_id") else None
        pid = (svc or {}).get("provider_id")
    provider = get_provider(pid) if pid else None
    if not provider or not order.get("api_orderid"):
        return False, "ยังไม่มีรหัส API หรือผู้ให้บริการ"
    result = action(provider["api_url"], {
        "key": provider["api_key"],
        "action": "status",
        "order": order["api_orderid"],
    })
    if not isinstance(result, dict) or result.get("error"):
        err = ""
        if isinstance(result, dict):
            err = str(result.get("error") or "")
        else:
            err = str(result or "")
        return False, err or "ดึงสถานะไม่สำเร็จ"
    statu = str(result.get("status") or "").replace(" ", "").lower()
    start = result.get("start_count") or 0
    remains = result.get("remains") or 0
    mapped = "processing"
    if statu in ("completed", "complete", "success"):
        mapped = "completed"
    elif statu in ("partial",):
        mapped = "partial"
    elif statu in ("canceled", "cancelled", "refunded"):
        mapped = "canceled"
    elif statu in ("inprogress", "processing", "pending"):
        mapped = "processing"
    update_order(order["id"], status=mapped, start_count=str(start), remains=str(remains), api_error="-")
    if mapped == "canceled":
        refund_order(order["id"])
    elif mapped == "partial":
        try:
            qty = float(order.get("quantity") or 0)
            rem = float(remains or 0)
            charge = float(order.get("charge") or 0)
            if qty > 0 and rem > 0:
                refund_order(order["id"], round(charge * rem / qty, 2))
        except Exception:
            pass
    return True, mapped


def check_one_order(oid):
    return sync_order_status(get_order(oid))


def check_statuses():
    updated = 0
    for order in active_status_orders():
        ok, _msg = sync_order_status(order)
        if ok:
            updated += 1
    return updated


def refresh_balances():
    from db import list_providers
    n = 0
    for p in list_providers():
        full = get_provider(p["id"])
        result = action(full["api_url"], {"key": full["api_key"], "action": "balance"})
        if isinstance(result, dict) and "balance" in result:
            save_provider_balance(p["id"], result.get("balance"), result.get("currency") or "")
            n += 1
    return n


def _parse_ts(value):
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def shop_rebuild_due(hours=SHOP_REBUILD_HOURS):
    from db import connect, get_settings, shop_manual_locked
    # Admin emptied/customized shop — do not auto-rebuild from API
    if shop_manual_locked():
        return False
    # Large curated shops (full catalog import) — sync prices only, never cull via pick_best
    con = connect()
    n = con.execute("SELECT COUNT(*) FROM services WHERE status='active'").fetchone()[0]
    con.close()
    if int(n or 0) >= 400:
        return False
    last = _parse_ts(get_settings().get("shop_rebuild_at"))
    if not last:
        return True
    if (datetime.now() - last).total_seconds() >= hours * 3600:
        return True
    return int(n or 0) == 0


def refresh_catalogs(force_shop=False):
    from db import get_settings, list_providers, replace_provider_catalog, save_settings, sync_listed_from_catalog, shop_manual_locked
    from db import now as db_now
    from smm_api import normalize_services
    from catalog_pick import rebuild_best_shop
    try:
        providers = list_providers()
        if not providers:
            return 0
        last = 0
        try:
            last = int(get_settings().get("catalog_sync_pid") or 0)
        except (TypeError, ValueError):
            last = 0
        nxt = None
        for row in providers:
            if int(row["id"]) > last:
                nxt = row
                break
        if nxt is None:
            nxt = providers[0]
        full = get_provider(nxt["id"])
        if not full:
            return 0
        result = action(full["api_url"], {"key": full["api_key"], "action": "services"}, timeout=90)
        items, err = normalize_services(result)
        if err or not items:
            save_settings({"catalog_sync_pid": str(nxt["id"])})
            add_cron_log("catalog", "pid=%s fetch_fail %s" % (nxt["id"], (err or "empty")[:160]))
            # Do not rebuild/sync against a failed fetch — that culls the shop.
            return 0
        currency = (full.get("currency") or "USD").strip() or "USD"
        # Prefer currency from first service row when present
        for it in items:
            if isinstance(it, dict) and (it.get("currency") or it.get("Currency")):
                currency = str(it.get("currency") or it.get("Currency") or currency).strip() or currency
                break
        n_cat = replace_provider_catalog(nxt["id"], items, currency)
        if n_cat <= 0:
            add_cron_log("catalog", "pid=%s skip_empty_replace" % nxt["id"])
            return 0
        do_rebuild = (force_shop or shop_rebuild_due()) and not shop_manual_locked()
        if do_rebuild:
            stats = rebuild_best_shop(nxt["id"], fetch=False) or {}
            # Still align any remaining listed rows to live rates
            sync_stats = sync_listed_from_catalog(nxt["id"]) or {}
            save_settings({
                "catalog_sync_pid": str(nxt["id"]),
                "catalog_synced_at": db_now(),
                "shop_rebuild_at": db_now(),
                "shop_synced_at": db_now(),
            })
            add_cron_log("shop", "picked=%s added=%s updated=%s removed=%s cats=%s sync_active=%s sync_inactive=%s" % (
                stats.get("picked") or 0,
                stats.get("added") or 0,
                stats.get("updated") or 0,
                stats.get("removed") or 0,
                stats.get("cats") or 0,
                sync_stats.get("active") or 0,
                sync_stats.get("inactive") or 0,
            ))
        else:
            sync_stats = sync_listed_from_catalog(nxt["id"]) or {}
            save_settings({
                "catalog_sync_pid": str(nxt["id"]),
                "catalog_synced_at": db_now(),
                "shop_synced_at": db_now(),
            })
            add_cron_log(
                "sync",
                "pid=%s catalog=%s listed=%s active=%s inactive=%s dead=%s removed=%s" % (
                    nxt["id"],
                    sync_stats.get("catalog") or 0,
                    sync_stats.get("listed") or 0,
                    sync_stats.get("active") or 0,
                    sync_stats.get("inactive") or 0,
                    sync_stats.get("dead_marked") or 0,
                    sync_stats.get("removed") or 0,
                ),
            )
        return len(items)
    except Exception as exc:
        try:
            add_cron_log("catalog", "error " + str(exc)[:240])
        except Exception:
            pass
        return 0


def refresh_shop():
    return refresh_catalogs(force_shop=True)


def run_all():
    init_db()
    sent, err = send_orders()
    checked = check_statuses()
    bals = refresh_balances()
    from store import process_dripfeeds, process_subscriptions, process_tasks
    drips = process_dripfeeds()
    subs = process_subscriptions()
    tasks = process_tasks()
    catalog = refresh_catalogs()
    blog_n = 0
    try:
        from blog_content import publish_next_blog
        blog_n = publish_next_blog() or 0
    except Exception:
        blog_n = 0
    detail = "send=%s err=%s status=%s balance=%s drip=%s sub=%s task=%s catalog=%s blog=%s" % (
        sent, err, checked, bals, drips, subs, tasks, catalog, blog_n
    )
    add_cron_log("pull", detail)
    add_log("cron " + detail, "-")
    try:
        from db_backup import schedule_backup
        schedule_backup("cron")
    except Exception:
        pass
    return detail


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "shop":
        print("shop", refresh_shop())
    else:
        print(run_all())