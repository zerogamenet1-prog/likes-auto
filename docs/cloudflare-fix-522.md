# แก้ likes-auto.com ขึ้น 522 (ชี้มา Visperhost)

เว็บอัปขึ้นโฮสต์ **165.101.65.6** แล้ว (ทดสอบด้วย Host `likes-auto.com` ได้หน้าแรก 200)  
แต่โดเมนผ่าน **Cloudflare** ยังชี้ไปเซิร์ฟเวอร์เก่าที่ปิด → ขึ้น **522**

## ขั้นตอน (ทำครั้งเดียว)

1. เข้า [Cloudflare Dashboard](https://dash.cloudflare.com) → โดเมน **likes-auto.com**
2. เมนู **DNS** → **Records**
3. แก้ **A** ชื่อ `@` ให้เป็น **`165.101.65.6`**
4. แก้ **A** ชื่อ `www` ให้เป็น **`165.101.65.6`** (แนะนำใช้ **A record** โดยตรง — อย่าใช้ CNAME แบบเคยเปิด Proxy แล้วปิด เพราะบาง resolver ยังเห็น IP ของ Cloudflare ค้าง)
5. ตั้ง **Proxy status** ของ `@`, `www`, `ftp`, `name` เป็น **DNS only** (เมฆเทา) — **อย่าเปิดเมฆส้ม** บน Visperhost (ขึ้น **522**). ถ้า UI ขึ้นเมฆเทาแต่ DNS ยังเป็น 104.21.x ให้ **ลบ A record แล้วสร้างใหม่** (grey cloud) แล้วเช็กที่ `nslookup -type=A likes-auto.com carla.ns.cloudflare.com` ต้องได้ **165.101.65.6**
6. ออก **Let's Encrypt** ใน DirectAdmin แล้วใช้ **https://** ตรงจากโฮสต์ (กุญแจเขียว ไม่มีคำเตือนใบรับรอง)
7. รอ 2–10 นาที แล้วเปิด https://likes-auto.com/ และ https://www.likes-auto.com/
8. ถ้าเครื่องคุณยังเห็น **522** หรือ IP 104.21.x / 172.67.x ให้รัน `ipconfig /flushdns` (Windows) แล้วลองใหม่
9. ใน Cloudflare → **Caching** → **Purge Everything** (ล้าง cache 522 เก่า)

## SSL หลัง DNS ถูกแล้ว

ใน DirectAdmin → **ใบรับรอง SSL/TLS** → ออกใบรับรองฟรี (Let's Encrypt) สำหรับ `likes-auto.com`  
ใช้ **DNS only** ที่ Cloudflare — ไม่ต้องเปิด Proxy จนกว่าโฮสต์จะรองรับ IP ของ Cloudflare

## ทดสอบก่อนแก้ DNS (บน PC คุณ)

แก้ไฟล์ `C:\Windows\System32\drivers\etc\hosts` (Run as Admin):

```
165.101.65.6 likes-auto.com www.likes-auto.com
```

เปิด http://likes-auto.com/ ควรเห็นหน้า Likes Auto (เวอร์ชัน static)

## ข้อจำกัดชั่วคราว

ชุดที่อัปตอนนี้เป็น ** static HTML** (หน้าโชว์ + SEO + บล็อก) — **สมัคร / ล็อกอิน / สั่งซื้อ** ต้องรอรัน Python backend (ขอ SSH จาก Visperhost หรือ VPS)
