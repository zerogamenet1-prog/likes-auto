"""Detect which order inputs a shop service needs (link, comments, etc.)."""

import re

_COMMENT_TYPES = frozenset({
    "custom comments",
    "custom comments package",
    "comment replies",
    "comment reply",
    "random comments",
    "auto comments",
    "positive comments",
    "super comments",
    "live comments",
})

_COMMENT_LIKE_HINTS = (
    "comment like",
    "comment likes",
    "likes comment",
    "ไลค์คอมเม",
    "ถูกใจคอมเม",
)

_NO_LINK_TYPES = frozenset({
    "subscriptions",
    "subscription",
})


def _blob(item):
    typ = (item.get("catalog_type") or item.get("type") or "default").strip().lower()
    name = (item.get("name") or "").lower()
    cat = (item.get("category") or item.get("category_th") or "").lower()
    return typ, name, cat, "%s %s %s" % (typ, name, cat)


def _is_comment_likes(blob):
    return any(h in blob for h in _COMMENT_LIKE_HINTS)


def order_fields(item):
    if not item:
        return {"needs_link": True, "needs_comments": False, "sync_qty_comments": False}
    typ, name, cat, blob = _blob(item)
    comment_likes = _is_comment_likes(blob)
    needs_comments = False
    if not comment_likes:
        if typ in _COMMENT_TYPES:
            needs_comments = True
        elif "custom comment" in blob or "คอมเมนต์กำหนด" in blob:
            needs_comments = True
        elif re.search(r"\bcomments?\b", typ) and "package" not in typ and "like" not in typ:
            needs_comments = True
        elif ("เพิ่มคอมเมนต์" in cat or cat.endswith("คอมเมนต์")) and not comment_likes:
            if "reply" not in blob and "like" not in blob and "ถูกใจ" not in name:
                needs_comments = True
        elif "comment" in name and "เพิ่ม" in name and not comment_likes:
            needs_comments = True
    needs_link = typ not in _NO_LINK_TYPES and "subscription" not in typ
    return {
        "needs_link": needs_link,
        "needs_comments": needs_comments,
        "sync_qty_comments": needs_comments,
    }


def count_comment_lines(text):
    return len([ln for ln in (text or "").splitlines() if ln.strip()])


def normalize_comments(text):
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(lines)


def service_refill_ok(svc, order_label=""):
    catalog = (svc or {}).get("catalog_name") or ""
    name = (svc or {}).get("name") or order_label or ""
    blob = ("%s %s" % (catalog, name)).lower()
    if not blob.strip() and order_label:
        blob = str(order_label).lower()
    refill_raw = str((svc or {}).get("catalog_refill") or "").lower().strip()
    if refill_raw in {"0", "false", "no", "n"}:
        return False
    if refill_raw in {"1", "true", "yes", "y"}:
        return True
    if "no refill" in blob or "refill: no" in blob or "refill:no" in blob:
        return False
    if "ไม่มีรับประกัน" in blob or "ไม่มีประกัน" in blob:
        return False
    if "refill" in blob or "guarantee" in blob or "lifetime" in blob:
        return True
    if "รับประกัน" in blob or "เติมยอด" in blob:
        return True
    return False