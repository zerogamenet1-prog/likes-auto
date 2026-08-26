import os, posixpath
from pathlib import Path
import paramiko
pw = os.environ["VPS_PW"]
local = Path(__file__).resolve().parent
remote = "/var/www/likes-auto"
files = [
    "admin.py",
    "db.py",
    "templates/admin/crons.html",
    "templates/admin/base.html",
    "static/css/panel/ideacode/admin.css",
]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("103.91.205.39", username="root", password=pw, timeout=30, allow_agent=False, look_for_keys=False, banner_timeout=30)
sftp = c.open_sftp()
for f in files:
    sftp.put(str(local / f), posixpath.join(remote, f))
    print("up", f)
sftp.close()
cmd = (
    "chown www-data:www-data "
    + " ".join("/var/www/likes-auto/" + f for f in files)
    + "; systemctl restart likes-auto; sleep 1; systemctl is-active likes-auto; "
    + "grep -c cron-log-list /var/www/likes-auto/templates/admin/crons.html; "
    + "grep -c format_cron_logs /var/www/likes-auto/admin.py; "
    + "grep -c admin.css?v=dash25 /var/www/likes-auto/templates/admin/base.html"
)
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode("utf-8", "replace"))
err = e.read().decode("utf-8", "replace")
if err.strip():
    print("ERR", err)
c.close()