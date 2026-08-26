from db import add_log, connect, now, save_settings, _hash


DEFAULTS = {
    "timezone": "Asia/Bangkok",
    "enable_transfer_funds": "1",
    "fundstransfer_fees": "0",
    "ticket_system": "1",
    "max_ticket": "5",
    "registration_page": "1",
    "resetpass": "1",
    "google_login": "1",
    "google_client_id": "",
    "google_client_secret": "",
    "auto_refill": "1",
    "service_list": "1",
    "mod_neworder": "1",
    "mod_dripfeed": "1",
    "mod_services": "1",
    "mod_orders": "1",
    "mod_subscription": "1",
    "mod_addfunds": "1",
    "mod_affiliate": "1",
    "mod_child": "1",
    "mod_tickets": "1",
    "mod_faq": "1",
    "mod_account": "1",
    "mod_api": "1",
    "mod_logout": "1",
    "mod_transfer": "1",
    "smtp_host": "",
    "smtp_user": "",
    "smtp_pass": "",
    "smtp_port": "587",
    "recaptcha_key": "",
    "admin_allow_ips": "",
    "analytics_id": "",
    "custom_header": "",
    "custom_footer": "",
    "usd_rate": "35",
    "profit_percent": "100",
    "alert_balance": "10",
    "truemoney": "",
    "pay_unique_satang": "1",
    "pay_merchant": "LIKES AUTO",
    "easyslip_key": "",
    "auto_approve_slip": "1",
    "oiio_slip_on": "1",
    "pay_notify_token": "",
    "max_deposit": "5000",
    "logo_url": "/static/assets/admin-crest.png",
    "theme_pack": "violet",
    "theme_switch": "1",
    "theme_violet_bg": "#070512",
    "theme_violet_text": "#f4f0ff",
    "theme_violet_muted": "#c9bddf",
    "theme_violet_accent": "#a855f7",
    "theme_violet_accent2": "#ec4899",
    "theme_violet_cyan": "#38bdf8",
    "theme_navy_bg": "#0a1220",
    "theme_navy_text": "#eef4ff",
    "theme_navy_muted": "#9eb0c9",
    "theme_navy_accent": "#3b82f6",
    "theme_navy_accent2": "#6366f1",
    "theme_navy_cyan": "#22d3ee",
    "theme_light_bg": "#f4f1fb",
    "theme_light_text": "#1e1233",
    "theme_light_muted": "#6b5d80",
    "theme_light_accent": "#7c3aed",
    "theme_light_accent2": "#db2777",
    "theme_light_cyan": "#0284c7",
}


def cms_migrate():
    con = connect()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE,
            title TEXT,
            body TEXT
        );
        CREATE TABLE IF NOT EXISTS blog (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT,
            created_at TEXT,
            slug TEXT,
            tags TEXT,
            excerpt TEXT,
            published INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY,
            label TEXT,
            href TEXT,
            sort INTEGER DEFAULT 0,
            visible INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY,
            min_amount REAL,
            percent REAL,
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY,
            name TEXT,
            path TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS guard_logs (
            id INTEGER PRIMARY KEY,
            username TEXT,
            ip TEXT,
            ok INTEGER,
            created_at TEXT
        );
        """
    )
    if cur.execute("SELECT COUNT(*) FROM pages").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO pages (slug, title, body) VALUES (?,?,?)",
            [
                ("faq", "คำถามที่พบบ่อย", "ดูหน้า FAQ ของเว็บ"),
                ("terms", "ข้อกำหนดการใช้งาน", "การใช้บริการถือว่ายอมรับเงื่อนไขของ LIKES AUTO"),
                ("privacy", "นโยบายความเป็นส่วนตัว", "เราเก็บเฉพาะข้อมูลที่จำเป็นต่อการให้บริการ"),
            ],
        )
    if cur.execute("SELECT COUNT(*) FROM menus").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO menus (label, href, sort, visible) VALUES (?,?,?,?)",
            [
                ("บริการ", "/services", 1, 1),
                ("วิธีใช้", "/#howto", 2, 1),
                ("API", "/api", 3, 1),
                ("บล็อก", "/blog", 4, 1),
                ("FAQ", "/faq", 5, 1),
            ],
        )
    if cur.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 0:
        cur.executemany("INSERT INTO subjects (name) VALUES (?)", [("สอบถามออเดอร์",), ("ปัญหาเติมเงิน",), ("อื่นๆ",)])
    from db import _has_col
    if not _has_col(cur, "blog", "slug"):
        cur.execute("ALTER TABLE blog ADD COLUMN slug TEXT")
    if not _has_col(cur, "blog", "tags"):
        cur.execute("ALTER TABLE blog ADD COLUMN tags TEXT")
    if not _has_col(cur, "blog", "excerpt"):
        cur.execute("ALTER TABLE blog ADD COLUMN excerpt TEXT")
    if not _has_col(cur, "blog", "published"):
        cur.execute("ALTER TABLE blog ADD COLUMN published INTEGER DEFAULT 1")
    if not _has_col(cur, "blog", "cover"):
        cur.execute("ALTER TABLE blog ADD COLUMN cover TEXT")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS blog_slug ON blog(slug) WHERE slug IS NOT NULL AND slug != ''")
    for k, v in DEFAULTS.items():
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    cur.execute(
        "UPDATE settings SET value=? WHERE key='logo_url' AND (value LIKE '%smmspot%' OR value='' OR value IS NULL)",
        (DEFAULTS["logo_url"],),
    )
    con.commit()
    con.close()
    try:
        from blog_content import seed_blog
        seed_blog()
    except Exception:
        pass


def q_all(sql, args=()):
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [dict(x) for x in items]


def q_one(sql, args=()):
    con = connect()
    row = con.execute(sql, args).fetchone()
    con.close()
    return dict(row) if row else None


def blog_media():
    from db import ROOT
    items = []
    seen = set()
    folders = [
        (ROOT / "static" / "uploads" / "blog", "/static/uploads/blog"),
        (ROOT / "static" / "assets" / "blog", "/static/assets/blog"),
    ]
    for folder, prefix in folders:
        if not folder.is_dir():
            continue
        files = sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files:
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                continue
            url = prefix + "/" + path.name
            if url in seen:
                continue
            seen.add(url)
            items.append(url)
    return items[:80]


def q_run(sql, args=()):
    con = connect()
    cur = con.execute(sql, args)
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid


def add_guard(username, ip, ok):
    q_run("INSERT INTO guard_logs (username, ip, ok, created_at) VALUES (?,?,?,?)", (username, ip, 1 if ok else 0, now()))


def apply_bonus(amount):
    row = q_one(
        "SELECT * FROM bonuses WHERE status='active' AND min_amount<=? ORDER BY min_amount DESC LIMIT 1",
        (float(amount),),
    )
    if not row:
        return 0
    return round(float(amount) * float(row["percent"]) / 100.0, 2)


def add_staff(username, password):
    from db import connect as c2
    con = c2()
    try:
        con.execute("INSERT INTO admins (username, password_hash) VALUES (?,?)", (username, _hash(password)))
        con.commit()
    except Exception:
        con.close()
        return False
    con.close()
    return True


def delete_staff(sid, current_username=""):
    from db import connect as c2
    con = c2()
    row = con.execute("SELECT * FROM admins WHERE id=?", (int(sid),)).fetchone()
    if not row:
        con.close()
        return False
    if str(row["username"]) == str(current_username or ""):
        con.close()
        return False
    total = con.execute("SELECT COUNT(*) c FROM admins").fetchone()["c"]
    if int(total) <= 1:
        con.close()
        return False
    con.execute("DELETE FROM admins WHERE id=?", (int(sid),))
    con.commit()
    con.close()
    return True
