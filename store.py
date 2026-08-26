from datetime import datetime
import os
import random

from db import (
    _hash,
    _hash_eq,
    add_log,
    calc_charge,
    connect,
    get_client,
    get_service,
    now,
    save_settings,
    shop_cache_clear,
)


def extra_migrate():
    con = connect()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS dripfeeds (
            id INTEGER PRIMARY KEY,
            client TEXT,
            service_id INTEGER,
            service TEXT,
            link TEXT,
            quantity INTEGER,
            runs INTEGER,
            interval_min INTEGER,
            delivered INTEGER DEFAULT 0,
            charge REAL,
            status TEXT,
            last_run TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY,
            client TEXT,
            service_id INTEGER,
            service TEXT,
            username TEXT,
            min_qty INTEGER,
            max_qty INTEGER,
            posts INTEGER,
            delay INTEGER,
            expiry TEXT,
            delivered INTEGER DEFAULT 0,
            status TEXT,
            last_run TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            client TEXT,
            kind TEXT,
            status TEXT,
            detail TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS ticket_replies (
            id INTEGER PRIMARY KEY,
            ticket_id INTEGER,
            author TEXT,
            message TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS child_panels (
            id INTEGER PRIMARY KEY,
            client TEXT,
            domain TEXT,
            charge REAL,
            status TEXT,
            note TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS methods (
            id INTEGER PRIMARY KEY,
            name TEXT,
            detail TEXT,
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS banks (
            id INTEGER PRIMARY KEY,
            bank TEXT,
            account TEXT,
            holder TEXT,
            status TEXT DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            amount REAL,
            created_at TEXT
        );
        """
    )
    for table, col, spec in [
        ("clients", "ref_code", "TEXT"),
        ("clients", "referred_by", "TEXT"),
        ("clients", "ref_earn", "REAL"),
        ("clients", "google_id", "TEXT"),
        ("tickets", "reply", "TEXT"),
        ("orders", "parent_drip", "INTEGER"),
        ("orders", "parent_sub", "INTEGER"),
        ("child_panels", "admin_user", "TEXT"),
        ("child_panels", "admin_pass", "TEXT"),
        ("child_panels", "currency", "TEXT"),
    ]:
        cols = [r[1] for r in cur.execute("PRAGMA table_info(%s)" % table)]
        if col not in cols:
            cur.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, spec))
    if cur.execute("SELECT COUNT(*) FROM methods").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO methods (name, detail, status) VALUES (?,?,?)",
            [
                ("PromptPay", "โอนพร้อมเพย์ แล้วแจ้งสลิปผ่านตั๋ว", "active"),
                ("TrueMoney", "โอนวอลเล็ท แล้วแจ้งสลิปผ่านตั๋ว", "active"),
                ("โอนธนาคาร", "โอนเข้าบัญชีด้านล่าง แล้วแจ้งสลิปผ่านตั๋ว", "active"),
            ],
        )
    if cur.execute("SELECT COUNT(*) FROM news").fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO news (title, body, created_at) VALUES (?,?,?)",
            ("ยินดีต้อนรับสู่ LIKES AUTO", "สมัคร เติมเงิน แล้วสั่งซื้อได้ทันที ระบบดึงสถานะอัตโนมัติ", now()),
        )
    con.commit()
    for row in cur.execute("SELECT id, username, ref_code FROM clients").fetchall():
        if not row["ref_code"]:
            code = (row["username"] or ("u%s" % row["id"]))[:12]
            cur.execute("UPDATE clients SET ref_code=? WHERE id=?", (code, row["id"]))
    defaults = {
        "affiliate_percent": "5",
        "child_panel_price": "500",
        "child_ns1": "ns1.likes-auto.com",
        "child_ns2": "ns2.likes-auto.com",
        "announcement": "",
        "maintenance": "0",
        "min_deposit": "20",
        "promptpay": "",
        "bank_name": "",
        "bank_account": "",
        "bank_holder": "",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    con.commit()
    con.close()
    try:
        from pay import pay_migrate
        pay_migrate()
    except Exception:
        pass


def fetch_all(sql, args=()):
    con = connect()
    items = con.execute(sql, args).fetchall()
    con.close()
    return [dict(x) for x in items]


def fetch_one(sql, args=()):
    con = connect()
    row = con.execute(sql, args).fetchone()
    con.close()
    return dict(row) if row else None


def execute(sql, args=()):
    con = connect()
    cur = con.execute(sql, args)
    con.commit()
    lid = cur.lastrowid
    con.close()
    return lid


def minutes_ago(ts):
    if not ts:
        return 99999
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            t = datetime.strptime(ts, fmt)
            return (datetime.now() - t).total_seconds() / 60.0
        except ValueError:
            continue
    return 99999


def get_client_by_key(key):
    if not key:
        return None
    return fetch_one("SELECT * FROM clients WHERE api_key=?", (key,))


def adjust_balance(username, amount, note="-"):
    execute("UPDATE clients SET balance = balance + ? WHERE username=?", (amount, username))
    add_log("ปรับยอด %s %s (%s)" % (username, amount, note), "-")


def set_client_status(cid, status):
    execute("UPDATE clients SET status=? WHERE id=?", (status, cid))


def set_client_password(cid, password):
    execute("UPDATE clients SET password_hash=? WHERE id=?", (_hash(password), cid))


def regenerate_api_key(cid):
    key = os.urandom(12).hex()
    execute("UPDATE clients SET api_key=? WHERE id=?", (key, cid))
    return key


def save_service(sid, platform, name, rate, min_qty, max_qty, status, provider_id, api_service):
    if sid:
        execute(
            "UPDATE services SET platform=?, name=?, rate=?, min_qty=?, max_qty=?, status=?, provider_id=?, api_service=? WHERE id=?",
            (platform, name, float(rate or 0), int(min_qty or 1), int(max_qty or 100000), status or "active", provider_id or None, api_service or "", int(sid)),
        )
        shop_cache_clear()
        return int(sid)
    sid = execute(
        "INSERT INTO services (platform,name,rate,min_qty,max_qty,status,provider_id,api_service) VALUES (?,?,?,?,?,?,?,?)",
        (platform, name, float(rate or 0), int(min_qty or 1), int(max_qty or 100000), status or "active", provider_id or None, api_service or ""),
    )
    shop_cache_clear()
    return sid


def delete_service(sid):
    execute("DELETE FROM services WHERE id=?", (sid,))
    shop_cache_clear()


def spawn_order(client, service_id, link, quantity, charge=0, parent_drip=None, parent_sub=None):
    svc = get_service(service_id)
    if not svc:
        return None
    return execute(
        "INSERT INTO orders (client,service,link,quantity,charge,status,created_at,provider_id,service_id,parent_drip,parent_sub) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            client,
            "%s %s" % (svc["platform"], svc["name"]),
            link,
            int(quantity),
            float(charge or 0),
            "pending",
            now(),
            svc.get("provider_id"),
            svc.get("id"),
            parent_drip,
            parent_sub,
        ),
    )


def create_dripfeed(client, service_id, link, quantity, runs, interval_min):
    svc = get_service(service_id)
    if not svc:
        return None, "ไม่พบบริการ"
    runs = max(1, int(runs))
    interval_min = max(1, int(interval_min))
    qty = int(quantity)
    if qty < svc["min_qty"] or qty > svc["max_qty"]:
        return None, "จำนวนไม่อยู่ในช่วงที่กำหนด"
    charge = round(calc_charge(svc["rate"], qty) * runs, 2)
    user = get_client(username=client)
    if not user:
        return None, "ไม่พบบัญชี"
    if float(user["balance"] or 0) < charge:
        return None, "ยอดเงินไม่พอ กรุณาเติมเงิน"
    execute("UPDATE clients SET balance = balance - ? WHERE username=?", (charge, client))
    did = execute(
        "INSERT INTO dripfeeds (client,service_id,service,link,quantity,runs,interval_min,delivered,charge,status,last_run,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (client, svc["id"], "%s %s" % (svc["platform"], svc["name"]), link, qty, runs, interval_min, 0, charge, "active", "", now()),
    )
    add_log("เปิด drip-feed #%s" % did, "-")
    return did, None


def process_dripfeeds():
    n = 0
    for row in fetch_all("SELECT * FROM dripfeeds WHERE status='active'"):
        if row["delivered"] >= row["runs"]:
            execute("UPDATE dripfeeds SET status='completed' WHERE id=?", (row["id"],))
            continue
        if minutes_ago(row.get("last_run")) < int(row["interval_min"] or 1):
            continue
        spawn_order(row["client"], row["service_id"], row["link"], row["quantity"], 0, parent_drip=row["id"])
        delivered = int(row["delivered"] or 0) + 1
        status = "completed" if delivered >= int(row["runs"]) else "active"
        execute(
            "UPDATE dripfeeds SET delivered=?, last_run=?, status=? WHERE id=?",
            (delivered, now(), status, row["id"]),
        )
        n += 1
    return n


def create_subscription(client, service_id, username, min_qty, max_qty, posts, delay):
    svc = get_service(service_id)
    if not svc:
        return None, "ไม่พบบริการ"
    posts = max(1, int(posts))
    delay = max(1, int(delay))
    min_qty = int(min_qty)
    max_qty = int(max_qty)
    if min_qty > max_qty:
        min_qty, max_qty = max_qty, min_qty
    if min_qty < svc["min_qty"] or max_qty > svc["max_qty"]:
        return None, "จำนวนไม่อยู่ในช่วงที่กำหนด"
    user = get_client(username=client)
    if not user:
        return None, "ไม่พบบัญชี"
    sid = execute(
        "INSERT INTO subscriptions (client,service_id,service,username,min_qty,max_qty,posts,delay,delivered,status,last_run,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (client, svc["id"], "%s %s" % (svc["platform"], svc["name"]), username, min_qty, max_qty, posts, delay, 0, "active", "", now()),
    )
    add_log("เปิด subscription #%s" % sid, "-")
    return sid, None


def process_subscriptions():
    n = 0
    for row in fetch_all("SELECT * FROM subscriptions WHERE status='active'"):
        if int(row["delivered"] or 0) >= int(row["posts"] or 0):
            execute("UPDATE subscriptions SET status='completed' WHERE id=?", (row["id"],))
            continue
        if minutes_ago(row.get("last_run")) < int(row["delay"] or 1):
            continue
        qty = random.randint(int(row["min_qty"]), int(row["max_qty"]))
        svc = get_service(row["service_id"])
        if not svc:
            execute("UPDATE subscriptions SET status='canceled' WHERE id=?", (row["id"],))
            continue
        charge = calc_charge(svc["rate"], qty)
        user = get_client(username=row["client"])
        if not user or float(user["balance"] or 0) < charge:
            execute("UPDATE subscriptions SET status='paused' WHERE id=?", (row["id"],))
            continue
        execute("UPDATE clients SET balance = balance - ? WHERE username=?", (charge, row["client"]))
        link = "https://instagram.com/%s" % (row["username"] or "").lstrip("@")
        spawn_order(row["client"], row["service_id"], link, qty, charge, parent_sub=row["id"])
        delivered = int(row["delivered"] or 0) + 1
        status = "completed" if delivered >= int(row["posts"]) else "active"
        execute(
            "UPDATE subscriptions SET delivered=?, last_run=?, status=? WHERE id=?",
            (delivered, now(), status, row["id"]),
        )
        n += 1
    return n


def create_task(order_id, client, kind):
    existing = fetch_one(
        "SELECT id FROM tasks WHERE order_id=? AND kind=? AND status='pending'",
        (order_id, kind),
    )
    if existing:
        return None, "มีคำขอค้างอยู่แล้ว"
    tid = execute(
        "INSERT INTO tasks (order_id, client, kind, status, detail, created_at) VALUES (?,?,?,?,?,?)",
        (order_id, client, kind, "pending", "", now()),
    )
    return tid, None


def process_one_task(tid):
    from db import get_provider
    from smm_api import action

    row = fetch_one("SELECT * FROM tasks WHERE id=?", (tid,))
    if not row:
        return False
    order = fetch_one("SELECT * FROM orders WHERE id=?", (row["order_id"],))
    if not order or not order.get("api_orderid"):
        execute("UPDATE tasks SET status='failed', detail=? WHERE id=?", ("no_api_order", tid))
        return False
    svc = get_service(order.get("service_id")) if order.get("service_id") else None
    pid = (svc or {}).get("provider_id") or order.get("provider_id")
    provider = get_provider(pid) if pid else None
    if not provider:
        execute("UPDATE tasks SET status='failed', detail=? WHERE id=?", ("no_provider", tid))
        return False
    act = "refill" if row["kind"] == "refill" else "cancel"
    result = action(provider["api_url"], {"key": provider["api_key"], "action": act, "order": order["api_orderid"]})
    ok = isinstance(result, dict) and (result.get("refill") or result.get("cancel") or not result.get("error"))
    execute(
        "UPDATE tasks SET status=?, detail=? WHERE id=?",
        ("success" if ok else "failed", str(result)[:400], tid),
    )
    return ok


def process_tasks():
    n = 0
    for row in fetch_all("SELECT * FROM tasks WHERE status='pending'"):
        process_one_task(row["id"])
        n += 1
    return n


def set_task_status(tid, status):
    if status not in {"pending", "canceled", "failed", "success"}:
        return False
    execute("UPDATE tasks SET status=? WHERE id=?", (status, int(tid)))
    return True


def ticket_replies(tid):
    return fetch_all("SELECT * FROM ticket_replies WHERE ticket_id=? ORDER BY id", (tid,))


def all_ticket_replies():
    items = fetch_all("SELECT * FROM ticket_replies ORDER BY id")
    grouped = {}
    for row in items:
        grouped.setdefault(int(row["ticket_id"]), []).append(row)
    return grouped


def reply_ticket(tid, author, message, status="answered"):
    execute(
        "INSERT INTO ticket_replies (ticket_id, author, message, created_at) VALUES (?,?,?,?)",
        (tid, author, message, now()),
    )
    execute("UPDATE tickets SET reply=?, status=? WHERE id=?", (message, status, tid))


def close_ticket(tid):
    execute("UPDATE tickets SET status='closed' WHERE id=?", (tid,))


def add_news(title, body):
    return execute("INSERT INTO news (title, body, created_at) VALUES (?,?,?)", (title, body, now()))


def delete_news(nid):
    execute("DELETE FROM news WHERE id=?", (nid,))


def list_news(limit=20):
    return fetch_all("SELECT * FROM news ORDER BY id DESC LIMIT ?", (limit,))


def create_child_panel(client, domain, admin_user="", admin_pass="", currency="THB"):
    import re
    from db import get_settings

    settings = get_settings()
    price = float(settings.get("child_panel_price") or 500)
    user = get_client(username=client)
    if not user:
        return None, "ไม่พบบัญชี"
    domain = (domain or "").strip().lower().lstrip("https://").lstrip("http://").split("/")[0].strip(".")
    if domain.startswith("www."):
        domain = domain[4:]
    if not re.fullmatch(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+", domain or ""):
        return None, "รูปแบบโดเมนไม่ถูกต้อง เช่น mybrand.com"
    admin_user = (admin_user or "").strip()
    admin_pass = (admin_pass or "").strip()
    currency = (currency or "THB").strip().upper() or "THB"
    if len(admin_user) < 3:
        return None, "ชื่อแอดมินอย่างน้อย 3 ตัวอักษร"
    if len(admin_pass) < 6:
        return None, "รหัสผ่านอย่างน้อย 6 ตัวอักษร"
    if float(user["balance"] or 0) < price:
        return None, "ยอดเงินไม่พอ กรุณาเติมเงินก่อน"
    if fetch_one("SELECT id FROM child_panels WHERE domain=?", (domain,)):
        return None, "โดเมนนี้ถูกใช้แล้ว"
    pending = fetch_one(
        "SELECT COUNT(*) c FROM child_panels WHERE client=? AND status IN ('pending','active')",
        (client,),
    )
    if int((pending or {}).get("c") or 0) >= 5:
        return None, "เปิดแผงได้สูงสุด 5 โดเมนต่อบัญชี"
    execute("UPDATE clients SET balance = balance - ? WHERE username=?", (price, client))
    pid = execute(
        "INSERT INTO child_panels (client, domain, charge, status, note, created_at, admin_user, admin_pass, currency) VALUES (?,?,?,?,?,?,?,?,?)",
        (client, domain, price, "pending", "", now(), admin_user, admin_pass, currency),
    )
    add_log("คำขอแผงลูก #%s โดเมน %s โดย %s" % (pid, domain, client), "-")
    return pid, None


def set_child_status(pid, status):
    row = fetch_one("SELECT * FROM child_panels WHERE id=?", (pid,))
    if not row:
        return
    if status == "canceled" and row["status"] == "pending":
        execute("UPDATE clients SET balance = balance + ? WHERE username=?", (row["charge"], row["client"]))
    execute("UPDATE child_panels SET status=? WHERE id=?", (status, pid))


def transfer_funds(sender, receiver, amount):
    amt = float(amount)
    if amt <= 0:
        return None, "จำนวนไม่ถูกต้อง"
    src = get_client(username=sender)
    dst = get_client(username=receiver)
    if not dst:
        return None, "ไม่พบผู้รับ"
    if sender == receiver:
        return None, "โอนให้ตัวเองไม่ได้"
    if float(src["balance"] or 0) < amt:
        return None, "ยอดเงินไม่พอ"
    execute("UPDATE clients SET balance = balance - ? WHERE username=?", (amt, sender))
    execute("UPDATE clients SET balance = balance + ? WHERE username=?", (amt, receiver))
    execute(
        "INSERT INTO transfers (sender, receiver, amount, created_at) VALUES (?,?,?,?)",
        (sender, receiver, amt, now()),
    )
    add_log("โอน %s จาก %s ไป %s" % (amt, sender, receiver), "-")
    return True, None


def credit_affiliate(client, amount):
    user = get_client(username=client)
    if not user or not user.get("referred_by"):
        return
    from db import get_settings

    percent = float(get_settings().get("affiliate_percent") or 0)
    if percent <= 0:
        return
    bonus = round(float(amount) * percent / 100.0, 2)
    if bonus <= 0:
        return
    execute("UPDATE clients SET balance = balance + ?, ref_earn = IFNULL(ref_earn,0) + ? WHERE username=?", (bonus, bonus, user["referred_by"]))
    add_log("คอมมิชชัน %s ให้ %s" % (bonus, user["referred_by"]), "-")


def set_admin_password(username, password):
    execute("UPDATE admins SET password_hash=? WHERE username=?", (_hash(password), username))


def report_data():
    return {
        "paid": fetch_one("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='paid'")["s"],
        "pending_pay": fetch_one("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='pending'")["s"],
        "pending_pay_n": fetch_one("SELECT COUNT(*) c FROM payments WHERE status='pending'")["c"],
        "order_sum": fetch_one("SELECT COALESCE(SUM(charge),0) s FROM orders")["s"],
        "clients": fetch_one("SELECT COUNT(*) c FROM clients")["c"],
        "open_tickets": fetch_one("SELECT COUNT(*) c FROM tickets WHERE status='open'")["c"],
        "active_drip": fetch_one("SELECT COUNT(*) c FROM dripfeeds WHERE status='active'")["c"],
        "active_sub": fetch_one("SELECT COUNT(*) c FROM subscriptions WHERE status='active'")["c"],
        "pending_tasks": fetch_one("SELECT COUNT(*) c FROM tasks WHERE status='pending'")["c"],
        "pending_panels": fetch_one("SELECT COUNT(*) c FROM child_panels WHERE status='pending'")["c"],
    }


def change_client_password(username, old_password, new_password):
    user = get_client(username=username)
    if not user or not _hash_eq(user.get("password_hash"), old_password):
        return False, "รหัสผ่านเดิมไม่ถูกต้อง"
    execute("UPDATE clients SET password_hash=? WHERE username=?", (_hash(new_password), username))
    return True, None
