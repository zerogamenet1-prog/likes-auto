# แผนผังโปรเจกต์ Likes Auto

อ่านไฟล์นี้เมื่ออยากรู้ว่าของอยู่หมวดไหน โดยไม่ต้องไล่ทั้งโฟลเดอร์

## 1. เว็บลูกค้า

| ไฟล์ | หน้า |
|------|------|
| templates/home.html | หน้าแรก |
| templates/services.html | รายการบริการ |
| templates/neworder.html | สั่งซื้อ |
| templates/orders.html | ออเดอร์ของฉัน |
| templates/addfunds.html | เติมเงิน |
| templates/blog.html | รายการบทความ |
| templates/blog_post.html | อ่านบทความ |
| templates/signin.html / signup.html | เข้าสู่ระบบ / สมัคร |
| templates/account.html | บัญชี |
| templates/tickets.html | ตั๋วซัพพอร์ต |
| templates/faq.html / terms.html | คำถามและข้อตกลง |
| static/css/pages.css | สไตล์หลัก |
| static/css/responsive.css | มือถือ |

เลย์เอาต์รวมอยู่ที่ templates/base.html

## 2. แผงแอดมิน

เส้นทาง /admin/* อยู่ใน hub.py
เลย์เอาต์ templates/admin/base.html + static/css/admin.css

| ไฟล์ | หน้าที่ |
|------|--------|
| templates/admin/dashboard.html | ภาพรวม |
| templates/admin/orders.html | ออเดอร์ |
| templates/admin/clients.html | ลูกค้า |
| templates/admin/payments.html | เติมเงิน / สลิป |
| templates/admin/services.html | สินค้า |
| templates/admin/blog.html | CMS บล็อก (เขียน แก้ รูป เผยแพร่) |
| templates/admin/appear_hub.html | รูปลักษณ์เว็บ |
| templates/admin/settings.html | ตั้งค่า |
| templates/admin/providers.html | ผู้ให้บริการ SMM |
| templates/admin/tickets.html | ตั๋วลูกค้า |

## 3. บล็อกและ SEO

| ไฟล์ | หน้าที่ |
|------|--------|
| blog_posts.py | บทความชุดแรก |
| blog_posts_rest.py | บทความชุดที่เหลือ |
| blog_html.py | โครง HTML + แทรกรูป |
| blog_content.py | รวมบทและแท็ก |
| cms.py | ตารางบทความ, seed, อัปโหลดรูป |
| seo.py | sitemap, RSS, meta, JSON-LD |
| static/assets/blog/ | รูป JPEG ชื่อ blog-*.jpg |

แอดมินแก้บทจาก /admin/appearance/blog
บทที่ยังไม่เผยแพร่จะถูกปล่อยทีละบทผ่าน cron

## 4. เงิน ออเดอร์ API

| ไฟล์ | หน้าที่ |
|------|--------|
| pay.py | เติมเงิน PromptPay / สลิป |
| inbound.py | webhook เข้า |
| easyslip.py / oiio_slip.py / slip_verify.py | ตรวจสลิป |
| store.py | ออเดอร์ในระบบ |
| smm_api.py | ส่งงานไปผู้ให้บริการ |
| panel.py / api_v2.py | API ลูกค้า |
| th_shop.py | แคตตาล็อกไทย |

ระบบเติมเครดิตจากสลิปโอนจริงเท่านั้น ไม่ใช้ยอดที่พิมพ์ใน QR

## 5. บัญชี เมล Cron

| ไฟล์ | หน้าที่ |
|------|--------|
| db.py | SQLite, ผู้ใช้แอดมินเริ่มต้น |
| google_oauth.py | เข้าสู่ระบบ Google |
| mail.py | อีเมล |
| cron_jobs.py | ออเดอร์ค้าง + เผยแพร่บล็อกรายวัน |
| theme.py / content.py | ธีมและข้อความหน้าเว็บ |
| more.py | หน้าเสริม |

## 6. ของที่ไม่มีใน Git

- .env / sms.env — ความลับ
- data/ — ฐานข้อมูลไลฟ์
- .venv/ / dist/ / __pycache__/
- static/uploads/ — ไฟล์ที่ผู้ใช้อัปเอง
