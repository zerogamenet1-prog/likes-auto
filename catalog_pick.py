import re

from db import (
    connect,
    get_provider,
    get_settings,
    init_db,
    list_provider_catalog,
    price_cfg,
    replace_provider_catalog,
    save_provider_balance,
    save_settings,
    sell_thb,
    shop_cache_clear,
    split_category,
    to_thb,
)
from smm_api import action, normalize_services

MIN_PER_CAT = 5
MAX_PER_CAT = 8

SKIP_TYPES = {
    "subscriptions",
    "subscription",
    "mentions with hashtags",
    "mentions custom list",
    "mentions user followers",
    "mentions media likers",
    "invites from groups",
    "poll",
}
KEEP_TYPES = {
    "default",
    "package",
    "custom comments",
    "mentions",
    "comment replies",
    "drip-feed",
    "",
}
SKIP_WORDS = (
    "not working",
    "disabled",
    "test service",
    "do not order",
    "wrong",
    "failed",
    "can fully drop",
    "bots with no refill",
    "low quality bots",
)
SKIP_PLATS = (
    "kwai",
    "vk.com",
    "rumble",
    "trovo",
    "clubhouse",
    "quora",
    "audiomack",
    "snackvideo",
    "spinnin",
    "jap exclusive",
)
KEEP_PLAT_KEYS = (
    "facebook",
    "instagram",
    "tiktok",
    "youtube",
    "telegram",
    "twitter",
    "spotify",
    "website",
    "twitch",
    "soundcloud",
    "shopee",
    "whatsapp",
    "line",
    "threads",
    "pinterest",
    "reddit",
    "seo",
    "google",
)
KINDS = (
    ("live", ("live stream", "livestream", "live views", "live comments", "live video", "live likes")),
    ("story", ("story views", "stories", "story")),
    ("reels", ("reel views", "reels", "reel")),
    ("page_likes", ("page likes", "page like")),
    ("impressions", ("impressions", "impression", "reach")),
    ("visits", ("profile visits", "profile visit", "highlights")),
    ("plays", ("monthly listeners", "listeners", "plays", "play")),
    ("followers", ("page followers", "profile followers", "followers", "follower", "subscribers", "subscriber")),
    ("likes", ("post likes", "photo likes", "likes", "like", "reactions", "reaction")),
    ("views", ("video views", "watch time", "watch hours", "views", "view")),
    ("comments", ("custom comments", "comments", "comment")),
    ("shares", ("retweets", "reposts", "shares", "share")),
    ("saves", ("bookmarks", "saves", "save")),
    ("members", ("group members", "channel members", "members", "member")),
    ("friends", ("friends", "friend")),
    ("traffic", ("website traffic", "visitors", "traffic")),
    ("reviews", ("reviews", "review", "rating")),
)
KIND_TH = {
    "live": "ไลฟ์สตรีม",
    "story": "เพิ่มวิวสตอรี่",
    "reels": "เพิ่มวิวรีล",
    "page_likes": "เพิ่มไลค์เพจ",
    "impressions": "เพิ่มการแสดงผล",
    "visits": "เพิ่มผู้เข้าชมโปรไฟล์",
    "plays": "เพิ่มยอดเล่น",
    "followers": "เพิ่มผู้ติดตาม",
    "likes": "เพิ่มไลค์",
    "views": "เพิ่มวิว",
    "comments": "เพิ่มคอมเมนต์",
    "shares": "เพิ่มแชร์",
    "saves": "เพิ่มเซฟ",
    "members": "เพิ่มสมาชิก",
    "friends": "เพิ่มเพื่อน",
    "traffic": "ทราฟฟิกเว็บไซต์",
    "reviews": "เพิ่มรีวิว",
}
ROLE_TH = {
    "thai": "คนไทย",
    "cheap": "ราคาถูกสุด",
    "hq": "คุณภาพสูง",
    "refill": "มีรับประกัน",
    "fast": "เริ่มเร็ว",
    "us": "อเมริกา",
    "extra": "คุ้มราคา",
}
GEO_TH = {
    "th": "คนไทย",
    "us": "อเมริกา",
    "br": "บราซิล",
    "in": "อินเดีย",
    "ar": "อาหรับ",
    "kr": "เกาหลี",
    "vn": "เวียดนาม",
}
SHOP_KIND = {
    "page_likes": "likes",
    "friends": "followers",
    "visits": "impressions",
    "reviews": "likes",
}


def _has(text, word):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", text) is not None


def kind_of(name, category):
    text = ("%s %s" % (name or "", category or "")).lower()
    for kind, keys in KINDS:
        for key in keys:
            if _has(text, key):
                return kind
    return "other"


def geo_of(name, category):
    text = ("%s %s" % (name or "", category or "")).lower()
    if "thai" in text or "thailand" in text:
        return "th"
    if "brazil" in text:
        return "br"
    if "india" in text or "indian" in text:
        return "in"
    if "arab" in text:
        return "ar"
    if "usa" in text or "america" in text or "united states" in text:
        return "us"
    if "korea" in text:
        return "kr"
    if "vietnam" in text:
        return "vn"
    return "ww"


def plat_keep(plat):
    low = (plat or "").lower()
    if any(word in low for word in SKIP_PLATS):
        return False
    return any(key in low for key in KEEP_PLAT_KEYS)


def cost_cap(kind):
    if kind in {"followers", "members", "friends", "reviews"}:
        return 180.0
    if kind in {"live", "traffic"}:
        return 120.0
    return 90.0


def quality_score(item):
    text = ("%s %s" % (item.get("name") or "", item.get("category") or "")).lower()
    score = 0
    refill = str(item.get("refill") or "").lower() in {"1", "true", "yes"}
    if refill or "refill" in text or "guarantee" in text or "lifetime" in text:
        score += 30
    if "hq" in text or "premium" in text or "high quality" in text or "organic" in text or "monetizable" in text:
        score += 22
    if _has(text, "real"):
        score += 14
    if "non drop" in text or "no drop" in text:
        score += 16
    if "instant" in text or "fastest" in text or "express" in text or _has(text, "fast"):
        score += 8
    if "thai" in text or "thailand" in text:
        score += 10
    if _has(text, "bot") or "low quality" in text or _has(text, "lq") or _has(text, "fake") or "fully drop" in text:
        score -= 40
    if "cheap" in text and "refill" not in text and not refill:
        score -= 4
    try:
        min_qty = int(item.get("min_qty") or item.get("min") or 1)
    except (TypeError, ValueError):
        min_qty = 1
    if min_qty <= 50:
        score += 3
    elif min_qty >= 5000:
        score -= 4
    return score


def kind_label(kind):
    return KIND_TH.get(kind, "บริการยอดนิยม")


def display_name(item, role, used):
    base = kind_label(item.get("_kind"))
    tag = ROLE_TH.get(role) or GEO_TH.get(item.get("_geo")) or "แนะนำ"
    name = "%s · %s" % (base, tag)
    if name in used:
        geo = GEO_TH.get(item.get("_geo") or "")
        if geo and geo not in name:
            name = "%s · %s" % (name, geo)
    if name in used:
        name = "%s · ทางเลือก %s" % (base, len(used) + 1)
    used.add(name)
    return name


def _prepare(items, usd_rate=35):
    groups = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        cat = str(item.get("category") or "")
        typ = str(item.get("type") or "Default").strip().lower()
        if typ in SKIP_TYPES or typ not in KEEP_TYPES:
            continue
        low = (name + " " + cat).lower()
        if any(word in low for word in SKIP_WORDS):
            continue
        try:
            raw = float(item.get("rate") or 0)
        except (TypeError, ValueError):
            raw = 0.0
        if raw <= 0:
            continue
        currency = item.get("currency") or "USD"
        cost = to_thb(raw, currency, usd_rate)
        if cost <= 0:
            continue
        plat, _rest = split_category(cat)
        if not plat_keep(plat):
            continue
        kind = SHOP_KIND.get(kind_of(name, cat), kind_of(name, cat))
        if kind == "other":
            continue
        rec = dict(item)
        rec["_cost"] = cost
        rec["_score"] = quality_score(item)
        rec["_plat"] = plat
        rec["_kind"] = kind
        rec["_geo"] = geo_of(name, cat)
        rec["_api"] = str(item.get("api_service") or item.get("service") or "")
        rec["_refill"] = str(item.get("refill") or "").lower() in {"1", "true", "yes"} or "refill" in low or "guarantee" in low
        rec["_fast"] = "instant" in low or "fastest" in low or "express" in low or _has(low, "fast")
        rec["_cat"] = kind_label(kind)
        if rec["_api"]:
            groups.setdefault((plat, kind), []).append(rec)
    return groups


def pick_group(recs):
    if not recs:
        return []
    kind = recs[0]["_kind"]
    cap = cost_cap(kind)
    pool = [row for row in recs if row["_score"] >= 8 and row["_cost"] <= cap]
    if len(pool) < MIN_PER_CAT:
        pool = [row for row in recs if row["_score"] >= 0 and row["_cost"] <= cap]
    if len(pool) < MIN_PER_CAT:
        pool = [row for row in recs if row["_score"] >= -8 and row["_cost"] <= cap * 1.35]
    if len(pool) < MIN_PER_CAT:
        pool = [row for row in recs if row["_cost"] <= cap * 2.2]
    if not pool:
        return []
    picked = []
    used = set()

    def take(role, pred, keyfn):
        rows = [row for row in pool if row["_api"] not in used and pred(row)]
        if not rows:
            return
        rows.sort(key=keyfn)
        row = dict(rows[0])
        row["_role"] = role
        used.add(row["_api"])
        picked.append(row)

    take("thai", lambda row: row["_geo"] == "th", lambda row: (row["_cost"], -row["_score"]))
    take("refill", lambda row: row["_refill"] and row["_score"] >= 12, lambda row: (-row["_score"], row["_cost"]))
    take("hq", lambda row: row["_score"] >= 20, lambda row: (row["_cost"], -row["_score"]))
    take("fast", lambda row: row["_fast"], lambda row: (row["_cost"], -row["_score"]))
    take("cheap", lambda row: True, lambda row: (row["_cost"], -row["_score"]))
    take("us", lambda row: row["_geo"] == "us", lambda row: (row["_cost"], -row["_score"]))
    while len(picked) < MIN_PER_CAT:
        before = len(picked)
        take("extra", lambda row: True, lambda row: (row["_cost"], -row["_score"]))
        if len(picked) == before:
            break
    while len(picked) < MAX_PER_CAT:
        before = len(picked)
        take("extra", lambda row: row["_score"] >= 8, lambda row: (-row["_score"], row["_cost"]))
        if len(picked) == before:
            break
    names = set()
    for row in picked:
        row["_shop_name"] = display_name(row, row.get("_role") or "extra", names)
        row["_shop_cat"] = kind_label(row["_kind"])
    return picked


def pick_best(items, usd_rate=35):
    groups = _prepare(items, usd_rate)
    picked = []
    for recs in groups.values():
        picked.extend(pick_group(recs))
    buckets = {}
    for row in picked:
        buckets.setdefault((row["_plat"], row["_kind"]), []).append(row)
    keep = []
    for recs in buckets.values():
        if len(recs) >= MIN_PER_CAT:
            keep.extend(recs)
    keep.sort(key=lambda row: (row["_plat"], row.get("_shop_cat") or "", row["_cost"]))
    return keep


def apply_picked_services(pid, picked, cfg):
    rows = []
    keep = []
    for item in picked:
        api_sid = item.get("_api") or item.get("api_service") or item.get("service")
        if api_sid is None or str(api_sid) == "":
            continue
        api_sid = str(api_sid)
        plat = item.get("_plat") or split_category(item.get("category") or "")[0]
        sell = sell_thb(item.get("rate") or 0, item.get("currency") or "USD", cfg["usd"], cfg["pct"], 0)
        try:
            min_qty = int(item.get("min_qty") or 1)
        except (TypeError, ValueError):
            min_qty = 1
        try:
            max_qty = int(item.get("max_qty") or 100000)
        except (TypeError, ValueError):
            max_qty = 100000
        keep.append(api_sid)
        rows.append({
            "platform": plat,
            "name": item.get("_shop_name") or item.get("name") or ("Service %s" % api_sid),
            "rate": sell,
            "min_qty": min_qty,
            "max_qty": max_qty,
            "api_service": api_sid,
            "cost_rate": float(item.get("rate") or 0),
            "category": item.get("_shop_cat") or kind_label(item.get("_kind")),
            "currency": item.get("currency") or "USD",
        })
    con = connect()
    existing = {
        str(row["api_service"]): int(row["id"])
        for row in con.execute(
            "SELECT id, api_service FROM services WHERE provider_id=? AND IFNULL(api_service,'')!=''",
            (pid,),
        )
    }
    added = 0
    updated = 0
    for row in rows:
        vals = (
            row["platform"],
            row["name"],
            row["rate"],
            row["min_qty"],
            row["max_qty"],
            row["cost_rate"],
            row["category"],
            row["currency"],
            pid,
            row["api_service"],
        )
        if row["api_service"] in existing:
            con.execute(
                """
                UPDATE services
                SET platform=?, name=?, rate=?, min_qty=?, max_qty=?, status='active',
                    cost_rate=?, category=?, currency=?
                WHERE provider_id=? AND api_service=?
                """,
                vals,
            )
            updated += 1
        else:
            con.execute(
                """
                INSERT INTO services (platform, name, rate, min_qty, max_qty, status, provider_id, api_service, cost_rate, category, currency)
                VALUES (?,?,?,?,?,'active',?,?,?,?,?)
                """,
                (
                    row["platform"],
                    row["name"],
                    row["rate"],
                    row["min_qty"],
                    row["max_qty"],
                    pid,
                    row["api_service"],
                    row["cost_rate"],
                    row["category"],
                    row["currency"],
                ),
            )
            added += 1
    removed = 0
    if keep:
        marks = ",".join("?" * len(keep))
        cur = con.execute(
            "UPDATE services SET status='inactive' WHERE provider_id=? AND IFNULL(api_service,'')!='' AND api_service NOT IN (%s)" % marks,
            [pid] + keep,
        )
        removed = cur.rowcount or 0
    con.commit()
    con.close()
    shop_cache_clear()
    return {"added": added, "updated": updated, "removed": removed, "kept": len(keep)}


def rebuild_best_shop(provider_id, fetch=True):
    init_db()
    pid = int(provider_id)
    provider = get_provider(pid)
    if not provider:
        return {"error": "no_provider", "picked": 0, "catalog": 0}
    settings = get_settings()
    usd = settings.get("usd_rate") or 35
    save_settings({
        "profit_percent": str(settings.get("profit_percent") or "100"),
        "usd_rate": str(usd),
    })
    catalog_n = 0
    if fetch:
        result = action(provider["api_url"], {"key": provider["api_key"], "action": "services"}, timeout=120)
        items, err = normalize_services(result)
        if err or not items:
            return {"error": err or "empty_catalog", "picked": 0, "catalog": 0}
        currency = (provider.get("currency") or "USD").strip() or "USD"
        bal = action(provider["api_url"], {"key": provider["api_key"], "action": "balance"}, timeout=25)
        if isinstance(bal, dict) and bal.get("currency"):
            currency = str(bal.get("currency") or currency)
            save_provider_balance(pid, bal.get("balance"), currency)
        catalog_n = replace_provider_catalog(pid, items, currency)
    else:
        rows = list_provider_catalog(pid, limit=200000)
        catalog_n = len(rows)
    con = connect()
    rows = con.execute("SELECT * FROM provider_catalog WHERE provider_id=?", (pid,)).fetchall()
    con.close()
    catalog = [dict(x) for x in rows]
    picked = pick_best(catalog, usd)
    cfg = price_cfg(True)
    stats = apply_picked_services(pid, picked, cfg)
    cats = {}
    for item in picked:
        key = "%s | %s" % (item.get("_plat"), item.get("_shop_cat"))
        cats[key] = cats.get(key, 0) + 1
    thin = sum(1 for n in cats.values() if n < MIN_PER_CAT)
    return {
        "error": "",
        "picked": len(picked),
        "catalog": catalog_n,
        "cats": len(cats),
        "thin": thin,
        "added": stats["added"],
        "updated": stats["updated"],
        "removed": stats["removed"],
    }
