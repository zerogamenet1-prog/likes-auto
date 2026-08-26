"""SMM Panel compatible API (Perfect Panel / Followiz style)."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from db import calc_charge, create_order, get_service, get_settings, init_db, list_services
from service_fields import count_comment_lines, normalize_comments, order_fields, service_refill_ok
from store import create_dripfeed, create_task, fetch_one, get_client_by_key

router = APIRouter()

_STATUS_MAP = {
    "pending": "Pending",
    "processing": "In progress",
    "inprogress": "In progress",
    "completed": "Completed",
    "partial": "Partial",
    "canceled": "Canceled",
    "cancelled": "Canceled",
}

_ERR_MAP = {
    "ไม่พบบริการ": "Incorrect service ID",
    "จำนวนไม่อยู่ในช่วงที่กำหนด": "Incorrect quantity",
    "ไม่พบบัญชี": "Incorrect API key",
    "ยอดเงินไม่พอ กรุณาเติมเงิน": "Not enough funds",
    "กรุณากรอกลิงก์": "Incorrect link",
    "กรุณากรอกคอมเมนต์ (แยกแต่ละบรรทัด)": "Incorrect comments",
    "กรุณากรอกคอมเมนต์อย่างน้อย 1 บรรทัด": "Incorrect comments",
    "มีคำขอค้างอยู่แล้ว": "Order in progress",
    "บริการนี้ไม่รองรับการเติมยอด (ไม่มีรับประกัน)": "Refill unavailable",
}


def payload(request: Request, form: dict):
    data = dict(form or {})
    for k, v in request.query_params.items():
        data.setdefault(k, v)
    # normalize common aliases used by panels
    if "service_id" in data and "service" not in data:
        data["service"] = data["service_id"]
    if "order_id" in data and "order" not in data:
        data["order"] = data["order_id"]
    return data


def _api_err(msg):
    text = str(msg or "Incorrect request")
    return _ERR_MAP.get(text, text if text[:1].isascii() else "Incorrect request")


def _norm_type(raw):
    t = str(raw or "Default").strip()
    low = t.lower()
    aliases = {
        "default": "Default",
        "package": "Package",
        "custom comments": "Custom Comments",
        "custom comments package": "Custom Comments",
        "comment replies": "Comment Replies",
        "mentions": "Mentions",
        "mentions custom list": "Mentions Custom List",
        "mentions hashtag": "Mentions with Hashtags",
        "mentions with hashtags": "Mentions with Hashtags",
        "subscriptions": "Subscriptions",
        "subscription": "Subscriptions",
        "poll": "Poll",
        "seo": "SEO",
        "web traffic": "Web Traffic",
        "drip-feed": "Default",
        "drip feed": "Default",
    }
    return aliases.get(low, t.title() if t else "Default")


def _status_payload(row):
    st = _STATUS_MAP.get(str(row.get("status") or "").lower(), "Pending")
    return {
        "charge": str(row.get("charge") or 0),
        "start_count": str(row.get("start_count") or 0),
        "status": st,
        "remains": str(row.get("remains") or 0),
        "currency": "THB",
    }


def _parse_ids(raw, limit=100):
    out = []
    for part in str(raw or "").replace(" ", "").split(","):
        if not part:
            continue
        try:
            out.append(int(part))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def _svc_category(s):
    plat = (s.get("platform") or "").strip()
    cat = (s.get("category") or "").strip()
    if plat and cat and cat.lower() != plat.lower():
        return "%s - %s" % (plat, cat)
    return plat or cat or "Other"


@router.api_route("/api/v2", methods=["GET", "POST"])
async def api_v2(request: Request):
    init_db()
    if request.method == "POST":
        ctype = request.headers.get("content-type", "")
        if "json" in ctype:
            try:
                form = await request.json()
            except Exception:
                form = {}
        else:
            form = dict(await request.form())
    else:
        form = {}
    data = payload(request, form)
    action = str(data.get("action") or "").strip().lower()
    key = str(data.get("key") or "").strip()
    user = get_client_by_key(key)
    if not action or not key:
        return JSONResponse({"error": "Incorrect request"})
    if not user:
        return JSONResponse({"error": "Incorrect API key"})
    if user.get("status") != "active":
        return JSONResponse({"error": "Account inactive"})

    if action == "balance":
        return JSONResponse({
            "balance": "%.5f" % float(user.get("balance") or 0),
            "currency": "THB",
        })

    if action == "services":
        items = []
        for s in list_services():
            label = "%s %s" % (s.get("platform") or "", s.get("name") or "")
            refill = service_refill_ok(s, label)
            typ = _norm_type(s.get("catalog_type"))
            fields = order_fields(s)
            if fields.get("needs_comments") and typ == "Default":
                typ = "Custom Comments"
            item = {
                "service": int(s["id"]),
                "name": label.strip() or ("Service %s" % s["id"]),
                "type": typ,
                "category": _svc_category(s),
                "rate": "%.4f" % float(s.get("rate") or 0),
                "min": str(int(s.get("min_qty") or 1)),
                "max": str(int(s.get("max_qty") or 100000)),
                "refill": bool(refill),
                "cancel": True,
            }
            items.append(item)
        return JSONResponse(items)

    if action == "status":
        multi = str(data.get("orders") or "").strip()
        if multi:
            out = {}
            for oid in _parse_ids(multi):
                row = fetch_one("SELECT * FROM orders WHERE id=? AND client=?", (oid, user["username"]))
                out[str(oid)] = _status_payload(row) if row else {"error": "Incorrect order ID"}
            return JSONResponse(out)
        try:
            oid = int(data.get("order"))
        except Exception:
            return JSONResponse({"error": "Incorrect order ID"})
        row = fetch_one("SELECT * FROM orders WHERE id=? AND client=?", (oid, user["username"]))
        if not row:
            return JSONResponse({"error": "Incorrect order ID"})
        return JSONResponse(_status_payload(row))

    if action == "add":
        try:
            sid = int(data.get("service"))
        except Exception:
            return JSONResponse({"error": "Incorrect service ID"})
        link = str(data.get("link") or data.get("username") or "").strip()
        comments = normalize_comments(
            str(data.get("comments") or data.get("usernames") or data.get("keywords") or "")
        )
        try:
            qty = int(float(data.get("quantity") or 0))
        except Exception:
            qty = 0
        if comments and not qty:
            qty = count_comment_lines(comments) or 1

        # Optional drip-feed (Perfect Panel style)
        try:
            runs = int(data.get("runs") or 0)
            interval = int(data.get("interval") or 0)
        except Exception:
            runs, interval = 0, 0
        if runs > 1 and interval >= 0:
            did, err = create_dripfeed(user["username"], sid, link, qty or 1, runs, interval)
            if err:
                return JSONResponse({"error": _api_err(err)})
            return JSONResponse({"order": did})

        if not link and not comments:
            return JSONResponse({"error": "Incorrect link"})
        oid, err = create_order(user["username"], sid, link, qty or 1, comments)
        if err:
            return JSONResponse({"error": _api_err(err)})
        return JSONResponse({"order": oid})

    if action == "refill":
        settings = get_settings()
        if str(settings.get("auto_refill", "1")) == "0":
            return JSONResponse({"error": "Refill unavailable"})
        multi = str(data.get("orders") or "").strip()
        ids = _parse_ids(multi or data.get("order"))
        if not ids:
            return JSONResponse({"error": "Incorrect order ID"})

        def one_refill(oid):
            row = fetch_one("SELECT * FROM orders WHERE id=? AND client=?", (oid, user["username"]))
            if not row:
                return None, "Incorrect order ID"
            svc = get_service(row.get("service_id")) if row.get("service_id") else None
            if not service_refill_ok(svc, row.get("service") or ""):
                return None, "Refill unavailable"
            if (row.get("status") or "") not in {"completed", "partial"}:
                return None, "Incorrect order status"
            tid, err = create_task(oid, user["username"], "refill")
            if err:
                return None, _api_err(err)
            return tid or 1, None

        if not multi and len(ids) == 1:
            tid, err = one_refill(ids[0])
            if err:
                return JSONResponse({"error": err})
            return JSONResponse({"refill": str(tid)})
        out = []
        for oid in ids:
            tid, err = one_refill(oid)
            if err:
                out.append({"order": oid, "refill": {"error": err}})
            else:
                out.append({"order": oid, "refill": tid})
        return JSONResponse(out)

    if action == "cancel":
        ids = _parse_ids(data.get("orders") or data.get("order"))
        if not ids:
            return JSONResponse({"error": "Incorrect order ID"})
        out = []
        for oid in ids:
            row = fetch_one("SELECT * FROM orders WHERE id=? AND client=?", (oid, user["username"]))
            if not row:
                out.append({"order": oid, "cancel": {"error": "Incorrect order ID"}})
                continue
            if (row.get("status") or "") not in {"pending", "processing", "inprogress"}:
                out.append({"order": oid, "cancel": {"error": "Incorrect order status"}})
                continue
            tid, err = create_task(oid, user["username"], "cancel")
            if err:
                out.append({"order": oid, "cancel": {"error": _api_err(err)}})
            else:
                out.append({"order": oid, "cancel": tid or 1})
        return JSONResponse(out)

    if action in {"refill_status", "refillstatus"}:
        # Best-effort for panels that poll refill status
        rid = data.get("refill") or data.get("refills")
        ids = _parse_ids(rid)
        if not ids:
            return JSONResponse({"error": "Incorrect request"})
        if len(ids) == 1 and "," not in str(rid or ""):
            row = fetch_one("SELECT * FROM tasks WHERE id=? AND client=? AND kind='refill'", (ids[0], user["username"]))
            if not row:
                return JSONResponse({"error": "Refill not found"})
            st = {"pending": "Pending", "success": "Completed", "failed": "Rejected", "canceled": "Rejected"}.get(
                row.get("status"), "Pending"
            )
            return JSONResponse({"status": st})
        out = []
        for rid_n in ids:
            row = fetch_one("SELECT * FROM tasks WHERE id=? AND client=? AND kind='refill'", (rid_n, user["username"]))
            if not row:
                out.append({"refill": rid_n, "status": {"error": "Refill not found"}})
            else:
                st = {"pending": "Pending", "success": "Completed", "failed": "Rejected", "canceled": "Rejected"}.get(
                    row.get("status"), "Pending"
                )
                out.append({"refill": rid_n, "status": st})
        return JSONResponse(out)

    return JSONResponse({"error": "Incorrect request"})
