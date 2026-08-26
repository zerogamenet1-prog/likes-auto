import os
import posixpath
from pathlib import Path

import paramiko

pw = os.environ.get("VPS_PW")
if not pw:
    raise SystemExit("missing VPS_PW")

local = Path(__file__).resolve().parent
remote = "/var/www/likes-auto"
files = [
    "service_fields.py",
    "db.py",
    "cron_jobs.py",
    "panel.py",
    "api_v2.py",
    "th_shop.py",
    "templates/neworder.html",
    "templates/base.html",
    "static/js/order-form.js",
    "static/css/panel/ideacode/dash.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "103.91.205.39",
    username=os.environ.get("VPS_USER", "root"),
    password=pw,
    timeout=25,
    allow_agent=False,
    look_for_keys=False,
)
sftp = c.open_sftp()
for f in files:
    src = local / f
    data = src.read_bytes()
    if b"\x00" in data:
        data = data.replace(b"\x00", b"")
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        text = data.decode("utf-16")
        data = text.encode("utf-8")
    dst = posixpath.join(remote, f)
    with sftp.open(dst, "wb") as out:
        out.write(data)
    print("up", f)
sftp.close()
paths = " ".join(posixpath.join(remote, f) for f in files)
_, o, e = c.exec_command(
    "chown www-data:www-data %s; systemctl restart likes-auto; sleep 2; systemctl is-active likes-auto; "
    "grep -c needs_comments /var/www/likes-auto/service_fields.py; "
    "grep -c comments-wrap /var/www/likes-auto/templates/neworder.html; "
    "grep -c syncOrderFields /var/www/likes-auto/static/js/order-form.js"
    % paths,
    timeout=60,
)
print(o.read().decode("utf-8", "replace"))
err = e.read().decode("utf-8", "replace")
if err.strip():
    print("ERR", err)
c.close()