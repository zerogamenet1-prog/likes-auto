"""Export public HTML + static assets for Apache/public_html hosting."""
import os
import re
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "hosting-static"
BRIDGE = ROOT / "hosting" / "bridge"

# Seed demo data for richer static pages during export.
os.environ.setdefault("ALLOW_DEMO_SEED", "1")

HTACCESS = """# Run PHP (DirectAdmin / CloudLinux)
AddHandler application/x-httpd-php .php
AddType application/x-httpd-php .php

RewriteEngine On
RewriteBase /

# Allow Let's Encrypt HTTP-01 challenges (must not redirect)
RewriteRule ^\\.well-known/acme-challenge/ - [L]

# Canonical host: apex (likes-auto.com)
RewriteCond %{REQUEST_URI} !^/\\.well-known/acme-challenge/ [NC]
RewriteCond %{HTTP_HOST} ^www\\.likes-auto\\.com$ [NC]
RewriteRule ^ https://likes-auto.com%{REQUEST_URI} [L,R=301]

# HTTPS (Let's Encrypt on origin, or Cloudflare Flexible when proxied)
RewriteCond %{REQUEST_URI} !^/\\.well-known/acme-challenge/ [NC]
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP:X-Forwarded-Proto} !https [NC]
RewriteCond %{HTTP:CF-Visitor} !'"scheme":"https"' [NC]
RewriteCond %{ENV:REDIRECT_STATUS} ^$
RewriteRule ^ https://likes-auto.com%{REQUEST_URI} [L,R=301]

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"
</IfModule>

# Auth/admin/panel must hit bridge (even if static HTML exists) so CSRF/session match
RewriteCond %{REQUEST_URI} ^/(admin|signin|signup|forgot|reset|neworder|orders|addfunds|account|tickets|dripfeeds|subscriptions|affiliates|panels|google-login|shop|v2|api|logout|internal)(/|$) [NC]
RewriteRule ^ la.php [L,QSA]

# POST always hits bridge
RewriteCond %{REQUEST_METHOD} !^(GET|HEAD)$ [NC]
RewriteCond %{REQUEST_URI} !^/(css|assets|static)/ [NC]
RewriteRule ^ la.php [L,QSA]

# Serve existing files/dirs
RewriteCond %{REQUEST_FILENAME} -f [OR]
RewriteCond %{REQUEST_FILENAME} -d
RewriteRule ^ - [L]
# /path -> /path/index.html
RewriteCond %{DOCUMENT_ROOT}%{REQUEST_URI}/index.html -f
RewriteRule ^(.+?)/?$ $1/index.html [L]

# Fallback to bridge (404 static pages)
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ la.php [L,QSA]

DirectoryIndex index.html la.php
"""

ALIAS_REDIRECTS = {
    "/web-pump-like": "/pum-like",
    "/web-pum-like": "/pum-like",
    "/pump-like": "/pum-like",
    "/pumlike": "/pum-like",
    "/pump-follow": "/pum-follow",
    "/pumfollow": "/pum-follow",
    "/pump-view": "/pum-view",
    "/pumview": "/pum-view",
    "/smmpanel": "/smm-panel",
    "/smm-panel-thai": "/smm-panel",
    "/thai-smm": "/smm-panel",
    "/thai-smm-panel": "/smm-panel",
    "/add-follower": "/add-followers",
    "/followers": "/add-followers",
    "/pum-like-thai": "/thai-likes",
    "/thai-like": "/thai-likes",
    "/pump-like-thai": "/thai-likes",
}


def collect_get_paths(app) -> list[str]:
    paths = set()
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        if "GET" not in methods:
            continue
        path = getattr(route, "path", "") or ""
        if not path or "{" in path:
            continue
        if path.startswith("/static") or path.startswith("/openapi"):
            continue
        paths.add(path)
    try:
        from seo_hubs import HUB_SLUGS
        from seo_landings import SLUGS

        for slug in HUB_SLUGS:
            paths.add("/" + slug)
        for slug in SLUGS:
            paths.add("/" + slug)
    except Exception:
        pass
    paths.update(ALIAS_REDIRECTS.keys())
    extra = [
        "/admin/login",
        "/admin",
        "/signin",
        "/signup",
        "/forgot",
        "/reset",
        "/neworder",
        "/orders",
        "/addfunds",
        "/account",
        "/tickets",
        "/dripfeeds",
        "/subscriptions",
        "/affiliates",
        "/panels",
        "/rss.xml",
        "/blog/rss.xml",
        "/sitemap-blog.xml",
    ]
    paths.update(extra)
    return sorted(paths)


def dest_for(path: str) -> Path:
    if path == "/":
        return OUT / "index.html"
    if re.search(r"\.(xml|txt|webmanifest|json)$", path) or path in ("/health",):
        name = path.lstrip("/").replace("/", "_")
        return OUT / name
    clean = path.strip("/")
    return OUT / clean / "index.html"


def export_path(client: TestClient, path: str) -> tuple[bool, str]:
    r = client.get(path, follow_redirects=True)
    if r.status_code != 200:
        return False, f"status {r.status_code}"
    dest = dest_for(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = r.content
    if path == "/health" and body.startswith(b"{"):
        body = b'{"ok":true,"engine":"static-bridge"}'
    dest.write_bytes(body)
    if dest.suffix == ".html":
        _fix_form_actions(dest)
    return True, dest.as_posix()


def _fix_form_actions(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    for path in ("/signin", "/signup", "/forgot", "/reset", "/admin/login"):
        text = text.replace(f'action="{path}"', f'action="{path}/"')
        text = text.replace(f"action='{path}'", f"action='{path}/'")
    html_path.write_text(text, encoding="utf-8")


def main():
    import shutil

    if OUT.exists():
        def _rm_readonly(func, path, _exc):
            import stat

            os.chmod(path, stat.S_IWRITE)
            func(path)

        shutil.rmtree(OUT, onerror=_rm_readonly)
    OUT.mkdir(parents=True)

    from app import app

    client = TestClient(app, raise_server_exceptions=False)
    paths = collect_get_paths(app)
    ok, fail = 0, []
    for path in paths:
        try:
            good, msg = export_path(client, path)
            if good:
                ok += 1
            else:
                fail.append((path, msg))
        except Exception as ex:
            fail.append((path, str(ex)))

    # Alias 301 pages (small HTML refresh)
    for src, dest in ALIAS_REDIRECTS.items():
        p = OUT / src.strip("/").replace("/", "_") / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={dest}">'
            f'<link rel="canonical" href="{dest}"></head>'
            f'<body><p><a href="{dest}">ไปยัง {dest}</a></p></body></html>',
            encoding="utf-8",
        )
        ok += 1

    # Thai path alias folder
    thai = OUT / "เพิ่มผู้ติดตาม" / "index.html"
    thai.parent.mkdir(parents=True, exist_ok=True)
    thai.write_text(
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=/add-followers">'
        '</head><body><a href="/add-followers">add-followers</a></body></html>',
        encoding="utf-8",
    )
    ok += 1

    # Blog posts
    try:
        from cms import q_all
        from blog_content import post_href

        for post in q_all("SELECT slug FROM blog WHERE COALESCE(published,1)=1 ORDER BY id DESC LIMIT 80"):
            href = post_href(post)
            r = client.get(href, follow_redirects=True)
            if r.status_code != 200:
                continue
            slug = (post.get("slug") or "").strip() or str(post.get("id"))
            dest = OUT / "blog" / slug / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            ok += 1
    except Exception as ex:
        fail.append(("blog/*", str(ex)))

    # CMS /p/ pages if any
    try:
        from cms import q_all as cms_all

        for row in cms_all("SELECT slug FROM pages WHERE COALESCE(published,1)=1 LIMIT 40"):
            slug = (row.get("slug") or "").strip()
            if not slug:
                continue
            href = f"/p/{slug}"
            r = client.get(href, follow_redirects=True)
            if r.status_code != 200:
                continue
            dest = OUT / "p" / slug / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            ok += 1
    except Exception:
        pass

    # Static trees
    shutil.copytree(ROOT / "static" / "css", OUT / "css")
    shutil.copytree(ROOT / "static" / "assets", OUT / "assets")
    js_dir = OUT / "static" / "js"
    js_dir.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "static" / "js").glob("*.js"):
        shutil.copy2(f, js_dir / f.name)
    if (ROOT / "static" / "llms.txt").is_file():
        shutil.copy2(ROOT / "static" / "llms.txt", OUT / "llms.txt")

    # PHP bridge
    for name in ("la.php", "ping.php"):
        shutil.copy2(BRIDGE / name, OUT / name)
    backend = (os.environ.get("LA_BACKEND_URL") or os.environ.get("BACKEND_BASE") or "").strip().rstrip("/")
    site_host = os.environ.get("LA_SITE_HOST", "likes-auto.com")
    cfg = BRIDGE / "la-config.php"
    if backend:
        tpl = (
            "<?php\nreturn [\n"
            f"    'backend_base' => '{backend}',\n"
            f"    'backend_host' => '{site_host}',\n"
            "];\n"
        )
        (OUT / "la-config.php").write_text(tpl, encoding="utf-8")
    else:
        shutil.copy2(cfg, OUT / "la-config.php")

    (OUT / ".htaccess").write_text(HTACCESS, encoding="utf-8")
    print("exported", ok, "artifacts,", len(paths), "routes tried ->", OUT)
    if fail:
        print("skipped", len(fail), fail[:20])


if __name__ == "__main__":
    main()
