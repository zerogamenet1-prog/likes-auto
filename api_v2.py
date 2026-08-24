from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from db import calc_charge, create_order, get_service, init_db, list_services
from store import fetch_one, get_client_by_key

router = APIRouter()


def payload(request: Request, form: dict):
    data = dict(form or {})
    for k, v in request.query_params.items():
        data.setdefault(k, v)
    return data


@router.api_route("/api/v2", methods=["GET", "POST"])
async def api_v2(request: Request):
    init_db()
    if request.method == "POST":
        ctype = request.headers.get("content-type", "")
        if "json" in ctype:
            form = await request.json()
        else:
            form = dict(await request.form())
    else:
        form = {}
    data = payload(request, form)
    action = str(data.get("action") or "")
    key = str(data.get("key") or "")
    user = get_client_by_key(key)
    if not action or not key:
        return JSONResponse({"error": "Incorrect request"})
    if not user:
        return JSONResponse({"error": "Incorrect API key"})
    if user.get("status") != "active":
        return JSONResponse({"error": "Account inactive"})
    if action == "balance":
        return JSONResponse({"balance": float(user.get("balance") or 0), "currency": "THB"})
    if action == "services":
        items = []
        for s in list_services():
            items.append({
                "service": s["id"],
                "name": "%s %s" % (s.get("platform") or "", s.get("name") or ""),
                "type": "Default",
                "category": s.get("platform") or "Other",
                "rate": s.get("rate") or 0,
                "min": s.get("min_qty") or 1,
                "max": s.get("max_qty") or 100000,
            })
        return JSONResponse(items)
    if action == "status":
        oid = data.get("order")
        row = fetch_one("SELECT * FROM orders WHERE id=? AND client=?", (oid, user["username"]))
        if not row:
            return JSONResponse({"error": "Incorrect order ID"})
        return JSONResponse({
            "charge": row.get("charge") or 0,
            "start_count": row.get("start_count") or 0,
            "status": (row.get("status") or "Pending").title(),
            "remains": row.get("remains") or 0,
            "currency": "THB",
        })
    if action == "add":
        try:
            sid = int(data.get("service"))
            qty = int(data.get("quantity"))
        except Exception:
            return JSONResponse({"error": "Incorrect request"})
        link = str(data.get("link") or "").strip()
        if not link:
            return JSONResponse({"error": "Incorrect link"})
        oid, err = create_order(user["username"], sid, link, qty)
        if err:
            return JSONResponse({"error": err})
        svc = get_service(sid)
        charge = calc_charge(svc["rate"], qty) if svc else 0
        return JSONResponse({"order": oid, "charge": charge, "currency": "THB"})
    return JSONResponse({"error": "Incorrect request"})
