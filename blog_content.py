import re
from datetime import datetime, timedelta


def L(href, text):
    return '<a href="%s">%s</a>' % (href, text)


def excerpt_text(html, n=170):
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= n:
        return text
    return text[:n].rstrip() + "…"


def post_href(row):
    slug = (row.get("slug") or "").strip()
    if slug:
        return "/blog/" + slug
    return "/blog/" + str(row.get("id") or "")


def tag_list(row):
    return [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()]


def first_img(html):
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html or "", re.I)
    return m.group(1) if m else ""


def decorate(posts):
    out = []
    for row in posts or []:
        item = dict(row)
        item["href"] = post_href(item)
        item["excerpt"] = item.get("excerpt") or excerpt_text(item.get("body") or "")
        item["tag_list"] = tag_list(item)
        item["cover"] = (item.get("cover") or "").strip() or first_img(item.get("body") or "")
        out.append(item)
    return out


def unique_blog_slug(title, slug="", exclude_id=None):
    from cms import q_one
    from store import now as nowfn

    slug = (slug or "").strip() or _slugish(title or "")
    if not slug or slug == "topic":
        slug = "post-" + nowfn().replace(" ", "-").replace(":", "")[:16]
    base = slug
    n = 2
    while True:
        row = q_one("SELECT id FROM blog WHERE slug=?", (slug,))
        if not row:
            return slug
        if exclude_id and int(row.get("id") or 0) == int(exclude_id):
            return slug
        slug = "%s-%s" % (base, n)
        n += 1


HOME = L("/", "ปั้มไลค์")
SVC = L("/services", "ราคาปั้มไลค์")
IG = L("/services?cat=Instagram", "ปั้มไลค์ Instagram")
TT = L("/services?cat=Tiktok", "ปั้มวิว TikTok")
FB = L("/services?cat=Facebook", "ปั้มไลค์ Facebook")
YT = L("/services?cat=Youtube", "เพิ่มยอดวิว YouTube")
FAQ = L("/faq", "ไม่ขอรหัสผ่าน")
SIGN = L("/signup", "สมัครฟรี")
API = L("/api", "API เปิดร้านต่อ")
HOW = L("/#howto", "วิธีใช้งาน")
PAY = L("/#pay", "พร้อมเพย์")
ADS = L("/blog/pump-likes-vs-ads", "ยิงแอด")
MKT = L("/blog/social-proof-marketing", "การตลาดออนไลน์")


def _ps(*rows):
    return "".join("<p>%s</p>" % x for x in rows)



try:
    from blog_posts import POSTS
except Exception:
    POSTS = []

def seed_blog():
    from cms import q_one, q_run

    now = datetime.now()
    for item in POSTS:
        slug = item["slug"]
        exists = q_one("SELECT id, body FROM blog WHERE slug=?", (slug,))
        published = 0 if int(item.get("queue") or 0) > 0 else 1
        body = item["body"]
        cover = first_img(body)
        if exists:
            old = exists.get("body") or ""
            if "<img" not in old.lower() and len(body) > 800:
                q_run(
                    "UPDATE blog SET title=?, body=?, tags=?, excerpt=?, cover=? WHERE id=?",
                    (item["title"], body, item.get("tags") or "", excerpt_text(body), cover, exists["id"]),
                )
            continue
        ago = int(item.get("ago") or 0)
        created = (now - timedelta(days=ago, hours=3)).strftime("%Y-%m-%d %H:%M")
        q_run(
            "INSERT INTO blog (title, body, created_at, slug, tags, excerpt, published, cover) VALUES (?,?,?,?,?,?,?,?)",
            (
                item["title"],
                body,
                created,
                slug,
                item.get("tags") or "",
                excerpt_text(body),
                published,
                cover,
            ),
        )
    try:
        from db import get_settings, now as db_now, save_settings
        if not str((get_settings() or {}).get("blog_last_pub") or "").strip():
            save_settings({"blog_last_pub": db_now()})
    except Exception:
        pass
    return True


DAILY_PLATS = [
    ("ig", "Instagram", "/services?cat=Instagram", "ปั้มไลค์ Instagram"),
    ("tt", "TikTok", "/services?cat=Tiktok", "ปั้มวิว TikTok"),
    ("fb", "Facebook", "/services?cat=Facebook", "ปั้มไลค์ Facebook"),
    ("yt", "YouTube", "/services?cat=Youtube", "เพิ่มยอดวิว YouTube"),
    ("x", "X (Twitter)", "/services?cat=Twitter", "ปั้มไลค์ Twitter"),
    ("tg", "Telegram", "/services?cat=Telegram", "เพิ่มสมาชิก Telegram"),
]
DAILY_NICHES = [
    "ร้านอาหาร", "ร้านเสื้อผ้า", "คลินิกความงาม", "เพจข่าวสั้น", "ครีเอเตอร์",
    "ร้านกาแฟ", "ขายของออนไลน์", "ครูสอนออนไลน์", "อสังหาริมทรัพย์", "ฟิตเนส",
    "ร้านเครื่องใช้ไฟฟ้า", "เพจแม่และเด็ก",
]
DAILY_GOALS = [
    ("likes", "เพิ่มไลค์", "ปั้มไลค์"),
    ("foll", "เพิ่มผู้ติดตาม", "ปั้มฟอล"),
    ("views", "เพิ่มยอดวิว", "ปั้มวิว"),
    ("ads", "ทำคู่ยิงแอด", "ยิงแอด"),
    ("budget", "งบน้อย", "การตลาด"),
    ("new", "มือใหม่", "วิธีใช้งาน"),
]


FEATURED_TAGS = [
    "ปั้มไลค์", "ปั้มฟอล", "ปั้มวิว", "ยิงแอด", "Instagram", "TikTok",
    "Facebook", "YouTube", "การตลาด", "พร้อมเพย์", "API", "วิธีใช้งาน",
]


def _slugish(text):
    t = re.sub(r"\s+", "-", (text or "").strip().lower())
    t = re.sub(r"[^\w\-]+", "", t, flags=re.UNICODE)
    return t[:48] or "topic"


def generate_daily_post(retry=True):
    import json
    from cms import q_one, q_run
    from db import get_settings, now, save_settings

    s = get_settings() or {}
    used = []
    try:
        used = json.loads(s.get("blog_daily_used") or "[]")
    except Exception:
        used = []
    used_set = set(used)
    today = datetime.now().strftime("%Y-%m-%d")
    for plat in DAILY_PLATS:
        for niche in DAILY_NICHES:
            for goal in DAILY_GOALS:
                key = "%s-%s-%s" % (plat[0], _slugish(niche), goal[0])
                if key in used_set:
                    continue
                slug = "daily-%s-%s" % (key, today)
                if q_one("SELECT id FROM blog WHERE slug=?", (slug,)):
                    used_set.add(key)
                    continue
                plat_link = L(plat[2], plat[3])
                title = "%s สำหรับ%s บน%s" % (goal[1], niche, plat[1])
                tags = "%s, %s, %s, ปั้มไลค์" % (plat[1], niche, goal[2])
                from blog_html import daily_story
                body = daily_story(niche, goal[1], plat[1], plat_link)
                stamp = now()
                q_run(
                    "INSERT INTO blog (title, body, created_at, slug, tags, excerpt, published, cover) VALUES (?,?,?,?,?,?,1,?)",
                    (title, body, stamp, slug, tags, excerpt_text(body), first_img(body)),
                )
                used.append(key)
                save_settings({"blog_daily_used": json.dumps(used[-400:], ensure_ascii=False), "blog_last_pub": stamp})
                return 1
    if retry and used:
        save_settings({"blog_daily_used": "[]"})
        return generate_daily_post(False)
    return 0


def publish_next_blog():
    from cms import q_one, q_run
    from db import get_settings, now, save_settings

    seed_blog()
    last = str((get_settings() or {}).get("blog_last_pub") or "")
    if last:
        try:
            prev = datetime.strptime(last[:16], "%Y-%m-%d %H:%M")
            if datetime.now() - prev < timedelta(hours=20):
                return 0
        except Exception:
            pass
    row = q_one("SELECT * FROM blog WHERE published=0 ORDER BY id ASC LIMIT 1")
    stamp = now()
    if row:
        q_run("UPDATE blog SET published=1, created_at=? WHERE id=?", (stamp, row["id"]))
        save_settings({"blog_last_pub": stamp})
        return 1
    return generate_daily_post()
