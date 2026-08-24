# Deploy Likes Auto

เซิร์ฟเวอร์รันแอปที่ `/var/www/likes-auto`  
Nginx เป็น reverse proxy ไป Gunicorn (`likes-auto.service`)  
ผู้ใช้โปรเซส: `www-data`

## สิ่งที่ห้ามทับบนเซิร์ฟเวอร์

- `data/app.db` — ฐานลูกค้า ออเดอร์ บทความที่เผยแพร่แล้ว
- `.env` — คีย์และค่าคอนฟิกไลฟ์

## อัปไฟล์จาก Windows

อัปเฉพาะซอร์ส ข้าม `.venv`, `dist`, `__pycache__`, `data`  
แปลงไฟล์ที่เป็น UTF-16 ให้เป็น UTF-8 ก่อนอัป  
แล้ว `chown www-data` เฉพาะไฟล์ที่อัป และ `systemctl restart likes-auto`

## Nginx

ไฟล์ตัวอย่าง: `nginx-likes-auto.conf`  
โดเมนไลฟ์: `https://likes-auto.com`

## Cron

`likes-auto-cron.timer` ยิงประมาณทุก 2 นาที  
รัน `cron_jobs.py` รวมถึงคิวเผยแพร่บล็อกรายวัน (throttle ประมาณ 20 ชั่วโมงต่อบท)

## CSS cache

หน้าลูกค้า: `pages.css` + `responsive.css?v=...`  
แอดมิน: `admin.css?v=...`
