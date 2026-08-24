import smtplib
from email.message import EmailMessage

from db import get_settings


def smtp_ready(settings=None):
    s = settings or get_settings()
    return bool((s.get("smtp_host") or "").strip() and (s.get("smtp_user") or "").strip())


def send_mail(to_addr, subject, body, settings=None):
    s = settings or get_settings()
    host = (s.get("smtp_host") or "").strip()
    user = (s.get("smtp_user") or "").strip()
    password = s.get("smtp_pass") or ""
    try:
        port = int(s.get("smtp_port") or 587)
    except (TypeError, ValueError):
        port = 587
    if not host or not to_addr:
        return False, "smtp_missing"
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user or ("noreply@" + host)
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.ehlo()
            try:
                server.starttls()
            except Exception:
                pass
        if user:
            server.login(user, password)
        server.send_message(msg)
        server.quit()
        return True, None
    except Exception as exc:
        return False, str(exc)
