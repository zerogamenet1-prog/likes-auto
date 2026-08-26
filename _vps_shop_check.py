import os
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "103.91.205.39",
    username="root",
    password=os.environ["VPS_PW"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
remote_py = """
import sys
sys.path.insert(0, "/var/www/likes-auto")
from db import connect, get_settings, shop_manual_locked
con = connect()
print("providers", [dict(r) for r in con.execute("SELECT id,name,currency,balance FROM providers")])
print("services_active", con.execute("SELECT COUNT(*) FROM services WHERE status='active'").fetchone()[0])
print("services_inactive", con.execute("SELECT COUNT(*) FROM services WHERE status!='active'").fetchone()[0])
print("with_api", con.execute("SELECT COUNT(*) FROM services WHERE IFNULL(api_service,'')!=''").fetchone()[0])
print("catalog", [dict(r) for r in con.execute("SELECT provider_id, COUNT(*) c FROM provider_catalog GROUP BY provider_id")])
print("orphan_api", con.execute("SELECT COUNT(*) FROM services s LEFT JOIN provider_catalog c ON c.provider_id=s.provider_id AND c.api_service=s.api_service WHERE IFNULL(s.api_service,'')!='' AND c.id IS NULL").fetchone()[0])
s = get_settings()
print("catalog_synced_at", s.get("catalog_synced_at"))
print("catalog_sync_pid", s.get("catalog_sync_pid"))
print("shop_rebuild_at", s.get("shop_rebuild_at"))
print("shop_manual_locked", shop_manual_locked())
print("profit", s.get("profit_percent"), "usd", s.get("usd_rate"))
print("cron recent:")
for r in con.execute("SELECT id,job,substr(detail,1,140) d,created_at FROM cron_logs ORDER BY id DESC LIMIT 10"):
    print(dict(r))
con.close()
"""
sftp = c.open_sftp()
with sftp.file("/tmp/la_shop_check.py", "w") as f:
    f.write(remote_py)
sftp.close()
_, o, e = c.exec_command(
    "cd /var/www/likes-auto; PYTHONPATH=/var/www/likes-auto python3 /tmp/la_shop_check.py; echo ---; crontab -l 2>/dev/null | head -40",
    timeout=90,
)
print(o.read().decode("utf-8", "replace"))
err = e.read().decode("utf-8", "replace")
if err.strip():
    print("ERR", err)
c.close()