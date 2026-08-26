import os, paramiko
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("103.91.205.39", username="root", password=os.environ["VPS_PW"], timeout=30, allow_agent=False, look_for_keys=False)
remote = """
import sys
sys.path.insert(0, "/var/www/likes-auto")
from db import connect, sell_thb, price_cfg
con = connect()
cfg = price_cfg(True)
print("cfg", cfg)
rows = con.execute("""
SELECT s.id, s.api_service, s.rate sell, s.cost_rate, s.currency, c.rate cat_rate, c.currency cat_cur, s.name
FROM services s
JOIN provider_catalog c ON c.provider_id=s.provider_id AND c.api_service=s.api_service
LIMIT 8
""").fetchall()
for r in rows:
    d=dict(r)
    live = sell_thb(d["cat_rate"], d["cat_cur"] or "USD", cfg["usd"], cfg["pct"], 0)
    print(d["id"], "sell", d["sell"], "cost", d["cost_rate"], "cat", d["cat_rate"], "expect", live, "diff", round(float(d["sell"] or 0)-live,4), (d["name"] or "")[:50])
# mismatch count
n = con.execute("""
SELECT COUNT(*) FROM services s
JOIN provider_catalog c ON c.provider_id=s.provider_id AND c.api_service=s.api_service
WHERE abs(IFNULL(s.cost_rate,0) - IFNULL(c.rate,0)) > 0.00001
""").fetchone()[0]
print("cost_mismatch", n)
n2 = con.execute("""
SELECT COUNT(*) FROM services s
JOIN provider_catalog c ON c.provider_id=s.provider_id AND c.api_service=s.api_service
WHERE abs(IFNULL(s.min_qty,0) - IFNULL(c.min_qty,0)) > 0 OR abs(IFNULL(s.max_qty,0) - IFNULL(c.max_qty,0)) > 0
""").fetchone()[0]
print("qty_mismatch", n2)
bad = con.execute("""
SELECT COUNT(*) FROM provider_catalog
WHERE lower(name) LIKE '%not working%' OR lower(name) LIKE '%disabled%' OR lower(category) LIKE '%not working%'
""").fetchone()[0]
print("catalog_bad_name", bad)
con.close()
"""
sftp=c.open_sftp(); f=sftp.file("/tmp/la_price.py","w"); f.write(remote); f.close(); sftp.close()
_,o,e=c.exec_command("PYTHONPATH=/var/www/likes-auto python3 /tmp/la_price.py", timeout=60)
print(o.read().decode()); print(e.read().decode())
c.close()