import io
import json
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from db import get_settings

API = "https://api.easyslip.com/v1/verify"


def _key():
    return str(get_settings().get("easyslip_key") or "").strip()


def ready():
    return bool(_key())


def _load(raw):
    try:
        data = json.loads(raw.decode("utf-8", "replace") if isinstance(raw, bytes) else (raw or "{}"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        return None, "fail"
    status = int(data.get("status") or 0)
    info = data.get("data") if isinstance(data.get("data"), dict) else None
    if status == 200 and info:
        return info, None
    msg = str(data.get("message") or data.get("error") or "fail")
    return None, msg


def _request(req):
    try:
        with urlopen(req, timeout=28) as resp:
            return _load(resp.read())
    except HTTPError as err:
        try:
            return _load(err.read())
        except Exception:
            return None, "fail"
    except (URLError, TimeoutError, OSError):
        return None, "timeout"


def verify_payload(payload):
    key = _key()
    text = str(payload or "").strip()
    if not key:
        return None, "no_key"
    if not (20 <= len(text) <= 255):
        return None, "bad_qr"
    q = urlencode({"payload": text, "checkDuplicate": "true"})
    req = Request(
        API + "?" + q,
        method="GET",
        headers={"Authorization": "Bearer " + key, "Accept": "application/json", "User-Agent": "likes-auto-pay/1.0"},
    )
    return _request(req)


def _jpeg_body(image_path):
    path = Path(image_path)
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return None, "file_type"
    mime = "image/jpeg"
    name = "slip.jpg"
    if suffix == ".png":
        mime = "image/png"
        name = "slip.png"
    elif suffix == ".webp":
        mime = "image/webp"
        name = "slip.webp"
    if len(raw) > 3_500_000 or suffix in {".png", ".webp", ".gif"}:
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(raw))
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")
            im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=82, optimize=True)
            raw = buf.getvalue()
            mime = "image/jpeg"
            name = "slip.jpg"
        except Exception:
            pass
    if len(raw) > 4_000_000:
        return None, "file_size"
    return raw, mime, name


def verify_image(image_path):
    key = _key()
    if not key:
        return None, "no_key"
    packed = _jpeg_body(image_path)
    if not packed or packed[0] is None:
        return None, packed[1] if packed else "file_bad"
    raw, mime, name = packed
    boundary = "----likesauto" + uuid.uuid4().hex
    head = (
        "--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
        "Content-Type: %s\r\n\r\n"
    ) % (boundary, name, mime)
    body = head.encode("ascii") + raw + ("\r\n--%s--\r\n" % boundary).encode("ascii")
    req = Request(
        API,
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Accept": "application/json",
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "User-Agent": "likes-auto-pay/1.0",
        },
    )
    return _request(req)
