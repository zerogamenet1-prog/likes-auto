"""Bootstrap DB, export static, upload to Visperhost FTP."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    os.environ.setdefault("ALLOW_DEMO_SEED", "1")
    run([sys.executable, "_bootstrap_fresh.py"])
    run([sys.executable, "_export_hosting_static.py"])
    if not (os.environ.get("HOST_PW") or os.environ.get("FTP_PW")):
        print("skip FTP: set HOST_PW or FTP_PW")
        return
    run([sys.executable, "_deploy_ftp_visperhost.py"])
    backend = (os.environ.get("LA_BACKEND_URL") or "").strip()
    if backend:
        print("backend configured in la-config.php:", backend)
    else:
        print("WARN: LA_BACKEND_URL not set — login/admin POST will return 503 until backend is linked")


if __name__ == "__main__":
    main()
