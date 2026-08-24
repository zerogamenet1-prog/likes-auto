import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / "sms.env"
SEEN_PATH = ROOT / "data" / "sms_seen.json"


def load_env():
    vals = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    for k in (
        "ROUTER_URL", "ROUTER_USER", "ROUTER_PASS", "PAY_WEBHOOK",
        "POLL_SEC", "SMS_SENDERS", "POLL_PAGES",
    ):
        if os.environ.get(k):
            vals[k] = os.environ[k]
    return vals


def load_seen():
    try:
        return set(json.loads(SEEN_PATH.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_seen(seen):
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    items = sorted(seen)[-800:]
    SEEN_PATH.write_text(json.dumps(items), encoding="utf-8")


def post_pay(webhook, sms):
    payload = json.dumps({
        "source": "sms",
        "sender": sms.get("sender") or "",
        "text": sms.get("content") or "",
        "sms": sms.get("content") or "",
    }).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "likes-auto-sms/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", "replace") or "{}")


def key_of(sms):
    return "|".join([
        str(sms.get("id") or ""),
        str(sms.get("time") or ""),
        str(sms.get("sender") or ""),
        str(sms.get("content") or "")[:80],
    ])


def is_krungthai_sender(sender):
    text = str(sender or "").lower()
    keys = ("krungthai", "krung thai", "ktb", "\u0e01\u0e23\u0e38\u0e07\u0e44\u0e17\u0e22")
    return any(k in text for k in keys)


def wanted(sms, only):
    if only == "*":
        return True
    return is_krungthai_sender(sms.get("sender") or "")


def poll_once(cfg, seen, router):
    pages = int(cfg.get("POLL_PAGES") or 8)
    messages = router.inbox(pages)
    webhook = cfg.get("PAY_WEBHOOK") or ""
    if not webhook:
        raise SystemExit("missing PAY_WEBHOOK")
    only = str(cfg.get("SMS_SENDERS") or "krungthai").strip().lower()
    wanted_msgs = [sms for sms in messages if wanted(sms, only)]
    if not seen:
        for sms in wanted_msgs:
            seen.add(key_of(sms))
        save_seen(seen)
        print("seeded %s existing %s sms, waiting for new" % (len(wanted_msgs), only))
        return 0, len(messages)
    n = 0
    for sms in wanted_msgs:
        kid = key_of(sms)
        if kid in seen:
            continue
        result = post_pay(webhook, sms)
        seen.add(kid)
        n += 1
        sender = sms.get("sender") or ""
        snippet = (sms.get("content") or "").replace("\n", " ")[:60]
        print("%s %s %s -> %s" % (sms.get("time") or "", sender, snippet, result))
    if n:
        save_seen(seen)
    return n, len(messages)


def main():
    cfg = load_env()
    if not (cfg.get("ROUTER_PASS") or "").strip():
        print("Put the router admin password in sms.env as ROUTER_PASS=")
        return 2
    seen = load_seen()
    loop = "--loop" in sys.argv
    wait = int(cfg.get("POLL_SEC") or 12)
    from sms_router import MR6400
    router = None
    while True:
        try:
            if router is None:
                router = MR6400(
                    cfg.get("ROUTER_URL") or "http://192.168.2.1",
                    cfg.get("ROUTER_USER") or "admin",
                    cfg.get("ROUTER_PASS") or "",
                )
                router.login()
                print("router login ok")
            n, total = poll_once(cfg, seen, router)
            print("checked %s sms, new %s" % (total, n))
        except Exception as e:
            print("poll error", type(e).__name__, e)
            router = None
        if not loop:
            break
        time.sleep(max(5, wait))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
