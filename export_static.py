from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from content import COPY, FAQ, SERVICES, SITE

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "cf-pages"

PAGES = {
    "index.html": ("home.html", "home"),
    "services/index.html": ("services.html", "services"),
    "signup/index.html": ("signup.html", "signup"),
    "signin/index.html": ("signin.html", "signin"),
    "faq/index.html": ("faq.html", "faq"),
    "terms/index.html": ("terms.html", "terms"),
    "api/index.html": ("api.html", "api"),
}


def main():
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    import shutil

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    css_src = ROOT / "static" / "css"
    assets_src = ROOT / "static" / "assets"
    shutil.copytree(css_src, OUT / "css")
    shutil.copytree(assets_src, OUT / "assets")

    for dest, (template, name) in PAGES.items():
        html = env.get_template(template).render(site=SITE, t=COPY, page=name, faq=FAQ, services=SERVICES)
        path = OUT / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        print("wrote", path)

    print("export ok", OUT)


if __name__ == "__main__":
    main()
