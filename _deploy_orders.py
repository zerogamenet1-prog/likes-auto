import os
import posixpath
from pathlib import Path
import paramiko
pw = os.environ.get("VPS_PW")
local = Path(__file__).resolve().parent
remote = "/var/www/likes-auto"
files = [
    "service_fields.py", "db.py", "panel.py",
    "templates/orders.html", "templates/base.html",
    "static/css/panel/ideacode/dash.css",
]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("103.91.205.39", username="root", password=pw, timeout=25, allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
for f in files:
    data = (local / f).read_bytes()
    if data.startswith(b"\xff\xfe"):
        data = data.decode("utf-16").encode("utf-8")
    with sftp.open(posixpath.join(remote, f), "wb") as out:
        out.write(data)
    print("up", f)
sftp.close()
paths = " ".join(posixpath.join(remote, f) for f in files)
_, o, e = c.exec_command(
    "chown www-data:www-data %s; systemctl restart likes-auto; sleep 2; systemctl is-active likes-auto; "
    "grep -c can_refill /var/www/likes-auto/panel.py; grep -c la-ord-kpi /var/www/likes-auto/static/css/panel/ideacode/dash.css"
    % paths,
    timeout=60,
)
print(o.read().decode("utf-8", "replace"))
c.close()