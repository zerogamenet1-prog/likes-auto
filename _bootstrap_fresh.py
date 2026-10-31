"""Create a fresh SQLite panel DB + local .env (gitignored)."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB = DATA / "app.db"
ENV = ROOT / ".env"


def main():
    os.environ.setdefault("ALLOW_DEMO_SEED", "1")
    if DB.exists():
        DB.unlink()
    DATA.mkdir(parents=True, exist_ok=True)

    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS") or secrets.token_urlsafe(10)
    session_secret = os.environ.get("SESSION_SECRET") or secrets.token_urlsafe(32)
    demo_user = os.environ.get("DEMO_CLIENT_USER", "demo")
    demo_pass = os.environ.get("DEMO_CLIENT_PASS") or "Demo1234!"

    os.environ["ADMIN_USER"] = admin_user
    os.environ["ADMIN_PASS"] = admin_pass
    os.environ["SESSION_SECRET"] = session_secret

    from db import create_client, init_db

    init_db()
    from blog_content import seed_blog

    seed_blog()

    user, err = create_client(demo_user, "demo@likes-auto.local", demo_pass)
    if err:
        print("demo client skip:", err)
    else:
        print("demo client:", demo_user)

    env_lines = [
        f"SESSION_SECRET={session_secret}",
        f"ADMIN_USER={admin_user}",
        f"ADMIN_PASS={admin_pass}",
        "ADMIN_SALT=likes-auto-py",
        "ALLOW_DEMO_SEED=1",
        f"DEMO_CLIENT_USER={demo_user}",
        f"DEMO_CLIENT_PASS={demo_pass}",
        "",
        "# LA_BACKEND_URL=https://your-app.onrender.com",
        "# Set before: python _export_hosting_static.py",
    ]
    ENV.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    cred = ROOT / "data" / "FRESH_SETUP_CREDENTIALS.txt"
    cred.write_text(
        "\n".join(
            [
                "LIKES AUTO — fresh install (keep secret, do not commit)",
                f"Admin URL: /admin/login/",
                f"Admin user: {admin_user}",
                f"Admin pass: {admin_pass}",
                f"Panel demo user: {demo_user}",
                f"Panel demo pass: {demo_pass}",
                f"DB: {DB}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("wrote", DB, DB.stat().st_size, "bytes")
    print("credentials ->", cred)


if __name__ == "__main__":
    main()
