import hashlib
import hmac
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

from th_shop import search_aliases, shop_card, shop_explain, th_label, th_text


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "app.db"
_settings_lock = threading.Lock()
_settings_cache = {"t": 0.0, "data": None}


def _hash(password: str) -> str:
    salt = os.environ.get("ADMIN_SALT", "likes-auto-py")
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _hash_eq(stored, password: str) -> bool:
    got = _hash(password)
    saved = str(stored or "")
    dummy = _hash("timing-dummy")
    if len(saved) != len(got):
        hmac.compare_digest(dummy, got)
        return False
    return hmac.compare_digest(saved, got)


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA temp_store=MEMORY")
    except sqlite3.Error:
        pass
    return con


def init_db():
    con = connect()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            username TEXT,
            email TEXT,
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY,
            platform TEXT,
            name TEXT,
            rate REAL DEFAULT 0,
            min_qty INTEGER DEFAULT 10,
            max_qty INTEGER DEFAULT 10000,
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            client TEXT,
            service TEXT,
            link TEXT,
            quantity INTEGER,
            charge REAL,
            status TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            client TEXT,
            method TEXT,
            amount REAL,
            status TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY,
            client TEXT,
            subject TEXT,
            status TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            action TEXT,
            ip TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    if cur.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
        user = os.environ.get("ADMIN_USER", "admin")
        pw = os.environ.get("ADMIN_PASS", "ChangeMe#2026")
        cur.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            (user, _hash(pw)),
        )
    # Demo services are seeded at most once. Never re-insert after admin deletes them.
    demo = cur.execute("SELECT value FROM settings WHERE key='demo_seeded'").fetchone()
    if not demo:
        if cur.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
            if str(os.environ.get("ALLOW_DEMO_SEED", "0")).strip() in {"1", "true", "yes"}:
                cur.executemany(
                    "INSERT INTO services (platform, name, rate, min_qty, max_qty, status) VALUES (?,?,?,?,?,?)",
                    [
                        ("Instagram", "ไลค์รูป", 8, 10, 10000, "active"),
                        ("Instagram", "เพิ่มผู้ติดตาม", 25, 10, 5000, "active"),
                        ("Facebook", "ไลค์เพจ", 12, 10, 20000, "active"),
                        ("TikTok", "วิวคลิป", 5, 100, 100000, "active"),
                        ("YouTube", "วิว", 18, 100, 50000, "active"),
                        ("LINE OA", "เพิ่มเพื่อน", 30, 10, 3000, "active"),
                    ],
                )
        cur.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES('demo_seeded', '1')"
        )
    if cur.execute("SELECT COUNT(*) FROM settings").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            [
                ("site_name", "LIKES AUTO"),
                ("currency", "THB"),
                ("support_email", "support@likes-auto.com"),
            ],
        )
    con.commit()
    con.close()
    migrate()
    provider_migrate()
    from store import extra_migrate
    extra_migrate()
    from cms import cms_migrate
    cms_migrate()


def check_admin(username: str, password: str) -> bool:
    con = connect()
    row = con.execute(
        "SELECT password_hash FROM admins WHERE username=?", (username,)
    ).fetchone()
    con.close()
    stored = row["password_hash"] if row else None
    return bool(row) and _hash_eq(stored, password)


def stats():
    con = connect()
    data = {
        "clients": con.execute("SELECT COUNT(*) c FROM clients").fetchone()["c"],
        "orders": con.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"],
        "services": con.execute("SELECT COUNT(*) c FROM services").fetchone()["c"],
        "tickets": con.execute("SELECT COUNT(*) c FROM tickets WHERE status='open'").fetchone()["c"],
        "revenue": con.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='paid'").fetchone()["s"],
    }
    con.close()
    return data


_PUBLIC_STATS = {"t": 0.0, "data": None}
_PUBLIC_STATS_TTL = 30.0


def public_stats():
    """Homepage display counts — boosted for social proof; admin keeps real stats()."""
    now = time.monotonic()
    hit = _PUBLIC_STATS["data"]
    if hit is not None and (now - _PUBLIC_STATS["t"]) < _PUBLIC_STATS_TTL:
        return dict(hit)
    s = stats()
    orders = int(s.get("orders") or 0)
    clients = int(s.get("clients") or 0)
    services = int(s.get("services") or 0)
    out = {
        "orders": 28467 + orders * 37,
        "clients": 9684 + clients * 19,
        "services": services,
        "tickets": s.get("tickets") or 0,
        "revenue": s.get("revenue") or 0,
    }
    _PUBLIC_STATS["t"] = now
    _PUBLIC_STATS["data"] = out
    return dict(out)


def dashboard_series(days=14):
    from datetime import datetime, timedelta
    days = max(7, min(int(days or 14), 30))
    start = datetime.now() - timedelta(days=days - 1)
    con = connect()
    rows_data = con.execute(
        """
        SELECT substr(created_at,1,10) d, COUNT(*) c, COALESCE(SUM(charge),0) s
        FROM orders
        WHERE created_at >= ?
        GROUP BY substr(created_at,1,10)
        """,
        (start.strftime("%Y-%m-%d"),),
    ).fetchall()
    con.close()
    by = {x["d"]: x for x in rows_data}
    labels, orders, revenue = [], [], []
    for i in range(days):
        day = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])
        row = by.get(day)
        orders.append(int(row["c"]) if row else 0)
        revenue.append(round(float(row["s"]) if row else 0, 2))
    return {"labels": labels, "orders": orders, "revenue": revenue}


def rows(table: str, limit: int = 200):
    allowed = {"clients", "orders", "services", "payments", "tickets", "logs"}
    if table not in allowed:
        return []
    con = connect()
    items = con.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [dict(x) for x in items]


MOD_KEYS = [
    "mod_neworder",
    "mod_dripfeed",
    "mod_services",
    "mod_orders",
    "mod_subscription",
    "mod_addfunds",
    "mod_affiliate",
    "mod_child",
    "mod_tickets",
    "mod_faq",
    "mod_account",
    "mod_api",
    "mod_logout",
    "mod_transfer",
]


def get_settings():
    now = time.monotonic()
    with _settings_lock:
        cached = _settings_cache["data"]
        if cached is not None and (now - _settings_cache["t"]) < 8:
            return dict(cached)
    con = connect()
    items = con.execute("SELECT key, value FROM settings").fetchall()
    con.close()
    data = {x["key"]: x["value"] for x in items}
    with _settings_lock:
        _settings_cache["t"] = time.monotonic()
        _settings_cache["data"] = data
    return dict(data)


def mod_on(settings=None, key=""):
    s = settings if settings is not None else get_settings()
    return str(s.get(key, "1")) != "0"


def mods_map(settings=None):
    s = settings if settings is not None else get_settings()
    return {k: str(s.get(k, "1")) != "0" for k in MOD_KEYS}


def first_open_path(settings=None):
    s = settings if settings is not None else get_settings()
    for key, path in (
        ("mod_neworder", "/neworder"),
        ("mod_services", "/services"),
        ("mod_orders", "/orders"),
        ("mod_addfunds", "/addfunds"),
        ("mod_account", "/account"),
        ("mod_faq", "/faq"),
    ):
        if str(s.get(key, "1")) != "0":
            return path
    return "/"


def save_settings(values: dict):
    con = connect()
    for k, v in values.items():
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
    con.commit()
    con.close()
    with _settings_lock:
        _settings_cache["data"] = None
    if any(k in values for k in ("profit_percent", "usd_rate")):
        shop_cache_clear()


def add_log(action: str, ip: str):
    con = connect()
    con.execute(
        "INSERT INTO logs (action, ip, created_at) VALUES (?,?,?)",
        (action, ip, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    con.commit()
    con.close()

def _has_col(cur, table, col):
    return any(r[1] == col for r in cur.execute("PRAGMA table_info(%s)" % table))


def migrate():
    con = connect()
    cur = con.cursor()
    for table, col, spec in (
        ("clients", "password_hash", "TEXT"),
        ("clients", "api_key", "TEXT"),
        ("tickets", "message", "TEXT"),
        ("clients", "google_id", "TEXT"),
    ):
        if _has_col(cur, table, col):
            continue
        try:
            cur.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, spec))
        except sqlite3.OperationalError as ex:
            # Parallel gunicorn workers may race on first boot.
            if "duplicate column" not in str(ex).lower():
                raise
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS clients_google_id ON clients(google_id) WHERE google_id IS NOT NULL AND google_id != ''")
    con.commit()
    con.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def get_client(username=None, client_id=None, email=None):
    con = connect()
    row = None
    if client_id:
        row = con.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    elif username:
        row = con.execute("SELECT * FROM clients WHERE username=?", (username,)).fetchone()
    elif email:
        row = con.execute("SELECT * FROM clients WHERE email=? COLLATE NOCASE", (email,)).fetchone()
    con.close()
    return dict(row) if row else None


def create_client(username, email, password, referred_by=None):
    if get_client(username=username):
        return None, "ชื่อผู้ใช้นี้ถูกใช้แล้ว"
    con = connect()
    if con.execute("SELECT id FROM clients WHERE email=?", (email,)).fetchone():
        con.close()
        return None, "อีเมลนี้ถูกใช้แล้ว"
    key = os.urandom(12).hex()
    ref = (username or "u")[:12]
    referrer = None
    if referred_by:
        other = con.execute("SELECT username FROM clients WHERE ref_code=? OR username=?", (referred_by, referred_by)).fetchone()
        if other and other["username"] != username:
            referrer = other["username"]
    cur = con.execute(
        "INSERT INTO clients (username,email,balance,status,created_at,password_hash,api_key,ref_code,referred_by,ref_earn) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (username, email, 0, "active", now(), _hash(password), key, ref, referrer, 0),
    )
    con.commit()
    cid = cur.lastrowid
    con.close()
    return get_client(client_id=cid), None


def check_client(username, password):
    row = get_client(username=username)
    stored = (row or {}).get("password_hash") or ""
    if not _hash_eq(stored, password):
        return None
    if not row or row.get("status") != "active":
        return None
    return row


def list_services():
    con = connect()
    items = con.execute(
        """
        SELECT s.*, c.rate AS catalog_rate, c.currency AS catalog_currency,
               c.type AS catalog_type, c.refill AS catalog_refill, c.name AS catalog_name
        FROM services s
        LEFT JOIN provider_catalog c
          ON c.provider_id = s.provider_id AND c.api_service = s.api_service
        WHERE s.status='active'
        ORDER BY s.platform, IFNULL(s.category,''), s.name, s.id
        """
    ).fetchall()
    con.close()
    return [attach_live_rate(dict(x)) for x in items]


def plat_logo(name):
    n = (name or "").lower().strip()
    if n in {"x", "twitter / x", "twitter"}:
        return "/static/assets/plats/x.svg"
    if n == "line" or n.startswith("line ") or "line oa" in n:
        return "/static/assets/plats/line.svg"
    pairs = (
        ("instagram", "instagram"),
        ("facebook", "facebook"),
        ("tiktok", "tiktok"),
        ("youtube", "youtube"),
        ("twitter", "x"),
        ("telegram", "telegram"),
        ("spotify", "spotify"),
        ("twitch", "twitch"),
        ("whatsapp", "whatsapp"),
        ("shopee", "shopee"),
        ("reddit", "reddit"),
        ("pinterest", "pinterest"),
        ("soundcloud", "soundcloud"),
        ("discord", "discord"),
        ("threads", "threads"),
        ("linkedin", "linkedin"),
        ("snapchat", "snapchat"),
        ("lazada", "lazada"),
        ("google", "google"),
        ("website", "website"),
        ("seo", "website"),
        ("traffic", "website"),
    )
    for key, slug in pairs:
        if key in n:
            return "/static/assets/plats/%s.svg" % slug
    return "/static/assets/plats/app.svg"


def plat_meta(name):
    n = (name or "").lower()
    pairs = (
        ("instagram", "ri-instagram-line", "#e1306c"),
        ("facebook", "ri-facebook-circle-fill", "#1877f2"),
        ("tiktok", "ri-tiktok-fill", "#ffffff"),
        ("youtube", "ri-youtube-fill", "#ff0000"),
        ("twitter", "ri-twitter-x-fill", "#ffffff"),
        ("line", "ri-line-fill", "#06c755"),
        ("telegram", "ri-telegram-fill", "#2aabee"),
        ("shopee", "ri-shopping-bag-3-line", "#ee4d2d"),
        ("lazada", "ri-store-2-line", "#0f146d"),
        ("google", "ri-google-fill", "#4285f4"),
        ("threads", "ri-threads-line", "#ffffff"),
        ("spotify", "ri-spotify-fill", "#1db954"),
        ("discord", "ri-discord-fill", "#5865f2"),
        ("seo", "ri-line-chart-line", "#22d3ee"),
        ("traffic", "ri-global-line", "#67e8f9"),
    )
    for key, icon, color in pairs:
        if key in n:
            return icon, color
    if n.strip() in {"x", "twitter / x"}:
        return "ri-twitter-x-fill", "#ffffff"
    return "ri-apps-2-line", "#c4b5fd"


_SHOP_NAV = {"t": 0, "platforms": [], "categories": []}
_SHOP_NAV_TTL = 90
_PRICE = {"t": 0.0, "usd": 35.0, "pct": 100.0}
_PREFERRED_PLATS = ("facebook", "instagram", "tiktok", "youtube", "telegram", "twitter", "line", "threads", "spotify", "seo")


def shop_cache_clear():
    _SHOP_NAV["t"] = 0
    _PRICE["t"] = 0.0
    _SHOP_NAV["platforms"] = []
    _SHOP_NAV["categories"] = []
    _PUBLIC_STATS["t"] = 0.0
    _PUBLIC_STATS["data"] = None


def _cat_label(value):
    text = (value or "").strip()
    return text or "ทั่วไป"


def _plat_rank_legacy(name):
    low = (name or "").lower()
    for i, key in enumerate(_PREFERRED_PLATS):
        if key in low:
            return i
    return 80


def _plat_rank(name):
    try:
        con = connect()
        row = con.execute(
            "SELECT sort_order FROM shop_sort WHERE kind='main' AND name=? LIMIT 1",
            (_norm_plat(name),),
        ).fetchone()
        con.close()
        if row is not None:
            return int(row["sort_order"])
    except Exception:
        pass
    return _plat_rank_legacy(name)


def _shop_order_map(kind, platform=""):
    con = connect()
    if kind == "main":
        rows = con.execute(
            "SELECT name, sort_order FROM shop_sort WHERE kind='main' ORDER BY sort_order, name"
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT name, sort_order FROM shop_sort WHERE kind='sub' AND platform=? ORDER BY sort_order, name",
            (platform or "",),
        ).fetchall()
    con.close()
    return {r["name"]: int(r["sort_order"]) for r in rows}


def _norm_plat(value):
    return (value or "").strip() or "อื่น ๆ"


def _norm_cat(value):
    return (value or "").strip() or "ทั่วไป"


def sync_shop_sort():
    """Ensure every live platform/category has a sort row."""
    con = connect()
    try:
        plats = [
            _norm_plat(r["platform"])
            for r in con.execute("SELECT DISTINCT platform FROM services").fetchall()
        ]
        plats = sorted(set(plats), key=lambda n: (_plat_rank_legacy(n), n.lower()))
        existing = {
            r["name"]: int(r["sort_order"])
            for r in con.execute("SELECT name, sort_order FROM shop_sort WHERE kind='main'").fetchall()
        }
        next_ord = max(existing.values()) + 10 if existing else 10
        for name in plats:
            if name in existing:
                continue
            con.execute(
                "INSERT OR IGNORE INTO shop_sort(kind, platform, name, sort_order) VALUES('main','',?,?)",
                (name, next_ord),
            )
            existing[name] = next_ord
            next_ord += 10

        cat_rows = con.execute(
            "SELECT platform, category FROM services GROUP BY platform, category"
        ).fetchall()
        by_plat = {}
        for row in cat_rows:
            plat = _norm_plat(row["platform"])
            cat = _norm_cat(row["category"])
            by_plat.setdefault(plat, set()).add(cat)
        for plat, cats in by_plat.items():
            existing_sub = {
                r["name"]: int(r["sort_order"])
                for r in con.execute(
                    "SELECT name, sort_order FROM shop_sort WHERE kind='sub' AND platform=?",
                    (plat,),
                ).fetchall()
            }
            next_sub = max(existing_sub.values()) + 10 if existing_sub else 10
            for cat in sorted(cats, key=lambda n: n.lower()):
                if cat in existing_sub:
                    continue
                con.execute(
                    "INSERT OR IGNORE INTO shop_sort(kind, platform, name, sort_order) VALUES('sub',?,?,?)",
                    (plat, cat, next_sub),
                )
                existing_sub[cat] = next_sub
                next_sub += 10
        con.commit()
    finally:
        con.close()


def list_shop_mains():
    sync_shop_sort()
    blocked = blocked_shop_mains()
    con = connect()
    counts = {
        _norm_plat(r["platform"]): int(r["c"])
        for r in con.execute(
            "SELECT platform, COUNT(*) c FROM services GROUP BY platform"
        ).fetchall()
    }
    rows = con.execute(
        "SELECT name, sort_order FROM shop_sort WHERE kind='main' ORDER BY sort_order, name"
    ).fetchall()
    con.close()
    items = []
    for r in rows:
        name = r["name"]
        if name in blocked:
            continue
        items.append({
            "name": name,
            "count": int(counts.get(name) or 0),
            "sort_order": int(r["sort_order"]),
        })
    return items


def list_shop_subs(platform):
    plat = _norm_plat(platform)
    if not plat:
        return []
    if plat in blocked_shop_mains():
        return []
    sync_shop_sort()
    blocked = blocked_shop_subs()
    con = connect()
    counts = {
        _norm_cat(r["category"]): int(r["c"])
        for r in con.execute(
            "SELECT category, COUNT(*) c FROM services WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=? GROUP BY category",
            (plat,),
        ).fetchall()
    }
    rows = con.execute(
        "SELECT name, sort_order FROM shop_sort WHERE kind='sub' AND platform=? ORDER BY sort_order, name",
        (plat,),
    ).fetchall()
    con.close()
    items = []
    for r in rows:
        name = r["name"]
        if ("%s|%s" % (plat, name)) in blocked:
            continue
        items.append({
            "name": name,
            "count": int(counts.get(name) or 0),
            "sort_order": int(r["sort_order"]),
        })
    return items


def add_shop_main(name):
    name = _norm_plat(name)
    if not name:
        return False
    sync_shop_sort()
    con = connect()
    exists = con.execute(
        "SELECT id FROM shop_sort WHERE kind='main' AND name=?", (name,)
    ).fetchone()
    if exists:
        con.close()
        unblock_shop_main(name)
        return True
    row = con.execute(
        "SELECT MAX(sort_order) m FROM shop_sort WHERE kind='main'"
    ).fetchone()
    nxt = int(row["m"] or 0) + 10
    con.execute(
        "INSERT INTO shop_sort(kind, platform, name, sort_order) VALUES('main','',?,?)",
        (name, nxt),
    )
    con.commit()
    con.close()
    unblock_shop_main(name)
    shop_cache_clear()
    return True


def add_shop_sub(platform, name):
    plat = _norm_plat(platform)
    name = _norm_cat(name)
    if not plat or not name:
        return False
    add_shop_main(plat)
    con = connect()
    exists = con.execute(
        "SELECT id FROM shop_sort WHERE kind='sub' AND platform=? AND name=?",
        (plat, name),
    ).fetchone()
    if exists:
        con.close()
        unblock_shop_sub(plat, name)
        return True
    row = con.execute(
        "SELECT MAX(sort_order) m FROM shop_sort WHERE kind='sub' AND platform=?",
        (plat,),
    ).fetchone()
    nxt = int(row["m"] or 0) + 10
    con.execute(
        "INSERT INTO shop_sort(kind, platform, name, sort_order) VALUES('sub',?,?,?)",
        (plat, name, nxt),
    )
    con.commit()
    con.close()
    unblock_shop_sub(plat, name)
    shop_cache_clear()
    return True


def _block_list(key):
    import json
    raw = (get_settings().get(key) or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data if str(x).strip()]
    except Exception:
        pass
    return [x.strip() for x in raw.split("\n") if x.strip()]


def _save_block_list(key, items):
    import json
    uniq = []
    seen = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        uniq.append(text)
    save_settings({key: json.dumps(uniq, ensure_ascii=False)})


def blocked_shop_mains():
    return set(_block_list("shop_blocked_mains"))


def blocked_shop_subs():
    return set(_block_list("shop_blocked_subs"))


def block_shop_main(name):
    name = _norm_plat(name)
    items = _block_list("shop_blocked_mains")
    if name not in items:
        items.append(name)
    _save_block_list("shop_blocked_mains", items)
    # drop blocked subs under this main
    prefix = name + "|"
    subs = [x for x in _block_list("shop_blocked_subs") if not x.startswith(prefix)]
    _save_block_list("shop_blocked_subs", subs)


def unblock_shop_main(name):
    name = _norm_plat(name)
    items = [x for x in _block_list("shop_blocked_mains") if x != name]
    _save_block_list("shop_blocked_mains", items)


def block_shop_sub(platform, name):
    plat = _norm_plat(platform)
    name = _norm_cat(name)
    key = "%s|%s" % (plat, name)
    items = _block_list("shop_blocked_subs")
    if key not in items:
        items.append(key)
    _save_block_list("shop_blocked_subs", items)


def unblock_shop_sub(platform, name):
    plat = _norm_plat(platform)
    name = _norm_cat(name)
    key = "%s|%s" % (plat, name)
    items = [x for x in _block_list("shop_blocked_subs") if x != key]
    _save_block_list("shop_blocked_subs", items)


def shop_item_blocked(platform, category=""):
    plat = _norm_plat(platform)
    if plat in blocked_shop_mains():
        return True
    cat = _norm_cat(category)
    return ("%s|%s" % (plat, cat)) in blocked_shop_subs()


def set_shop_manual_lock(on=True):
    save_settings({"shop_manual_lock": "1" if on else "0"})


def shop_manual_locked():
    return str(get_settings().get("shop_manual_lock") or "0") == "1"


def clear_shop_blocks():
    _save_block_list("shop_blocked_mains", [])
    _save_block_list("shop_blocked_subs", [])
    set_shop_manual_lock(False)


def delete_shop_main(name):
    name = _norm_plat(name)
    if not name:
        return 0
    con = connect()
    cur = con.execute(
        "DELETE FROM services WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=?",
        (name,),
    )
    n = cur.rowcount if cur.rowcount is not None else 0
    con.execute("DELETE FROM shop_sort WHERE kind='main' AND name=?", (name,))
    con.execute("DELETE FROM shop_sort WHERE kind='sub' AND platform=?", (name,))
    con.commit()
    con.close()
    block_shop_main(name)
    set_shop_manual_lock(True)
    shop_cache_clear()
    return int(n)


def delete_shop_sub(platform, name):
    plat = _norm_plat(platform)
    name = _norm_cat(name)
    if not plat or not name:
        return 0
    con = connect()
    cur = con.execute(
        """
        DELETE FROM services
        WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=?
          AND IFNULL(NULLIF(TRIM(category),''),'ทั่วไป')=?
        """,
        (plat, name),
    )
    n = cur.rowcount if cur.rowcount is not None else 0
    con.execute(
        "DELETE FROM shop_sort WHERE kind='sub' AND platform=? AND name=?",
        (plat, name),
    )
    con.commit()
    con.close()
    block_shop_sub(plat, name)
    set_shop_manual_lock(True)
    shop_cache_clear()
    return int(n)


def delete_all_shop_mains():
    con = connect()
    cur = con.execute("DELETE FROM services")
    n = cur.rowcount if cur.rowcount is not None else 0
    con.execute("DELETE FROM shop_sort")
    con.commit()
    con.close()
    _save_block_list("shop_blocked_mains", [])
    _save_block_list("shop_blocked_subs", [])
    set_shop_manual_lock(True)
    shop_cache_clear()
    return int(n)


def delete_all_shop_subs(platform):
    plat = _norm_plat(platform)
    if not plat:
        return 0
    con = connect()
    cur = con.execute(
        "DELETE FROM services WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=?",
        (plat,),
    )
    n = cur.rowcount if cur.rowcount is not None else 0
    con.execute("DELETE FROM shop_sort WHERE kind='sub' AND platform=?", (plat,))
    con.commit()
    con.close()
    block_shop_main(plat)
    set_shop_manual_lock(True)
    shop_cache_clear()
    return int(n)

def rename_shop_main(old_name, new_name):
    old = _norm_plat(old_name)
    new = _norm_plat(new_name)
    if not old or not new or old == new:
        return False
    con = connect()
    taken = con.execute(
        "SELECT 1 FROM services WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=? LIMIT 1",
        (new,),
    ).fetchone()
    if taken and old != new:
        # merging into existing name is allowed
        pass
    con.execute(
        "UPDATE services SET platform=? WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=?",
        (new, old),
    )
    row = con.execute(
        "SELECT id, sort_order FROM shop_sort WHERE kind='main' AND name=?", (old,)
    ).fetchone()
    dest = con.execute(
        "SELECT id FROM shop_sort WHERE kind='main' AND name=?", (new,)
    ).fetchone()
    if row and dest and row["id"] != dest["id"]:
        con.execute("DELETE FROM shop_sort WHERE id=?", (row["id"],))
    elif row:
        con.execute("UPDATE shop_sort SET name=? WHERE id=?", (new, row["id"]))
    elif not dest:
        con.execute(
            "INSERT INTO shop_sort(kind, platform, name, sort_order) VALUES('main','',?,1000)",
            (new,),
        )
    con.execute("UPDATE shop_sort SET platform=? WHERE kind='sub' AND platform=?", (new, old))
    con.commit()
    con.close()
    shop_cache_clear()
    return True


def rename_shop_sub(platform, old_name, new_name):
    plat = _norm_plat(platform)
    old = _norm_cat(old_name)
    new = _norm_cat(new_name)
    if not plat or not old or not new or old == new:
        return False
    con = connect()
    con.execute(
        """
        UPDATE services SET category=?
        WHERE IFNULL(NULLIF(TRIM(platform),''),'อื่น ๆ')=?
          AND IFNULL(NULLIF(TRIM(category),''),'ทั่วไป')=?
        """,
        (new, plat, old),
    )
    row = con.execute(
        "SELECT id FROM shop_sort WHERE kind='sub' AND platform=? AND name=?",
        (plat, old),
    ).fetchone()
    dest = con.execute(
        "SELECT id FROM shop_sort WHERE kind='sub' AND platform=? AND name=?",
        (plat, new),
    ).fetchone()
    if row and dest and row["id"] != dest["id"]:
        con.execute("DELETE FROM shop_sort WHERE id=?", (row["id"],))
    elif row:
        con.execute("UPDATE shop_sort SET name=? WHERE id=?", (new, row["id"]))
    elif not dest:
        con.execute(
            "INSERT INTO shop_sort(kind, platform, name, sort_order) VALUES('sub',?,?,1000)",
            (plat, new),
        )
    con.commit()
    con.close()
    shop_cache_clear()
    return True


def move_shop_sort(kind, name, direction, platform=""):
    kind = "main" if kind == "main" else "sub"
    name = _norm_plat(name) if kind == "main" else _norm_cat(name)
    plat = _norm_plat(platform) if kind == "sub" else ""
    direction = -1 if int(direction or 0) < 0 else 1
    sync_shop_sort()
    con = connect()
    if kind == "main":
        rows = con.execute(
            "SELECT id, name, sort_order FROM shop_sort WHERE kind='main' ORDER BY sort_order, name"
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT id, name, sort_order FROM shop_sort WHERE kind='sub' AND platform=? ORDER BY sort_order, name",
            (plat,),
        ).fetchall()
    idx = next((i for i, r in enumerate(rows) if r["name"] == name), -1)
    if idx < 0:
        con.close()
        return False
    j = idx + direction
    if j < 0 or j >= len(rows):
        con.close()
        return False
    a, b = rows[idx], rows[j]
    con.execute("UPDATE shop_sort SET sort_order=? WHERE id=?", (b["sort_order"], a["id"]))
    con.execute("UPDATE shop_sort SET sort_order=? WHERE id=?", (a["sort_order"], b["id"]))
    # if equal, force unique order
    if a["sort_order"] == b["sort_order"]:
        con.execute("UPDATE shop_sort SET sort_order=? WHERE id=?", (a["sort_order"] + direction, a["id"]))
    con.commit()
    con.close()
    shop_cache_clear()
    return True


def reorder_shop_sort(kind, names, platform=""):
    """Persist an explicit order list (drag-and-drop)."""
    kind = "main" if kind == "main" else "sub"
    plat = _norm_plat(platform) if kind == "sub" else ""
    cleaned = []
    seen = set()
    for raw in names or []:
        name = _norm_plat(raw) if kind == "main" else _norm_cat(raw)
        if not name or name in seen:
            continue
        seen.add(name)
        cleaned.append(name)
    if not cleaned:
        return False
    sync_shop_sort()
    con = connect()
    if kind == "main":
        existing = {
            r["name"]: r["id"]
            for r in con.execute("SELECT id, name FROM shop_sort WHERE kind='main'").fetchall()
        }
    else:
        existing = {
            r["name"]: r["id"]
            for r in con.execute(
                "SELECT id, name FROM shop_sort WHERE kind='sub' AND platform=?",
                (plat,),
            ).fetchall()
        }
    order = 10
    for name in cleaned:
        sid = existing.get(name)
        if sid:
            con.execute("UPDATE shop_sort SET sort_order=? WHERE id=?", (order, sid))
        elif kind == "main":
            con.execute(
                "INSERT INTO shop_sort(kind, platform, name, sort_order) VALUES('main','',?,?)",
                (name, order),
            )
        else:
            con.execute(
                "INSERT INTO shop_sort(kind, platform, name, sort_order) VALUES('sub',?,?,?)",
                (plat, name, order),
            )
        order += 10
    # push any leftover names after the dragged set
    for name, sid in existing.items():
        if name in seen:
            continue
        con.execute("UPDATE shop_sort SET sort_order=? WHERE id=?", (order, sid))
        order += 10
    con.commit()
    con.close()
    shop_cache_clear()
    return True


def _shop_cat_sql(alias="s"):
    return (
        "CASE WHEN TRIM(IFNULL(%s.category,''))!='' THEN TRIM(%s.category) "
        "WHEN TRIM(IFNULL(c.category,''))!='' THEN TRIM(c.category) "
        "ELSE 'ทั่วไป' END" % (alias, alias)
    )


def shop_nav():
    now = time.monotonic()
    if _SHOP_NAV["platforms"] and now - _SHOP_NAV["t"] < _SHOP_NAV_TTL:
        return {"platforms": _SHOP_NAV["platforms"], "categories": _SHOP_NAV["categories"]}
    try:
        sync_shop_sort()
    except Exception:
        pass
    cat_sql = _shop_cat_sql("s")
    con = connect()
    plats = con.execute(
        "SELECT platform AS name, COUNT(*) AS count FROM services WHERE status='active' GROUP BY platform"
    ).fetchall()
    cats = con.execute(
        """
        SELECT s.platform, %s AS category, COUNT(*) AS count
        FROM services s
        LEFT JOIN provider_catalog c
          ON c.provider_id = s.provider_id AND c.api_service = s.api_service
        WHERE s.status='active'
        GROUP BY s.platform, %s
        """ % (cat_sql, cat_sql)
    ).fetchall()
    con.close()
    platforms = []
    for row in plats:
        name = (row["name"] or "อื่น ๆ").strip() or "อื่น ๆ"
        icon, color = plat_meta(name)
        platforms.append({
            "name": name,
            "count": int(row["count"] or 0),
            "icon": icon,
            "color": color,
            "logo": plat_logo(name),
        })
    platforms.sort(key=lambda x: (_plat_rank(x["name"]), x["name"].lower()))
    categories = []
    for row in cats:
        plat = (row["platform"] or "อื่น ๆ").strip() or "อื่น ๆ"
        cat = _cat_label(row["category"])
        icon, color = plat_meta(plat)
        label = th_label(plat, cat)
        categories.append({
            "platform": plat,
            "category": cat,
            "label": label,
            "count": int(row["count"] or 0),
            "icon": icon,
            "color": color,
            "featured": 0,
            "logo": plat_logo(plat),
        })
    featured = set()
    def _pin_kind(cat):
        text = (cat or "").lower()
        return any(key in text for key in ("like", "follow", "view", "subscriber", "ไลค์", "ผู้ติดตาม", "วิว"))
    for item in categories:
        plat = item["platform"]
        if plat in featured or _plat_rank_legacy(plat) > 5:
            continue
        if not _pin_kind(item["category"]):
            continue
        item["label"] = th_label(plat, item["category"], featured=True)
        item["featured"] = 1
        featured.add(plat)
    for item in categories:
        plat = item["platform"]
        if plat in featured or _plat_rank_legacy(plat) > 5:
            continue
        item["label"] = th_label(plat, item["category"], featured=True)
        item["featured"] = 1
        featured.add(plat)
    sub_maps = {}
    def _sub_rank(plat, cat):
        if plat not in sub_maps:
            try:
                sub_maps[plat] = _shop_order_map("sub", plat)
            except Exception:
                sub_maps[plat] = {}
        return sub_maps[plat].get(cat, 9000)
    categories.sort(key=lambda x: (
        _plat_rank(x["platform"]),
        _sub_rank(x["platform"], x["category"]),
        0 if x.get("featured") else 1,
        x["label"].lower(),
    ))
    _SHOP_NAV["t"] = now
    _SHOP_NAV["platforms"] = platforms
    _SHOP_NAV["categories"] = categories
    return {"platforms": platforms, "categories": categories}


def shop_services(platform="", category="", q="", limit=80, offset=0, sid=""):
    limit = max(1, min(int(limit or 80), 120))
    offset = max(0, int(offset or 0))
    plat = (platform or "").strip()
    cat = _cat_label(category) if category else ""
    needle = (q or "").strip()
    needles = search_aliases(needle) if needle else []
    cat_sql = _shop_cat_sql("s")
    if sid and not plat:
        try:
            sid_n = int(sid)
        except (TypeError, ValueError):
            sid_n = 0
        if sid_n:
            con = connect()
            found = con.execute(
                """
                SELECT s.platform, %s AS category
                FROM services s
                LEFT JOIN provider_catalog c
                  ON c.provider_id = s.provider_id AND c.api_service = s.api_service
                WHERE s.id=?
                """ % cat_sql,
                (sid_n,),
            ).fetchone()
            con.close()
            if found:
                plat = (found["platform"] or "").strip()
                cat = _cat_label(found["category"])
    sql = """
        SELECT s.id, s.platform, %s AS category, s.name, s.rate, s.min_qty, s.max_qty,
               s.cost_rate, s.currency, c.rate AS catalog_rate, c.currency AS catalog_currency,
               c.name AS catalog_name, c.refill AS catalog_refill, c.type AS catalog_type
        FROM services s
        LEFT JOIN provider_catalog c
          ON c.provider_id = s.provider_id AND c.api_service = s.api_service
        WHERE s.status='active'
    """ % cat_sql
    args = []
    if plat:
        sql += " AND s.platform=?"
        args.append(plat)
    if cat:
        sql += " AND %s=?" % cat_sql
        args.append(cat)
    if needles:
        bits = []
        for term in needles:
            like = "%" + term + "%"
            bits.append("(s.name LIKE ? OR CAST(s.id AS TEXT) LIKE ? OR IFNULL(s.category,'') LIKE ? OR IFNULL(c.category,'') LIKE ? OR s.platform LIKE ?)")
            args.extend([like, like, like, like, like])
        sql += " AND (" + " OR ".join(bits) + ")"
    sql += " ORDER BY s.rate ASC, s.id LIMIT ? OFFSET ?"
    args.extend([limit, offset])
    con = connect()
    rows = con.execute(sql, args).fetchall()
    con.close()
    out = []
    for row in rows:
        item = dict(row)
        item = attach_live_rate(item)
        plat_name = item.get("platform") or ""
        name = item.get("name") or ""
        item["name"] = th_text(name)
        item["category_th"] = th_text(item.get("category") or "")
        short = item["name"].split(" · ", 1)[0].strip() or item["name"]
        if "[" in short:
            short = short.split("[", 1)[0].strip()
        if len(short) > 48:
            short = short[:46].rstrip() + "…"
        item["name_short"] = short
        card = shop_card(item)
        item["title"] = card["title"]
        item["bits"] = card["bits"]
        item["line"] = card["line"]
        item["recommend"] = card["recommend"]
        item["notes"] = shop_explain(item)
        item["logo"] = plat_logo(plat_name)
        icon, color = plat_meta(plat_name)
        item["icon"] = icon
        item["color"] = color
        from service_fields import order_fields

        fields = order_fields(item)
        item["needs_link"] = fields["needs_link"]
        item["needs_comments"] = fields["needs_comments"]
        item["sync_qty_comments"] = fields["sync_qty_comments"]
        if fields["needs_comments"]:
            item["desc"] = "บริการ%sบน %s · กรอกลิงก์โพสต์และคอมเมนต์ (แยกแต่ละบรรทัด)" % (
                ((" " + item["category_th"]) if item["category_th"] else " "),
                plat_name,
            )
        elif fields["needs_link"]:
            item["desc"] = "บริการ%sบน %s · ใช้ลิงก์สาธารณะเท่านั้น ไม่ขอรหัสผ่าน" % (
                ((" " + item["category_th"]) if item["category_th"] else " "),
                plat_name,
            )
        else:
            item["desc"] = "บริการ%sบน %s" % (
                ((" " + item["category_th"]) if item["category_th"] else " "),
                plat_name,
            )
        out.append(item)
    if out:
        cheap = min(out, key=lambda row: float(row.get("rate") or 999999))
        bits = list(cheap.get("bits") or [])
        if "💎 ราคาถูก" not in bits:
            bits.append("💎 ราคาถูก")
        if "⚡ แนะนำ" not in bits:
            bits.append("⚡ แนะนำ")
        cheap["bits"] = bits
        cheap["line"] = " | ".join(bits)
        cheap["recommend"] = True
    return out


def shop_groups(items=None):
    if items is None:
        nav = shop_nav()
        return [], nav["platforms"]
    slim = []
    groups = {}
    for row in items:
        plat = (row.get("platform") or "อื่น ๆ").strip() or "อื่น ๆ"
        item = {
            "id": row.get("id"),
            "platform": plat,
            "category": _cat_label(row.get("category")),
            "name": row.get("name") or "",
            "rate": row.get("rate") or 0,
            "min_qty": row.get("min_qty") or 1,
            "max_qty": row.get("max_qty") or 100000,
        }
        slim.append(item)
        groups.setdefault(plat, []).append(item)
    ranked = []
    for key, val in groups.items():
        icon, color = plat_meta(key)
        ranked.append({
            "name": key,
            "count": len(val),
            "icon": icon,
            "color": color,
            "logo": plat_logo(key),
        })
    ranked.sort(key=lambda x: (_plat_rank(x["name"]), -x["count"], x["name"].lower()))
    return slim, ranked


_SYNC_DEAD_WORDS = (
    "not working",
    "disabled",
    "do not order",
    "dont order",
    "don't order",
    "out of stock",
    "service closed",
    "temporary off",
    "temp off",
)


def _catalog_row_dead(name="", category=""):
    text = ("%s %s" % (name or "", category or "")).lower()
    return any(word in text for word in _SYNC_DEAD_WORDS)


def sync_listed_from_catalog(provider_id):
    """Keep listed shop rows aligned with upstream catalog: price, qty, status."""
    pid = int(provider_id)
    cfg = price_cfg(True)
    con = connect()
    rows = con.execute(
        """
        SELECT api_service, name, category, rate, min_qty, max_qty, IFNULL(currency,'USD') AS currency
        FROM provider_catalog WHERE provider_id=?
        """,
        (pid,),
    ).fetchall()
    live_set = set()
    good_ids = []
    dead_ids = []
    payload = []
    for row in rows:
        api_sid = str(row["api_service"] or "")
        if not api_sid:
            continue
        live_set.add(api_sid)
        cur = row["currency"] or "USD"
        try:
            cost = float(row["rate"] or 0)
        except (TypeError, ValueError):
            cost = 0.0
        sell = sell_thb(cost, cur, cfg["usd"], cfg["pct"], 0)
        try:
            min_qty = int(row["min_qty"] or 1)
        except (TypeError, ValueError):
            min_qty = 1
        try:
            max_qty = int(row["max_qty"] or 100000)
        except (TypeError, ValueError):
            max_qty = 100000
        dead = _catalog_row_dead(row["name"], row["category"]) or cost <= 0
        if dead:
            dead_ids.append(api_sid)
            status = "inactive"
        else:
            good_ids.append(api_sid)
            status = "active"
        payload.append((
            cost,
            cur,
            min_qty,
            max_qty,
            sell,
            str(row["category"] or ""),
            status,
            pid,
            api_sid,
        ))
    listed = 0
    if payload:
        con.executemany(
            """
            UPDATE services
            SET cost_rate=?, currency=?, min_qty=?, max_qty=?, rate=?,
                category=CASE WHEN IFNULL(TRIM(category),'')='' THEN ? ELSE category END,
                status=?
            WHERE provider_id=? AND api_service=?
            """,
            payload,
        )
        listed = con.execute(
            "SELECT COUNT(*) FROM services WHERE provider_id=? AND IFNULL(api_service,'')!=''",
            (pid,),
        ).fetchone()[0] or 0

    removed = 0
    shop_apis = [
        str(r["api_service"])
        for r in con.execute(
            "SELECT api_service FROM services WHERE provider_id=? AND IFNULL(api_service,'')!=''",
            (pid,),
        )
    ]
    missing = [sid for sid in shop_apis if sid not in live_set]
    chunk = 400
    for i in range(0, len(missing), chunk):
        part = missing[i:i + chunk]
        marks = ",".join("?" * len(part))
        cur = con.execute(
            "UPDATE services SET status='inactive' WHERE provider_id=? AND api_service IN (%s)" % marks,
            [pid] + part,
        )
        removed += int(cur.rowcount or 0)

    con.commit()
    active_n = con.execute(
        "SELECT COUNT(*) FROM services WHERE provider_id=? AND status='active' AND IFNULL(api_service,'')!=''",
        (pid,),
    ).fetchone()[0] or 0
    inactive_n = con.execute(
        "SELECT COUNT(*) FROM services WHERE provider_id=? AND status!='active' AND IFNULL(api_service,'')!=''",
        (pid,),
    ).fetchone()[0] or 0
    con.close()
    shop_cache_clear()
    return {
        "catalog": len(rows),
        "listed": int(listed),
        "active": int(active_n),
        "inactive": int(inactive_n),
        "dead_marked": len(dead_ids),
        "removed": int(removed),
    }


def client_dash(username):
    con = connect()
    row = con.execute(
        """
        SELECT COUNT(*) AS n,
               COALESCE(SUM(CASE WHEN IFNULL(status,'') NOT IN ('canceled','cancelled') THEN charge ELSE 0 END), 0) AS spent
        FROM orders WHERE client=?
        """,
        (username,),
    ).fetchone()
    con.close()
    return {"orders": int(row["n"] or 0), "spent": float(row["spent"] or 0)}


def get_service(sid):
    con = connect()
    row = con.execute(
        """
        SELECT s.*, c.rate AS catalog_rate, c.currency AS catalog_currency,
               c.type AS catalog_type, c.refill AS catalog_refill, c.name AS catalog_name
        FROM services s
        LEFT JOIN provider_catalog c
          ON c.provider_id = s.provider_id AND c.api_service = s.api_service
        WHERE s.id=?
        """,
        (sid,),
    ).fetchone()
    con.close()
    return attach_live_rate(dict(row)) if row else None


def get_order(oid):
    con = connect()
    row = con.execute("SELECT * FROM orders WHERE id=?", (int(oid),)).fetchone()
    con.close()
    return dict(row) if row else None


def calc_charge(rate, qty):
    return round((float(rate) * int(qty)) / 1000.0, 2)


def create_order(client, service_id, link, quantity, comments=None):
    from service_fields import count_comment_lines, normalize_comments, order_fields

    svc = get_service(service_id)
    if not svc:
        return None, "ไม่พบบริการ"
    fields = order_fields(svc)
    link = (link or "").strip()
    comments = normalize_comments(comments)
    if fields["needs_link"] and not link:
        return None, "กรุณากรอกลิงก์"
    if fields["needs_comments"]:
        if not comments:
            return None, "กรุณากรอกคอมเมนต์ (แยกแต่ละบรรทัด)"
        qty = count_comment_lines(comments)
        if qty < 1:
            return None, "กรุณากรอกคอมเมนต์อย่างน้อย 1 บรรทัด"
    else:
        qty = int(quantity)
    if qty < svc["min_qty"] or qty > svc["max_qty"]:
        return None, "จำนวนไม่อยู่ในช่วงที่กำหนด"
    charge = calc_charge(svc["rate"], qty)
    user = get_client(username=client)
    if not user:
        return None, "ไม่พบบัญชี"
    if float(user["balance"] or 0) < charge:
        return None, "ยอดเงินไม่พอ กรุณาเติมเงิน"
    con = connect()
    con.execute("UPDATE clients SET balance = balance - ? WHERE username=?", (charge, client))
    cur = con.execute(
        "INSERT INTO orders (client,service,link,quantity,charge,status,created_at,provider_id,service_id,comments) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (client, "%s %s" % (svc["platform"], svc["name"]), link, qty, charge, "pending", now(), svc.get("provider_id"), svc.get("id"), comments or None),
    )
    con.commit()
    oid = cur.lastrowid
    con.close()
    add_log("สั่งซื้อ #%s" % oid, "-")
    return oid, None


def client_orders(username):
    con = connect()
    items = con.execute("SELECT * FROM orders WHERE client=? ORDER BY id DESC", (username,)).fetchall()
    con.close()
    return [dict(x) for x in items]


def create_payment(client, method, amount, method_id=None):
    from pay import infer_kind, make_ref_code, method_row, unique_amount
    amt = float(amount)
    min_amt = 20.0
    settings = get_settings()
    try:
        min_amt = float(settings.get("min_deposit") or 20)
    except (TypeError, ValueError):
        min_amt = 20.0
    if amt < min_amt:
        return None, "ยอดเติมขั้นต่ำ %.0f บาท" % min_amt
    try:
        max_amt = float(settings.get("max_deposit") or 5000)
    except (TypeError, ValueError):
        max_amt = 5000.0
    if amt > max_amt:
        return None, "ยอดเติมสูงสุด %.0f บาท" % max_amt
    row = method_row(method_id, method)
    if not row or (row.get("status") or "active") != "active":
        return None, "ช่องทางนี้ปิดใช้งาน"
    kind = infer_kind(row.get("name"), row.get("kind"))
    name = row.get("name") or method
    con = connect()
    cur = con.execute(
        "INSERT INTO payments (client,method,amount,status,created_at,method_id,kind,ref_code) VALUES (?,?,?,?,?,?,?,?)",
        (client, name, amt, "pending", now(), row.get("id"), kind, make_ref_code()),
    )
    pid = cur.lastrowid
    exact = unique_amount(amt, pid)
    con.execute("UPDATE payments SET amount=? WHERE id=?", (exact, pid))
    ref = "LA%06d" % int(pid)
    con.execute("UPDATE payments SET ref_code=? WHERE id=? AND (ref_code IS NULL OR ref_code='')", (ref, pid))
    # keep generated ref; only fill if empty
    con.commit()
    con.close()
    return pid, None


def client_payments(username):
    con = connect()
    items = con.execute("SELECT * FROM payments WHERE client=? ORDER BY id DESC", (username,)).fetchall()
    con.close()
    return [dict(x) for x in items]


def approve_payment(pid):
    con = connect()
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        if not row or row["status"] != "pending":
            con.execute("ROLLBACK")
            con.close()
            return False
        cur = con.execute(
            "UPDATE payments SET status='paid' WHERE id=? AND status='pending'",
            (pid,),
        )
        if cur.rowcount != 1:
            con.execute("ROLLBACK")
            con.close()
            return False
        con.execute(
            "UPDATE clients SET balance = balance + ? WHERE username=?",
            (row["amount"], row["client"]),
        )
        con.commit()
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        con.close()
        return False
    con.close()
    add_log("อนุมัติเติมเงิน #%s" % pid, "-")
    try:
        from cms import apply_bonus
        bonus = apply_bonus(row["amount"])
        if bonus:
            con2 = connect()
            con2.execute("UPDATE clients SET balance = balance + ? WHERE username=?", (bonus, row["client"]))
            con2.commit()
            con2.close()
            add_log("โบนัสเติมเงิน %s ให้ %s" % (bonus, row["client"]), "-")
        from store import credit_affiliate
        credit_affiliate(row["client"], row["amount"])
    except Exception:
        pass
    return True


def reject_payment(pid, note=""):
    con = connect()
    row = con.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not row or row["status"] != "pending":
        con.close()
        return False
    if note:
        con.execute("UPDATE payments SET status='canceled', note=? WHERE id=?", (note.strip(), pid))
    else:
        con.execute("UPDATE payments SET status='canceled' WHERE id=?", (pid,))
    con.commit()
    con.close()
    add_log("ปฏิเสธเติมเงิน #%s" % pid, "-")
    return True


def create_ticket(client, subject, message):
    con = connect()
    cur = con.execute(
        "INSERT INTO tickets (client,subject,status,created_at,message) VALUES (?,?,?,?,?)",
        (client, subject, "open", now(), message),
    )
    con.commit()
    tid = cur.lastrowid
    con.close()
    return tid


def client_tickets(username):
    con = connect()
    items = con.execute("SELECT * FROM tickets WHERE client=? ORDER BY id DESC", (username,)).fetchall()
    con.close()
    return [dict(x) for x in items]

def provider_migrate():
    con = connect()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            api_url TEXT,
            api_key TEXT,
            balance TEXT DEFAULT '-',
            currency TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cron_logs (
            id INTEGER PRIMARY KEY,
            job TEXT,
            detail TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS provider_catalog (
            id INTEGER PRIMARY KEY,
            provider_id INTEGER,
            api_service TEXT,
            category TEXT,
            name TEXT,
            rate REAL,
            min_qty INTEGER,
            max_qty INTEGER,
            type TEXT,
            currency TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shop_sort (
            id INTEGER PRIMARY KEY,
            kind TEXT NOT NULL,
            platform TEXT NOT NULL DEFAULT '',
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 1000,
            UNIQUE(kind, platform, name)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catalog_provider ON provider_catalog(provider_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_svc_status_plat ON services(status, platform)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_catalog_api ON provider_catalog(provider_id, api_service)")
    for table, col, spec in [
        ("services", "provider_id", "INTEGER"),
        ("services", "api_service", "TEXT"),
        ("services", "cost_rate", "REAL"),
        ("services", "category", "TEXT"),
        ("services", "currency", "TEXT"),
        ("provider_catalog", "main_cat", "TEXT"),
        ("provider_catalog", "refill", "TEXT"),
        ("orders", "service_id", "INTEGER"),
        ("orders", "provider_id", "INTEGER"),
        ("orders", "api_orderid", "TEXT"),
        ("orders", "api_error", "TEXT"),
        ("orders", "start_count", "TEXT"),
        ("orders", "remains", "TEXT"),
        ("orders", "refunded", "INTEGER"),
        ("orders", "comments", "TEXT"),
    ]:
        if not _has_col(cur, table, col):
            cur.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, spec))
    if _has_col(cur, "services", "category"):
        cur.execute("CREATE INDEX IF NOT EXISTS idx_svc_status_cat ON services(status, platform, category)")
    if _has_col(cur, "services", "provider_id") and _has_col(cur, "services", "api_service"):
        cur.execute("CREATE INDEX IF NOT EXISTS idx_svc_provider_api ON services(provider_id, api_service)")
    con.commit()
    con.close()


def list_providers():
    con = connect()
    items = con.execute("SELECT id, name, api_url, balance, currency, created_at FROM providers ORDER BY id DESC").fetchall()
    con.close()
    return [dict(x) for x in items]


def get_provider(pid):
    con = connect()
    row = con.execute("SELECT * FROM providers WHERE id=?", (pid,)).fetchone()
    con.close()
    return dict(row) if row else None


def add_provider(name, api_url, api_key):
    con = connect()
    cur = con.execute(
        "INSERT INTO providers (name, api_url, api_key, created_at) VALUES (?,?,?,?)",
        (name, api_url.strip(), api_key.strip(), now()),
    )
    con.commit()
    pid = cur.lastrowid
    con.close()
    return pid


def save_provider(pid, name, api_url, api_key):
    name = (name or "").strip()
    api_url = (api_url or "").strip()
    api_key = (api_key or "").strip()
    if not name or not api_url:
        return None
    if not pid:
        if not api_key:
            return None
        return add_provider(name, api_url, api_key)
    old = get_provider(int(pid))
    if not old:
        return add_provider(name, api_url, api_key) if api_key else None
    key = api_key or old.get("api_key") or ""
    con = connect()
    con.execute(
        "UPDATE providers SET name=?, api_url=?, api_key=? WHERE id=?",
        (name, api_url, key, int(pid)),
    )
    con.commit()
    con.close()
    return int(pid)


def delete_provider(pid):
    con = connect()
    con.execute("DELETE FROM providers WHERE id=?", (pid,))
    con.commit()
    con.close()


def save_provider_balance(pid, balance, currency):
    con = connect()
    con.execute("UPDATE providers SET balance=?, currency=? WHERE id=?", (str(balance), currency, pid))
    con.commit()
    con.close()


MAIN_CATS = [
    "Instagram", "TikTok", "YouTube", "Facebook", "Twitter / X", "Telegram",
    "Spotify", "Discord", "Twitch", "LinkedIn", "Threads", "Snapchat",
    "Pinterest", "LINE", "WhatsApp", "SoundCloud", "Reddit", "Shopee",
    "Lazada", "Google", "Website",
]
MAIN_ALIASES = [
    ("Instagram", ("instagram",)),
    ("TikTok", ("tiktok", "tik tok")),
    ("YouTube", ("youtube",)),
    ("Facebook", ("facebook",)),
    ("Twitter / X", ("twitter", "tweet")),
    ("Telegram", ("telegram",)),
    ("Spotify", ("spotify",)),
    ("Discord", ("discord",)),
    ("Twitch", ("twitch",)),
    ("LinkedIn", ("linkedin",)),
    ("Threads", ("threads",)),
    ("Snapchat", ("snapchat",)),
    ("Pinterest", ("pinterest",)),
    ("LINE", ("line oa",)),
    ("WhatsApp", ("whatsapp",)),
    ("SoundCloud", ("soundcloud",)),
    ("Reddit", ("reddit",)),
    ("Shopee", ("shopee",)),
    ("Lazada", ("lazada",)),
    ("Google", ("google",)),
    ("Website", ("website", "traffic", "seo")),
]


def split_category(raw):
    text = str(raw or "").strip() or "อื่น ๆ"
    low = text.lower()
    for main, aliases in MAIN_ALIASES:
        for alias in aliases:
            if low.startswith(alias):
                rest = text[len(alias):].lstrip(" -|/:")
                return main, rest
    for main, aliases in MAIN_ALIASES:
        for alias in aliases:
            if alias.strip() and alias.strip() in low:
                return main, text
    return "อื่น ๆ", text


def money(value):
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount >= 1:
        return round(amount + 1e-9, 2)
    return round(amount + 1e-12, 4)


def norm_currency(currency, default="USD"):
    cur = str(currency or "").strip().upper().replace(" ", "").replace("฿", "THB")
    if cur in {"THB", "BAHT", "BATH"}:
        return "THB"
    if cur in {"USD", "US$", "$", "DOLLAR", "DOLLARS"}:
        return "USD"
    if cur:
        return cur
    return str(default or "USD").strip().upper() or "USD"


def is_thb_currency(currency):
    return norm_currency(currency, "USD") == "THB"


def to_thb(amount, currency, usd_rate=35):
    try:
        raw = float(amount or 0)
    except (TypeError, ValueError):
        raw = 0.0
    try:
        usd = float(usd_rate or 35)
    except (TypeError, ValueError):
        usd = 35.0
    cur = norm_currency(currency, "USD")
    if cur == "THB":
        return money(raw)
    usd_each = {
        "USD": 1.0, "US$": 1.0, "$": 1.0,
        "EUR": 1.08, "GBP": 1.27, "AUD": 0.65, "CAD": 0.73, "SGD": 0.74,
        "INR": 0.012, "TRY": 0.029, "RUB": 0.011, "IDR": 0.000063,
        "VND": 0.00004, "PHP": 0.017, "MYR": 0.22, "BRL": 0.18,
    }.get(cur, 1.0)
    return money(raw * usd_each * usd)


def sell_thb(amount, currency, usd_rate=35, percent=0, fixed=0):
    cost = to_thb(amount, currency, usd_rate)
    try:
        pct = float(percent or 0)
    except (TypeError, ValueError):
        pct = 0.0
    try:
        extra = float(fixed or 0)
    except (TypeError, ValueError):
        extra = 0.0
    return money(cost * (1 + pct / 100.0) + extra)


def price_cfg(force=False):
    now = time.monotonic()
    if not force and _PRICE["t"] and now - _PRICE["t"] < 8:
        return _PRICE
    settings = get_settings()
    try:
        _PRICE["usd"] = float(settings.get("usd_rate") or 35)
    except (TypeError, ValueError):
        _PRICE["usd"] = 35.0
    raw = settings.get("profit_percent")
    if raw in (None, ""):
        raw = 100
    try:
        _PRICE["pct"] = float(raw)
    except (TypeError, ValueError):
        _PRICE["pct"] = 100.0
    _PRICE["t"] = now
    return _PRICE


def attach_live_rate(svc):
    if not svc:
        return svc
    cfg = price_cfg()
    cost = svc.get("catalog_rate")
    cur = svc.get("catalog_currency") or svc.get("currency") or "USD"
    if cost is None:
        cost = svc.get("cost_rate")
    if cost is None:
        return svc
    try:
        cost = float(cost)
    except (TypeError, ValueError):
        return svc
    svc["cost_rate"] = cost
    svc["currency"] = cur
    svc["rate"] = sell_thb(cost, cur, cfg["usd"], cfg["pct"], 0)
    return svc


def import_provider_service(provider_id, platform, name, rate, min_qty, max_qty, api_service, cost_rate=None, category=None, currency=None):
    rows = [{
        "platform": platform,
        "name": name,
        "rate": rate,
        "min_qty": min_qty,
        "max_qty": max_qty,
        "api_service": api_service,
        "cost_rate": cost_rate,
        "category": category,
        "currency": currency,
    }]
    return import_shop_rows(provider_id, rows)


def import_shop_rows(provider_id, rows):
    """Bulk upsert shop services in one DB transaction (faster / safer for large imports)."""
    if not rows:
        return 0
    pid = int(provider_id)
    con = connect()
    existing = {
        str(r["api_service"]): {
            "id": int(r["id"]),
            "platform": (r["platform"] or "").strip(),
            "category": (r["category"] or "").strip(),
        }
        for r in con.execute(
            "SELECT id, api_service, platform, category FROM services WHERE provider_id=? AND IFNULL(api_service,'')!=''",
            (pid,),
        )
    }
    count = 0
    for row in rows:
        api_sid = str(row.get("api_service") or "")
        if not api_sid:
            continue
        cost = row.get("cost_rate")
        cost = None if cost is None else float(cost)
        cat = (row.get("category") or "").strip()
        cur = (row.get("currency") or "USD").strip() or "USD"
        platform = (row.get("platform") or "อื่น ๆ").strip() or "อื่น ๆ"
        name = str(row.get("name") or ("Service %s" % api_sid))[:180]
        try:
            rate = float(row.get("rate") or 0)
        except (TypeError, ValueError):
            rate = 0.0
        try:
            min_qty = int(row.get("min_qty") or 1)
        except (TypeError, ValueError):
            min_qty = 1
        try:
            max_qty = int(row.get("max_qty") or 100000)
        except (TypeError, ValueError):
            max_qty = 100000
        old = existing.get(api_sid)
        if old:
            con.execute(
                "UPDATE services SET platform=?, name=?, rate=?, min_qty=?, max_qty=?, cost_rate=?, category=?, currency=?, status='active' WHERE id=?",
                (
                    old["platform"] or platform,
                    name,
                    rate,
                    min_qty,
                    max_qty,
                    cost,
                    old["category"] or cat,
                    cur,
                    old["id"],
                ),
            )
        else:
            cur_ins = con.execute(
                "INSERT INTO services (platform, name, rate, min_qty, max_qty, status, provider_id, api_service, cost_rate, category, currency) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (platform, name, rate, min_qty, max_qty, "active", pid, api_sid, cost, cat, cur),
            )
            existing[api_sid] = {
                "id": int(cur_ins.lastrowid),
                "platform": platform,
                "category": cat,
            }
        count += 1
    con.commit()
    con.close()
    shop_cache_clear()
    return count


def import_provider_services(provider_id, items):
    if isinstance(items, dict):
        items = items.get("services") or []
    if not isinstance(items, list):
        return 0
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        api_sid = item.get("service")
        if api_sid is None:
            continue
        cat = str(item.get("category") or "อื่น ๆ").strip() or "อื่น ๆ"
        platform = cat[:80]
        name = str(item.get("name") or ("Service %s" % api_sid))[:180]
        import_provider_service(
            provider_id,
            platform,
            name,
            item.get("rate") or 0,
            item.get("min") or 1,
            item.get("max") or 100000,
            api_sid,
            item.get("rate") or 0,
            cat,
        )
        count += 1
    return count


def replace_provider_catalog(provider_id, items, currency):
    rows = []
    fallback = norm_currency(currency, "USD")
    for item in items:
        if not isinstance(item, dict):
            continue
        api_sid = item.get("service")
        if api_sid is None:
            continue
        try:
            rate = float(item.get("rate") or 0)
        except (TypeError, ValueError):
            rate = 0.0
        try:
            min_qty = int(float(item.get("min") or 1))
        except (TypeError, ValueError):
            min_qty = 1
        try:
            max_qty = int(float(item.get("max") or 100000))
        except (TypeError, ValueError):
            max_qty = 100000
        cat = str(item.get("category") or "อื่น ๆ").strip()[:120] or "อื่น ๆ"
        main, _sub = split_category(cat)
        refill = item.get("refill")
        if isinstance(refill, bool):
            refill = "1" if refill else "0"
        else:
            refill = "1" if str(refill or "").lower() in {"1", "true", "yes"} else "0"
        row_cur = norm_currency(item.get("currency") or item.get("Currency") or fallback, fallback)
        rows.append((
            int(provider_id),
            str(api_sid),
            cat,
            main,
            str(item.get("name") or ("Service %s" % api_sid))[:180],
            rate,
            min_qty,
            max_qty,
            str(item.get("type") or "Default")[:40],
            row_cur,
            refill,
        ))
    con = connect()
    con.execute("DELETE FROM provider_catalog WHERE provider_id=?", (int(provider_id),))
    con.executemany(
        "INSERT INTO provider_catalog (provider_id, api_service, category, main_cat, name, rate, min_qty, max_qty, type, currency, refill) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    con.close()
    return len(rows)


def catalog_count(provider_id, q="", category="", main="", stype=""):
    sql = "SELECT COUNT(*) c FROM provider_catalog WHERE provider_id=?"
    args = [int(provider_id)]
    sql, args = _catalog_filters(sql, args, q, category, main, stype)
    con = connect()
    row = con.execute(sql, args).fetchone()
    con.close()
    return int(row["c"] if row else 0)


def _catalog_filters(sql, args, q, category, main="", stype=""):
    if main:
        sql += " AND main_cat=?"
        args.append(main)
    if category:
        sql += " AND category=?"
        args.append(category)
    if stype:
        sql += " AND IFNULL(type,'')=?"
        args.append(stype)
    if q:
        like = "%" + q.strip() + "%"
        sql += " AND (name LIKE ? OR api_service LIKE ? OR category LIKE ? OR IFNULL(type,'') LIKE ?)"
        args.extend([like, like, like, like])
    return sql, args


def list_provider_catalog(provider_id, q="", category="", limit=80, offset=0, main="", stype=""):
    sql = "SELECT * FROM provider_catalog WHERE provider_id=?"
    args = [int(provider_id)]
    sql, args = _catalog_filters(sql, args, q, category, main, stype)
    sql += " ORDER BY category, name LIMIT ? OFFSET ?"
    args.extend([int(limit), int(offset)])
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [dict(x) for x in items]


def catalog_types(provider_id, category="", main=""):
    sql = "SELECT IFNULL(type,'Default') AS type, COUNT(*) c FROM provider_catalog WHERE provider_id=?"
    args = [int(provider_id)]
    if main:
        sql += " AND main_cat=?"
        args.append(main)
    if category:
        sql += " AND category=?"
        args.append(category)
    sql += " GROUP BY IFNULL(type,'Default') ORDER BY c DESC, type"
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [{"name": x["type"] or "Default", "count": x["c"]} for x in items]


def catalog_categories(provider_id, main=""):
    sql = "SELECT category, COUNT(*) c FROM provider_catalog WHERE provider_id=?"
    args = [int(provider_id)]
    if main:
        sql += " AND main_cat=?"
        args.append(main)
    sql += " GROUP BY category ORDER BY category"
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [{"name": x["category"], "count": x["c"]} for x in items]


def catalog_mains(provider_id):
    con = connect()
    blank = con.execute(
        "SELECT COUNT(*) c FROM provider_catalog WHERE provider_id=? AND IFNULL(main_cat,'')=''",
        (int(provider_id),),
    ).fetchone()["c"]
    if blank:
        rows = con.execute(
            "SELECT id, category FROM provider_catalog WHERE provider_id=? AND IFNULL(main_cat,'')=''",
            (int(provider_id),),
        ).fetchall()
        for row in rows:
            main, _sub = split_category(row["category"])
            con.execute("UPDATE provider_catalog SET main_cat=? WHERE id=?", (main, row["id"]))
        con.commit()
    items = con.execute(
        "SELECT main_cat, COUNT(*) c FROM provider_catalog WHERE provider_id=? GROUP BY main_cat ORDER BY c DESC, main_cat",
        (int(provider_id),),
    ).fetchall()
    con.close()
    return [{"name": x["main_cat"] or "อื่น ๆ", "count": x["c"]} for x in items]


def catalog_by_ids(provider_id, api_ids):
    ids = [str(x) for x in api_ids if str(x)]
    if not ids:
        return []
    q = ",".join("?" * len(ids))
    con = connect()
    items = con.execute(
        "SELECT * FROM provider_catalog WHERE provider_id=? AND api_service IN (%s)" % q,
        [int(provider_id)] + ids,
    ).fetchall()
    con.close()
    return [dict(x) for x in items]


def catalog_all_filtered(provider_id, q="", category="", main="", stype=""):
    sql = "SELECT * FROM provider_catalog WHERE provider_id=?"
    args = [int(provider_id)]
    sql, args = _catalog_filters(sql, args, q, category, main, stype)
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [dict(x) for x in items]


def imported_api_ids(provider_id):
    con = connect()
    items = con.execute(
        "SELECT api_service FROM services WHERE provider_id=? AND api_service IS NOT NULL AND api_service!=''",
        (int(provider_id),),
    ).fetchall()
    con.close()
    return {str(x["api_service"]) for x in items}


def list_admin_services(q="", platform="", limit=400, offset=0):
    sql = """
        SELECT s.*, p.name AS provider_name
        FROM services s
        LEFT JOIN providers p ON p.id = s.provider_id
        WHERE 1=1
    """
    args = []
    if platform:
        sql += " AND IFNULL(s.platform,'อื่น ๆ')=?"
        args.append(platform)
    if q:
        like = "%" + q.strip() + "%"
        sql += " AND (s.name LIKE ? OR IFNULL(s.api_service,'') LIKE ? OR CAST(s.id AS TEXT) LIKE ? OR IFNULL(s.category,'') LIKE ?)"
        args.extend([like, like, like, like])
    sql += " ORDER BY s.platform, s.category, s.id DESC LIMIT ? OFFSET ?"
    args.extend([int(limit), int(offset)])
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [dict(x) for x in items]


def count_admin_services(q="", platform=""):
    sql = "SELECT COUNT(*) c FROM services WHERE 1=1"
    args = []
    if platform:
        sql += " AND IFNULL(platform,'อื่น ๆ')=?"
        args.append(platform)
    if q:
        like = "%" + q.strip() + "%"
        sql += " AND (name LIKE ? OR IFNULL(api_service,'') LIKE ? OR CAST(id AS TEXT) LIKE ? OR IFNULL(category,'') LIKE ?)"
        args.extend([like, like, like, like])
    con = connect()
    row = con.execute(sql, args).fetchone()
    con.close()
    return int(row["c"] if row else 0)


def set_service_status(sid, status):
    con = connect()
    con.execute("UPDATE services SET status=? WHERE id=?", (status, int(sid)))
    con.commit()
    con.close()
    shop_cache_clear()


def update_service_rate(sid, rate):
    con = connect()
    con.execute("UPDATE services SET rate=? WHERE id=?", (float(rate or 0), int(sid)))
    con.commit()
    con.close()
    shop_cache_clear()


def bump_service_rates(ids, percent):
    pct = float(percent or 0)
    con = connect()
    for sid in ids:
        row = con.execute("SELECT rate FROM services WHERE id=?", (int(sid),)).fetchone()
        if not row:
            continue
        con.execute("UPDATE services SET rate=? WHERE id=?", (money(float(row["rate"] or 0) * (1 + pct / 100.0)), int(sid)))
    con.commit()
    con.close()
    shop_cache_clear()
    return len(ids)


def _service_cost_row(con, row, usd):
    cost = row["cost_rate"]
    cur = norm_currency(row["currency"] or "", "USD")
    if cost is None and row["provider_id"] and row["api_service"]:
        cat = con.execute(
            "SELECT rate, currency FROM provider_catalog WHERE provider_id=? AND api_service=?",
            (int(row["provider_id"]), str(row["api_service"])),
        ).fetchone()
        if cat:
            cost = cat["rate"]
            cur = norm_currency(cat["currency"] or cur, cur)
    if cost is None:
        return None, cur
    try:
        return float(cost), cur
    except (TypeError, ValueError):
        return None, cur


def apply_rates_from_cost(percent, fixed=0, ids=None):
    cfg = price_cfg(force=True)
    usd = cfg["usd"]
    try:
        pct = float(percent or 0)
    except (TypeError, ValueError):
        pct = 0.0
    try:
        extra = float(fixed or 0)
    except (TypeError, ValueError):
        extra = 0.0
    con = connect()
    if ids:
        placeholders = ",".join("?" for _ in ids)
        rows = con.execute(
            "SELECT id, cost_rate, currency, provider_id, api_service FROM services WHERE id IN (%s)" % placeholders,
            [int(x) for x in ids],
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT id, cost_rate, currency, provider_id, api_service FROM services"
        ).fetchall()
    updated = 0
    for row in rows:
        cost, cur = _service_cost_row(con, row, usd)
        if cost is None:
            continue
        rate = sell_thb(cost, cur, usd, pct, extra)
        con.execute("UPDATE services SET rate=? WHERE id=?", (rate, int(row["id"])))
        updated += 1
    con.commit()
    con.close()
    shop_cache_clear()
    return updated


def set_service_subcategory(ids, category):
    cat = (category or "").strip()
    con = connect()
    for sid in ids:
        con.execute("UPDATE services SET category=? WHERE id=?", (cat, int(sid)))
    con.commit()
    con.close()
    shop_cache_clear()
    return len(ids)


def shop_platforms():
    return list_shop_mains()


def pending_send_orders(limit=15):
    con = connect()
    items = con.execute(
        "SELECT * FROM orders WHERE status='pending' AND IFNULL(api_orderid,'')='' ORDER BY id ASC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    return [dict(x) for x in items]


def active_status_orders(limit=30):
    con = connect()
    items = con.execute(
        "SELECT * FROM orders WHERE status IN ('processing','inprogress','pending') AND IFNULL(api_orderid,'')!='' ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    return [dict(x) for x in items]


def update_order(oid, **fields):
    if not fields:
        return
    sets = ", ".join("%s=?" % k for k in fields)
    vals = list(fields.values()) + [oid]
    con = connect()
    con.execute("UPDATE orders SET %s WHERE id=?" % sets, vals)
    con.commit()
    con.close()


def refund_order(oid, amount=None):
    con = connect()
    row = con.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not row:
        con.close()
        return False
    order = dict(row)
    if int(order.get("refunded") or 0):
        con.close()
        return False
    amt = float(amount if amount is not None else order.get("charge") or 0)
    if amt > 0 and order.get("client"):
        con.execute("UPDATE clients SET balance = balance + ? WHERE username=?", (amt, order["client"]))
    con.execute("UPDATE orders SET refunded=1 WHERE id=?", (oid,))
    con.commit()
    con.close()
    add_log("คืนเงินออเดอร์ #%s จำนวน %s" % (oid, amt), "-")
    return True


def add_cron_log(job, detail):
    con = connect()
    con.execute("INSERT INTO cron_logs (job, detail, created_at) VALUES (?,?,?)", (job, detail, now()))
    con.commit()
    con.close()


def list_cron_logs(limit=40, job=""):
    con = connect()
    job = (job or "").strip().lower()
    if job and job != "all":
        items = con.execute(
            "SELECT * FROM cron_logs WHERE lower(job)=? ORDER BY id DESC LIMIT ?",
            (job, int(limit)),
        ).fetchall()
    else:
        items = con.execute(
            "SELECT * FROM cron_logs ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    con.close()
    return [dict(x) for x in items]


def cron_log_job_counts(limit=200):
    con = connect()
    rows = con.execute(
        """
        SELECT job, COUNT(*) AS c FROM (
          SELECT job FROM cron_logs ORDER BY id DESC LIMIT ?
        ) t GROUP BY job ORDER BY c DESC
        """,
        (int(limit),),
    ).fetchall()
    con.close()
    return [{"job": r["job"], "count": int(r["c"] or 0)} for r in rows]