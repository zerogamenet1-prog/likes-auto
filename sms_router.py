from base64 import b64encode
from urllib.parse import quote
import re
import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA


class RouterError(Exception):
    pass


class MR6400:
    def __init__(self, base_url, username="admin", password=""):
        self.base = str(base_url or "http://192.168.2.1").rstrip("/")
        self.username = username or "admin"
        self.password = password or ""
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Referer": self.base + "/",
            "Content-Type": "text/plain",
        })
        self.token = ""

    def _rsa(self, value):
        r = self.s.post(self.base + "/cgi/getParm", timeout=12)
        r.raise_for_status()
        nn = re.search(r'var nn="([0-9A-Fa-f]+)"', r.text)
        ee = re.search(r'var ee="([0-9A-Fa-f]+)"', r.text)
        if not nn or not ee:
            raise RouterError("no rsa key")
        n = int(nn.group(1), 16)
        e = int(ee.group(1), 16)
        cipher = PKCS1_v1_5.new(RSA.construct((n, e)))
        enc = cipher.encrypt(value.encode("utf-8"))
        return enc.hex().zfill(256)

    def login(self):
        user = self._rsa(self.username)
        pwd = self._rsa(b64encode(self.password.encode("utf-8")).decode("ascii"))
        q = "UserName=%s&Passwd=%s&Action=1&LoginStatus=0" % (
            quote(user, safe=""),
            quote(pwd, safe=""),
        )
        r = self.s.post(self.base + "/cgi/login?" + q, timeout=12)
        r.raise_for_status()
        ret = re.search(r"\$\.ret=(\d+)", r.text)
        code = int(ret.group(1)) if ret else -1
        if code == 1:
            raise RouterError("wrong password")
        if code not in (0,):
            raise RouterError("login failed %s" % code)
        home = self.s.get(self.base + "/", timeout=12)
        home.raise_for_status()
        tok = re.search(r'var token="([^"]+)"', home.text or "")
        if not tok:
            raise RouterError("no token after login")
        self.token = tok.group(1)
        self.s.headers["TokenID"] = self.token
        return True

    def _cgi(self, actions, body):
        url = self.base + "/cgi?" + str(actions).lstrip("?")
        r = self.s.post(url, data=body.encode("utf-8"), timeout=15)
        r.raise_for_status()
        return r.text

    def total(self):
        raw = self._cgi("1", (
            "[LTE_SMS_RECVMSGBOX#0,0,0,0,0,0#0,0,0,0,0,0]0,1\r\n"
            "totalNumber\r\n"
        ))
        m = re.search(r"totalNumber=(\d+)", raw or "")
        return int(m.group(1)) if m else 0

    def inbox_page(self, page=1):
        body = (
            "[LTE_SMS_RECVMSGBOX#0,0,0,0,0,0#0,0,0,0,0,0]0,1\r\n"
            "PageNumber=%s\r\n"
            "[LTE_SMS_RECVMSGENTRY#0,0,0,0,0,0#0,0,0,0,0,0]1,5\r\n"
            "index\r\nfrom\r\ncontent\r\nreceivedTime\r\nunread\r\n"
        ) % int(page)
        return parse_sms(self._cgi("2&5", body))

    def inbox(self, pages=8):
        items = []
        seen_ids = set()
        for page in range(1, max(1, int(pages)) + 1):
            chunk = self.inbox_page(page)
            if not chunk:
                break
            fresh = 0
            for sms in chunk:
                sid = sms.get("id") or ""
                if sid and sid in seen_ids:
                    continue
                if sid:
                    seen_ids.add(sid)
                items.append(sms)
                fresh += 1
            if fresh == 0:
                break
        return items


def _decode_content(text):
    blob = str(text or "")
    blob = blob.replace(chr(18), "\n").replace(chr(17), "\r")
    if re.fullmatch(r"[0-9A-Fa-f]+", blob) and len(blob) >= 8 and len(blob) % 4 == 0:
        try:
            return bytes.fromhex(blob).decode("utf-16-be", "replace")
        except Exception:
            pass
    return blob


def parse_sms(raw):
    items = []
    cur = {}
    for line in str(raw or "").splitlines():
        line = line.strip()
        if line.startswith("[") and "]" in line:
            if cur.get("sender") or cur.get("content"):
                items.append(cur)
            cur = {}
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key == "from":
            cur["sender"] = val
        elif key == "content":
            cur["content"] = _decode_content(val)
        elif key == "index":
            cur["id"] = val
        elif key == "receivedTime":
            cur["time"] = val
        elif key == "unread":
            cur["unread"] = val == "1"
    if cur.get("sender") or cur.get("content"):
        items.append(cur)
    out = []
    for item in items:
        if item.get("content") or item.get("sender"):
            out.append({
                "id": str(item.get("id") or ""),
                "sender": item.get("sender") or "",
                "content": item.get("content") or "",
                "time": item.get("time") or "",
                "unread": bool(item.get("unread")),
            })
    return out
