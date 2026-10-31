# เปิดใช้ Likes Auto ครบ (หน้าเว็บ + ล็อกอิน + แอดมิน)

## 1. สร้างฐานข้อมูลใหม่ + อัปเว็บ Visperhost

```powershell
cd "...\py-app"
$env:HOST_PW = "รหัส FTP likesaut"
python _deploy_all.py
```

รหัสอยู่ใน `data/FRESH_SETUP_CREDENTIALS.txt` (อย่า commit)

## 2. Backend Python (Render — ฟรี)

1. Push โค้ด `py-app` ไป GitHub (repo `likes-auto`)
2. [Render](https://render.com) → **New** → **Blueprint** → เลือก repo → ใช้ `render.yaml`
3. ตั้ง **ADMIN_PASS** ใน Environment (Render จะ generate SESSION_SECRET)
4. รอ deploy แล้ว copy URL เช่น `https://likes-auto-xxxx.onrender.com`

## 3. เชื่อมโดเมนกับ backend

```powershell
$env:LA_BACKEND_URL = "https://likes-auto-xxxx.onrender.com"
python _export_hosting_static.py
python _deploy_ftp_visperhost.py
```

## 4. Cloudflare (โดเมนยังใช้ CF ได้)

- `@` และ `www` → **A `165.101.65.6`**, **DNS only (เมฆเทา)**
- Purge cache
- ทดสอบ `https://likes-auto.com/ping.php` และ `/health` ผ่าน POST ไม่จำเป็น

## 5. ทดสอบ

| หน้า | คาดหวัง |
|------|---------|
| `/` | หน้าแรก |
| `/signin/` | ฟอร์มล็อกอิน → demo user จาก credentials |
| `/admin/login/` | แอดมิน |

**หมายเหตุ:** Render free อาจ sleep — ครั้งแรกหลัง sleep รอ ~30–60 วินาที
