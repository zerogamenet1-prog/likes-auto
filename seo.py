import json
import re
from datetime import datetime, timezone
from urllib.parse import urlencode

from content import COPY, FAQ, SITE

NOINDEX_PAGES = {
    "signin", "forgot", "reset", "neworder", "orders", "addfunds", "tickets",
    "account", "dripfeeds", "subscriptions", "affiliates", "panels", "notfound",
    "admin",
}
NOINDEX_PREFIX = ("/admin", "/internal")
PUBLIC_KEEP_QUERY = {"cat", "tag"}

DEFAULT_KEYWORDS = "ปั้มไลค์, ปั้มฟอล, ปั้มวิว, เพิ่มผู้ติดตาม, Instagram, TikTok, Facebook, YouTube, ยิงแอด, การตลาดออนไลน์, พร้อมเพย์, API"

META = {
    "home": (
        "ปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิว | Likes Auto",
        "ปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิว Instagram Facebook TikTok YouTube ส่งไว ไม่ใช้รหัสผ่าน ระบบอัตโนมัติ 24 ชม. เติมเงินพร้อมเพย์ได้ทันที",
    ),
    "services": (
        "ราคาปั้มไลค์ ปั้มฟอล เพิ่มวิว ทุกแพลตฟอร์ม | Likes Auto",
        "ดูราคาปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิว ทุกแพลตฟอร์ม เรทชัด ทดลองจำนวนน้อยได้ ไม่ขอรหัสผ่านโซเชียล",
    ),
    "faq": (
        "คำถามที่พบบ่อย ปั้มไลค์ ไม่ใช้รหัสผ่าน | Likes Auto",
        "คำตอบเรื่องการสั่งปั้มไลค์ เพิ่มฟอล เพิ่มวิว การเติมเงิน และความปลอดภัย ไม่ฝากรหัสผ่านโซเชียล",
    ),
    "terms": (
        "ข้อกำหนดการใช้งาน | Likes Auto",
        "ข้อกำหนดการใช้บริการปั้มไลค์ เพิ่มผู้ติดตาม และเพิ่มยอดวิวของ Likes Auto",
    ),
    "api": (
        "API ปั้มไลค์ สำหรับเปิดร้านต่อ | Likes Auto",
        "เชื่อม API ปั้มไลค์ เพิ่มฟอล เพิ่มวิว เพื่อเปิดร้านต่อ ใช้คีย์เดียวจัดการออเดอร์อัตโนมัติ",
    ),
    "blog": (
        "บทความปั้มไลค์ เพิ่มฟอล เพิ่มวิว | Likes Auto",
        "อ่านบทความวิธีใช้ปั้มไลค์ เพิ่มผู้ติดตาม และเพิ่มยอดวิวอย่างปลอดภัย จาก Likes Auto",
    ),
    "signup": (
        "สมัครฟรี ปั้มไลค์ เพิ่มฟอล เพิ่มวิว | Likes Auto",
        "สมัครใช้งาน Likes Auto ฟรี แล้วสั่งปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิวได้ทันที ไม่ขอรหัสผ่าน",
    ),
    "signin": (
        "เข้าสู่ระบบ | Likes Auto",
        "เข้าสู่ระบบ Likes Auto เพื่อสั่งซื้อ เติมเครดิต และติดตามออเดอร์",
    ),
    "page": (
        "Likes Auto",
        COPY.get("meta_desc") or "",
    ),
}


def site_url():
    return (SITE.get("url") or "https://likes-auto.com").rstrip("/")


def abs_url(path="/"):
    if path.startswith("http"):
        return path
    return site_url() + (path if path.startswith("/") else "/" + path)


def dumps_ld(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _plain(html, n=158):
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    if n and len(text) > n:
        return text[:n].rstrip() + "…"
    return text


def _title_desc(name, extra):
    extra = extra or {}
    if name == "blog" and extra.get("post"):
        post = extra["post"]
        title = (post.get("title") or "บทความ").strip() + " | Likes Auto"
        desc = (post.get("excerpt") or "").strip() or _plain(post.get("body") or "")
        if not desc:
            desc = META["blog"][1]
        return title, desc[:170]
    if name == "blog" and extra.get("tag"):
        tag = extra.get("tag")
        return (
            "บทความ %s ปั้มไลค์ ปั้มฟอล ปั้มวิว | Likes Auto" % tag,
            "อ่านบทความเรื่อง %s ปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิว และการตลาดออนไลน์ จาก Likes Auto" % tag,
        )
    if name == "page" and extra.get("item"):
        item = extra["item"]
        title = (item.get("title") or "หน้า").strip() + " | Likes Auto"
        body = (item.get("body") or "").replace("\n", " ").strip()
        desc = body[:158] if body else META["page"][1]
        return title, desc
    if name == "services" and extra.get("cat"):
        cat = str(extra.get("cat") or "").strip()
        return (
            "ปั้มไลค์ %s ราคา เพิ่มไลค์ ฟอล วิว | Likes Auto" % cat,
            "ดูราคาปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิว %s ส่งไว ไม่ใช้รหัสผ่าน สั่งจากแผง Likes Auto" % cat,
        )
    pair = META.get(name) or (COPY.get("meta_title"), COPY.get("meta_desc"))
    return pair[0], pair[1]


def canonical_for(request, name, extra):
    extra = extra or {}
    path = request.url.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    if name == "home":
        return abs_url("/")
    if name == "blog" and extra.get("post"):
        from blog_content import post_href
        return abs_url(post_href(extra["post"]))
    q = []
    if name == "services":
        cat = (extra.get("cat") or "").strip()
        if cat and not extra.get("q"):
            q.append(("cat", cat))
    if name == "blog":
        tag = (extra.get("tag") or "").strip()
        if tag:
            q.append(("tag", tag))
    if q:
        return abs_url(path) + "?" + urlencode(q)
    return abs_url(path)


def crumbs_for(name, extra, canonical):
    extra = extra or {}
    home = {"name": "หน้าแรก", "url": abs_url("/")}
    if name == "home":
        return [home]
    if name == "services":
        items = [home, {"name": "บริการ", "url": abs_url("/services")}]
        cat = (extra.get("cat") or "").strip()
        if cat:
            items.append({"name": cat, "url": canonical})
        return items
    if name == "faq":
        return [home, {"name": "คำถามที่พบบ่อย", "url": abs_url("/faq")}]
    if name == "terms":
        return [home, {"name": "ข้อกำหนด", "url": abs_url("/terms")}]
    if name == "api":
        return [home, {"name": "API", "url": abs_url("/api")}]
    if name == "blog" and extra.get("post"):
        return [home, {"name": "บล็อก", "url": abs_url("/blog")}, {"name": extra["post"].get("title") or "บทความ", "url": canonical}]
    if name == "blog" and extra.get("tag"):
        return [home, {"name": "บล็อก", "url": abs_url("/blog")}, {"name": extra.get("tag"), "url": canonical}]
    if name == "blog":
        return [home, {"name": "บล็อก", "url": abs_url("/blog")}]
    if name == "signup":
        return [home, {"name": "สมัครสมาชิก", "url": abs_url("/signup")}]
    if name == "page" and extra.get("item"):
        return [home, {"name": extra["item"].get("title") or "หน้า", "url": canonical}]
    return [home, {"name": COPY.get("meta_title") or "Likes Auto", "url": canonical}]


def should_index(request, name, extra):
    path = request.url.path or "/"
    if any(path.startswith(p) for p in NOINDEX_PREFIX):
        return False
    if name in NOINDEX_PAGES:
        return False
    if name == "services" and extra and extra.get("q"):
        return False
    return True


def json_ld(name, extra, title, desc, canonical, crumbs):
    extra = extra or {}
    org = {
        "@type": "Organization",
        "@id": abs_url("/#org"),
        "name": SITE.get("name") or "Likes Auto",
        "url": abs_url("/"),
        "logo": {
            "@type": "ImageObject",
            "url": abs_url("/static/assets/apple-touch.png"),
        },
        "description": COPY.get("meta_desc") or desc,
        "areaServed": "TH",
        "availableLanguage": "th",
    }
    website = {
        "@type": "WebSite",
        "@id": abs_url("/#website"),
        "url": abs_url("/"),
        "name": "Likes Auto",
        "inLanguage": "th",
        "publisher": {"@id": abs_url("/#org")},
        "potentialAction": {
            "@type": "SearchAction",
            "target": abs_url("/services") + "?q={search_term_string}",
            "query-input": "required name=search_term_string",
        },
    }
    crumbs_ld = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": c["name"], "item": c["url"]}
            for i, c in enumerate(crumbs)
        ],
    }
    graph = [org, website, crumbs_ld]
    if name in ("home", "faq") and FAQ:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in FAQ
            ],
        })
    if name == "home":
        graph.append({
            "@type": "Service",
            "name": "ปั้มไลค์ เพิ่มผู้ติดตาม เพิ่มยอดวิว",
            "provider": {"@id": abs_url("/#org")},
            "areaServed": "TH",
            "url": abs_url("/"),
            "description": desc,
        })
    if name == "blog" and extra.get("post"):
        post = extra["post"]
        tags = [t.strip() for t in (post.get("tags") or "").split(",") if t.strip()]
        graph.append({
            "@type": "Article",
            "headline": post.get("title") or title,
            "description": desc,
            "datePublished": post.get("created_at") or "",
            "inLanguage": "th",
            "keywords": ", ".join(tags) if tags else DEFAULT_KEYWORDS,
            "mainEntityOfPage": canonical,
            "author": {"@id": abs_url("/#org")},
            "publisher": {"@id": abs_url("/#org")},
            "image": abs_url((post.get("cover") or "").strip() or "/static/assets/og-cover.jpg"),
        })
    return dumps_ld({"@context": "https://schema.org", "@graph": graph})


def attach_seo(request, data):
    name = data.get("page") or ""
    extra = data
    title, desc = _title_desc(name, extra)
    canonical = canonical_for(request, name, extra)
    crumbs = crumbs_for(name, extra, canonical)
    indexable = should_index(request, name, extra)
    og_type = "article" if name == "blog" and extra.get("post") else "website"
    image = abs_url("/static/assets/og-cover.jpg")
    if extra.get("post"):
        cover = (extra["post"].get("cover") or "").strip()
        if cover:
            image = abs_url(cover)
    keywords = DEFAULT_KEYWORDS
    if extra.get("post") and extra["post"].get("tags"):
        keywords = extra["post"].get("tags")
    elif extra.get("tag"):
        keywords = extra.get("tag") + ", " + DEFAULT_KEYWORDS
    data["seo"] = {
        "title": title,
        "desc": desc,
        "canonical": canonical,
        "robots": "index, follow" if indexable else "noindex, nofollow",
        "indexable": indexable,
        "og_type": og_type,
        "og_image": image,
        "keywords": keywords,
        "crumbs": crumbs,
        "show_crumbs": name not in ("home", "signin", "signup", "notfound") and not data.get("dash_mode"),
        "json_ld": json_ld(name, extra, title, desc, canonical, crumbs) if indexable else "",
        "published": (extra.get("post") or {}).get("created_at") if extra.get("post") else "",
    }
    return data


def sitemap_xml(pages):
    now = datetime.now(timezone.utc).date().isoformat()
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for item in pages:
        loc = item["loc"]
        last = item.get("lastmod") or now
        freq = item.get("changefreq") or "weekly"
        pri = item.get("priority") or "0.6"
        chunks.append(
            "<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>"
            % (_xml(loc), _xml(last), freq, pri)
        )
    chunks.append("</urlset>")
    return "\n".join(chunks)


def robots_txt():
    base = site_url()
    return "\n".join([
        "User-agent: *",
        "Allow: /",
        "Allow: /services",
        "Allow: /faq",
        "Allow: /blog",
        "Allow: /api",
        "Allow: /terms",
        "Allow: /signup",
        "Disallow: /admin",
        "Disallow: /internal",
        "Disallow: /addfunds",
        "Disallow: /orders",
        "Disallow: /neworder",
        "Disallow: /account",
        "Disallow: /tickets",
        "Disallow: /signin",
        "Disallow: /forgot",
        "Disallow: /reset",
        "Disallow: /dripfeeds",
        "Disallow: /subscriptions",
        "Disallow: /affiliates",
        "Disallow: /panels",
        "",
        "Sitemap: %s/sitemap.xml" % base,
        "",
    ])


def rss_xml(posts):
    from blog_content import excerpt_text, post_href
    base = site_url()
    items = []
    for post in posts or []:
        link = base + post_href(post)
        items.append("".join([
            "<item>",
            "<title>%s</title>" % _xml(post.get("title") or ""),
            "<link>%s</link>" % _xml(link),
            "<guid>%s</guid>" % _xml(link),
            "<pubDate>%s</pubDate>" % _xml(post.get("created_at") or ""),
            "<description>%s</description>" % _xml(post.get("excerpt") or excerpt_text(post.get("body") or "", 240)),
            "</item>",
        ]))
    return "".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0"><channel>',
        "<title>Likes Auto Blog</title>",
        "<link>%s/blog</link>" % base,
        "<description>บทความปั้มไลค์ เพิ่มฟอล เพิ่มวิว</description>",
        "<language>th</language>",
        "".join(items),
        "</channel></rss>",
    ])


def _xml(text):
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
