"""Upload current SEO/UI release to production VPS. Requires VPS_PW env."""
import json
import os
import posixpath
import urllib.request
from pathlib import Path

import paramiko

pw = os.environ.get("VPS_PW")
if not pw:
    raise SystemExit("missing VPS_PW")

local = Path(__file__).resolve().parent
remote = "/var/www/likes-auto"

FILES = [
    "app.py",
    "blog_content.py",
    "blog_html.py",
    "blog_posts_rest.py",
    "cms.py",
    "content.py",
    "hub.py",
    "panel.py",
    "seo.py",
    "seo_hubs.py",
    "seo_landings.py",
    "service_fields.py",
    "theme.py",
    "templates/_dash_side.html",
    "templates/_guard_fields.html",
    "templates/admin/settings_hub.html",
    "templates/base.html",
    "templates/dripfeeds.html",
    "templates/faq.html",
    "templates/home.html",
    "templates/neworder.html",
    "templates/notfound.html",
    "templates/platform.html",
    "templates/seo_hub.html",
    "templates/services.html",
    "templates/signin.html",
    "templates/site_map.html",
    "templates/subscriptions.html",
    "static/assets/admin-crest.png",
    "static/assets/apple-touch.png",
    "static/assets/brand.svg",
    "static/assets/favicon.png",
    "static/assets/favicon.svg",
    "static/css/panel/ideacode/dash.css",
    "static/css/panel/ideacode/pages.css",
    "static/css/panel/ideacode/responsive.css",
    "static/css/panel/ideacode/themes.css",
    "static/js/fx.js",
    "static/js/home.js",
    "static/js/order-form.js",
    "static/llms.txt",
]


def payload(src: Path) -> bytes:
    data = src.read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16").encode("utf-8")
    if b"\x00" in data[:80]:
        return data.decode("utf-16-le").encode("utf-8")
    return data


def main():
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
    for rel in FILES:
        src = local / rel
        if not src.is_file():
            raise SystemExit("missing local file: %s" % rel)
        dst = posixpath.join(remote, rel.replace("\\", "/"))
        parent = posixpath.dirname(dst)
        try:
            sftp.stat(parent)
        except OSError:
            pass
        data = payload(src)
        with sftp.open(dst, "wb") as out:
            out.write(data)
        print("up", rel, len(data))
    sftp.close()

    paths = " ".join(posixpath.join(remote, f.replace("\\", "/")) for f in FILES)
    cmd = (
        "chown www-data:www-data %s; "
        "systemctl restart likes-auto; sleep 3; systemctl is-active likes-auto; "
        "curl -s -o /dev/null -w 'home %%{http_code}\\n' https://likes-auto.com/; "
        "curl -s -o /dev/null -w 'pum-like %%{http_code}\\n' https://likes-auto.com/pum-like; "
        "curl -s -o /dev/null -w 'site-map %%{http_code}\\n' https://likes-auto.com/site-map; "
        "curl -s -o /dev/null -w 'llms %%{http_code}\\n' https://likes-auto.com/llms.txt; "
        "curl -s https://likes-auto.com/sitemap-pages.xml | grep -c '<url>'"
    ) % paths
    _, o, e = c.exec_command(cmd, timeout=120)
    print(o.read().decode("utf-8", "replace"))
    err = e.read().decode("utf-8", "replace")
    if err.strip():
        print("ERR", err)
    c.close()

    import sys

    sys.path.insert(0, str(local))
    from seo import INDEXNOW_KEY, site_url
    from app import _sitemap_pages, _sitemap_platforms, _sitemap_blog

    urls = []
    for fn in (_sitemap_pages, _sitemap_platforms, _sitemap_blog):
        urls.extend(item["loc"] for item in fn())
    body = json.dumps(
        {
            "host": "likes-auto.com",
            "key": INDEXNOW_KEY,
            "keyLocation": site_url() + "/" + INDEXNOW_KEY + ".txt",
            "urlList": urls[:100],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("indexnow", resp.status, "urls", len(urls[:100]))
    except Exception as ex:
        print("indexnow err", ex)


if __name__ == "__main__":
    main()
