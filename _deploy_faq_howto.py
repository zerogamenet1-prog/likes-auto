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
    "templates/faq.html",
    "templates/base.html",
    "content.py",
    "static/css/panel/ideacode/pages.css",
]
imgs = sorted((local / "static/assets/howto").glob("*.png"))

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
howto_dir = posixpath.join(remote, "static/assets/howto")
try:
    sftp.stat(howto_dir)
except FileNotFoundError:
    sftp.mkdir(howto_dir)

for f in files:
    sftp.put(str(local / f), posixpath.join(remote, f))
    print("up", f)
for img in imgs:
    rel = "static/assets/howto/" + img.name
    sftp.put(str(img), posixpath.join(remote, rel))
    print("up", rel, img.stat().st_size)
sftp.close()

cmd = (
    "chown -R www-data:www-data /var/www/likes-auto/templates/faq.html "
    "/var/www/likes-auto/templates/base.html /var/www/likes-auto/content.py "
    "/var/www/likes-auto/static/css/panel/ideacode/pages.css "
    "/var/www/likes-auto/static/assets/howto; "
    "systemctl restart likes-auto; sleep 1; systemctl is-active likes-auto; "
    "ls -la /var/www/likes-auto/static/assets/howto; "
    "grep -c la-howto /var/www/likes-auto/templates/faq.html; "
    "grep -c 'pages.css?v=pro95' /var/www/likes-auto/templates/base.html"
)
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode("utf-8", "replace"))
err = e.read().decode("utf-8", "replace")
if err.strip():
    print("ERR", err)
c.close()
