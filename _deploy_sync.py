import os
import posixpath
from pathlib import Path

import paramiko

pw = os.environ["VPS_PW"]
local = Path(__file__).resolve().parent
remote = "/var/www/likes-auto"
files = [
    "db.py",
    "cron_jobs.py",
    "more.py",
    "templates/admin/service_import.html",
    "templates/admin/crons.html",
    "static/js/admin-import.js",
    # also finish FAQ mobile spacing from prior task
    "templates/faq.html",
    "templates/base.html",
    "content.py",
    "static/css/panel/ideacode/pages.css",
    "static/css/panel/ideacode/responsive.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "103.91.205.39",
    username="root",
    password=pw,
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
    banner_timeout=30,
)
sftp = c.open_sftp()
for f in files:
    sftp.put(str(local / f), posixpath.join(remote, f))
    print("up", f)
sftp.close()

# lock shop + run one sync
cmd = r'''
chown www-data:www-data /var/www/likes-auto/db.py /var/www/likes-auto/cron_jobs.py /var/www/likes-auto/more.py \
  /var/www/likes-auto/templates/admin/service_import.html /var/www/likes-auto/templates/admin/crons.html \
  /var/www/likes-auto/static/js/admin-import.js /var/www/likes-auto/templates/faq.html \
  /var/www/likes-auto/templates/base.html /var/www/likes-auto/content.py \
  /var/www/likes-auto/static/css/panel/ideacode/pages.css /var/www/likes-auto/static/css/panel/ideacode/responsive.css
systemctl restart likes-auto
sleep 2
systemctl is-active likes-auto
cd /var/www/likes-auto
PYTHONPATH=/var/www/likes-auto python3 - <<'PY'
from db import set_shop_manual_lock, sync_listed_from_catalog, list_providers, save_settings, now
from cron_jobs import refresh_catalogs
set_shop_manual_lock(True)
print("manual_lock on")
print("refresh", refresh_catalogs())
for p in list_providers():
    print("sync", p["id"], sync_listed_from_catalog(p["id"]))
save_settings({"shop_synced_at": now()})
from db import connect
con=connect()
print("active", con.execute("SELECT COUNT(*) FROM services WHERE status='active'").fetchone()[0])
print("inactive", con.execute("SELECT COUNT(*) FROM services WHERE status!='active'").fetchone()[0])
print("recent sync logs:")
for r in con.execute("SELECT id,job,substr(detail,1,160) d,created_at FROM cron_logs WHERE job IN ('sync','shop','catalog') ORDER BY id DESC LIMIT 5"):
    print(dict(r))
con.close()
PY
'''
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode("utf-8", "replace"))
err = e.read().decode("utf-8", "replace")
if err.strip():
    print("ERR", err)
c.close()