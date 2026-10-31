"""Export public HTML + static assets for Apache/public_html hosting."""
import re
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist" / "hosting-static"

PATHS = [
    "/",
    "/services",
    "/pum-like",
    "/pum-follow",
    "/pum-view",
    "/smm-panel",
    "/add-followers",
    "/thai-likes",
    "/instagram",
    "/tiktok",
    "/youtube",
    "/facebook",
    "/telegram",
    "/spotify",
    "/shopee",
    "/twitter",
    "/faq",
    "/terms",
    "/api",
    "/blog",
    "/site-map",
    "/signup",
    "/signin",
    "/robots.txt",
    "/llms.txt",
    "/sitemap.xml",
    "/sitemap-pages.xml",
    "/sitemap-platforms.xml",
    "/manifest.webmanifest",
    "/health",
]

HTACCESS = """RewriteEngine On
RewriteBase /
# Serve existing files/dirs
RewriteCond %{REQUEST_FILENAME} -f [OR]
RewriteCond %{REQUEST_FILENAME} -d
RewriteRule ^ - [L]
# /path -> /path/index.html
RewriteCond %{DOCUMENT_ROOT}%{REQUEST_URI}/index.html -f
RewriteRule ^(.+?)/?$ $1/index.html [L]
DirectoryIndex index.html
"""


def dest_for(path: str) -> Path:
    if path == "/":
        return OUT / "index.html"
    if path.endswith(".xml") or path.endswith(".txt") or path.endswith(".webmanifest") or path == "/health":
        name = path.lstrip("/").replace("/", "_")
        return OUT / name
    clean = path.strip("/")
    return OUT / clean / "index.html"


def main():
    import shutil

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    from app import app

    client = TestClient(app, raise_server_exceptions=False)
    ok, fail = 0, []
    for path in PATHS:
        r = client.get(path, follow_redirects=True)
        if r.status_code != 200:
            fail.append((path, r.status_code))
            continue
        dest = dest_for(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = r.content
        if path == "/health" and body.startswith(b"{"):
            body = b'{"ok":true,"engine":"static-bridge"}'
        dest.write_bytes(body)
        ok += 1

    # Blog posts
    try:
        from cms import q_all
        from blog_content import post_href

        for post in q_all("SELECT slug FROM blog WHERE COALESCE(published,1)=1 ORDER BY id DESC LIMIT 40"):
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

    # Static trees
    shutil.copytree(ROOT / "static" / "css", OUT / "css")
    shutil.copytree(ROOT / "static" / "assets", OUT / "assets")
    js_dir = OUT / "static" / "js"
    js_dir.mkdir(parents=True)
    for f in (ROOT / "static" / "js").glob("*.js"):
        shutil.copy2(f, js_dir / f.name)

    (OUT / ".htaccess").write_text(HTACCESS, encoding="utf-8")
    print("exported", ok, "files to", OUT)
    if fail:
        print("skipped", fail[:15])


if __name__ == "__main__":
    main()
