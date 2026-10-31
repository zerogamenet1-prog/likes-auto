# ย้ายไป Visperhost (DirectAdmin)

ข้อมูลจากโฮสต์ (อัปเดตเมื่อได้รับเมลเปิดบัญชี):

| รายการ | ค่า |
|--------|-----|
| Panel | https://thsv01.visperhost.net:2222 หรือ https://likes-auto.com:2222 (หลัง DNS พร้อม) |
| ผู้ใช้ | `likesaut` |
| IP | `165.101.65.6` |
| NS | `th01.visperhost.net`, `th02.visperhost.net` |

**อย่าเก็บรหัสผ่าน panel ใน Git หรือในแชท** — ใส่เฉพาะใน `.env` / ตัวแปร session บนเครื่องคุณ

---

## สำคัญ: แอป Likes Auto ไม่ใช่เว็บ PHP ธรรมดา

โปรเจกต์นี้คือ **FastAPI + Gunicorn + SQLite + cron** (เดิมรันบน VPS ที่ `/var/www/likes-auto`)

โฮสต์แบบ DirectAdmin บางแพ็ก **ไม่รองรับ Python app แบบนี้** หรือ **ไม่เปิด SSH (พอร์ต 22)** — ต้องเช็กกับ Visperhost ก่อนว่าแพ็กของคุณมี:

- SSH / SFTP (มักต้องเปิดใน panel)
- Python 3.11+ และรัน process ถาวร (หรือ Passenger / Setup Python App)
- Reverse proxy จาก Apache/Nginx ไปพอร์ตแอป (เช่น 8000)

ถ้าไม่มี — ต้อง **อัปเกรดเป็น VPS** ที่ Visperhost หรือ **ใช้เซิร์ฟเวอร์เดิม** จนกว่าจะย้าย DB และ `.env` ได้ครบ

---

## DNS (โดเมนยังอยู่ Cloudflare อยู่ตอนนี้)

ตอนนี้ `likes-auto.com` ชี้ NS ไป **Cloudflare** ไม่ใช่ Visperhost

เลือกอย่างใดอย่างหนึ่ง:

### แบบ A — เก็บ Cloudflare (แนะนำถ้าใช้ CDN/WAF อยู่)

1. ที่ Cloudflare → DNS → แก้ **A record** `@` และ `www` เป็น **`165.101.65.6`**
2. ชั่วคราวตั้ง Proxy เป็น **DNS only (เมฆเทา)** จน SSL บนโฮสต์ใหม่พร้อม
3. **ไม่ต้อง** เปลี่ยน NS เป็น th01/th02

### แบบ B — ใช้ NS ของ Visperhost

1. ที่ registrar เปลี่ยน NS เป็น `th01.visperhost.net` และ `th02.visperhost.net`
2. รอ propagate (มัก 1–24 ชม.)
3. ตั้งค่าโดเมน/SSL ใน DirectAdmin

---

## ขั้นตอนย้ายจาก VPS เก่า (103.91.205.39)

1. **สำรองจากเซิร์ฟเวอร์เก่า** (ถ้ายังเข้าได้):
   - `data/app.db` — ลูกค้า ออเดอร์ บล็อก ตั้งค่า
   - `.env` — คีย์ลับ
2. **อัปโหลดโค้ด** — จาก GitHub `main` หรือรัน `_deploy_web_release.py` เมื่อ SSH/SFTP พร้อม
3. **วาง `data/` และ `.env`** บนโฮสต์ใหม่ (path ตามที่โฮสต์กำหนด มักใต้ `/home/likesaut/...`)
4. ติดตั้ง venv, `pip install -r requirements.txt`, ตั้ง Gunicorn + cron ตามที่โฮสต์อนุญาต
5. ทดสอบ `/health` แล้วค่อยสลับ DNS

โค้ดล่าสุดอยู่ที่ GitHub แล้ว — ยังไม่จำเป็นต้องรอ DNS ถึงจะเตรียมไฟล์บนโฮสต์ได้

---

## Deploy จาก Windows (เมื่อ SSH/SFTP เปิดแล้ว)

ตั้งตัวแปร (PowerShell):

```powershell
cd "...\py-app"
$env:VPS_PW = "รหัส SSH/SFTP ของ likesaut"
$env:DEPLOY_HOST = "165.101.65.6"
$env:DEPLOY_USER = "likesaut"
$env:DEPLOY_PORT = "22"
$env:DEPLOY_PATH = "/home/likesaut/domains/likes-auto.com/app"   # แก้ตาม path จริงใน panel
$env:DEPLOY_RESTART = ""   # ถ้าไม่มี systemctl ให้เว้นว่าง
python _deploy_web_release.py
```

ถ้า SFTP ไม่ขึ้น: ใน DirectAdmin → **SSH Keys** / **FTP** / ติดต่อ support ให้เปิด SSH

---

## หลังย้าย DNS

- https://likes-auto.com/health → `{"ok":true,...}`
- หน้า SEO: `/pum-like`, `/site-map`
- แอดมิน: `/admin`
- เปลี่ยนรหัส panel และรหัสแอดมินเว็บหลัง go-live
