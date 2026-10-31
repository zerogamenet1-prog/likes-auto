"""Upload dist/hosting-static to Visperhost public_html via FTP."""
import os
from ftplib import FTP
from pathlib import Path

HOST = os.environ.get("FTP_HOST", "165.101.65.6")
USER = os.environ.get("FTP_USER", "likesaut")
PW = os.environ.get("HOST_PW") or os.environ.get("FTP_PW")
REMOTE = os.environ.get("FTP_REMOTE", "domains/likes-auto.com/public_html")

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / "dist" / "hosting-static"


def _mkd(ftp: FTP, path: str):
    if not path or path == "/":
        return
    parts = path.replace("\\", "/").strip("/").split("/")
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            ftp.mkd(cur)
        except Exception:
            pass


def main():
    if not PW:
        raise SystemExit("missing HOST_PW or FTP_PW")
    if not LOCAL.is_dir():
        raise SystemExit("run _export_hosting_static.py first")

    ftp = FTP()
    ftp.connect(HOST, 21, timeout=120)
    ftp.login(USER, PW)
    base = "/" + REMOTE.strip("/")
    _mkd(ftp, base)
    count = 0
    for path in sorted(LOCAL.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(LOCAL).as_posix()
        remote_path = base + "/" + rel
        remote_dir = remote_path.rsplit("/", 1)[0]
        _mkd(ftp, remote_dir)
        with path.open("rb") as f:
            ftp.storbinary("STOR " + remote_path, f)
        count += 1
        if count <= 30 or count % 50 == 0:
            print("up", rel, path.stat().st_size)
    ftp.quit()
    print("done", count, "files ->", base)


if __name__ == "__main__":
    main()
