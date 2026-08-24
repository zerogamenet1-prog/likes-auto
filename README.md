# Likes Auto

เว็บปั้มไลค์และบริการโซเชียลมีเดีย — [likes-auto.com](https://likes-auto.com)

แอป **FastAPI + SQLite + Jinja2** รันด้วย Gunicorn บน VPS และเสิร์ฟผ่าน Nginx

แผนผังละเอียดอยู่ที่ [docs/structure.md](docs/structure.md)  
ขั้นตอนขึ้นเซิร์ฟเวอร์อยู่ที่ [docs/deploy.md](docs/deploy.md)

---

## หมวดไฟล์หลัก

| หมวด | ไฟล์ / โฟลเดอร์ | หน้าที่ |
|------|------------------|--------|
| จุดเข้าแอป | `app.py` | รวม router ทั้งหมด เปิดเว็บ |
| หน้าลูกค้า | `templates/*.html` | หน้าแรก บริการ บล็อก เติมเงิน บัญชี |
| แผงแอดมิน | `templates/admin/` | ออเดอร์ ลูกค้า บล็อก CMS ธีม |
| สไตล์ลูกค้า | `static/css/pages.css`, `responsive.css` | เลย์เอาต์มือถือและเดสก์ท็อป |
| สไตล์แอดมิน | `static/css/admin.css` | แดชบอร์ดแอดมิน |
| รูปเว็บ | `static/assets/` | โลโก้ แบนเนอร์ รูปบทความ |
| บทความบล็อก | `blog_content.py`, `blog_html.py`, `blog_posts.py`, `blog_posts_rest.py` | เนื้อหาต้นฉบับ + รูปประกอบ |
| SEO | `seo.py` | sitemap.xml, RSS, meta, JSON-LD |
| ร้านค้า / ออเดอร์ | `store.py`, `smm_api.py` | สินค้า ส่งออเดอร์ไปผู้ให้บริการ |
| เติมเงิน | `pay.py`, `inbound.py`, `slip_verify.py` | PromptPay, อัปโหลดสลิป |
| ผู้ใช้ | `db.py`, `google_oauth.py` | สมัคร ล็อกอิน cookie / Google |
| แอดมิน | `hub.py` | เส้นทาง `/admin/*` รวม CMS บล็อก |
| CMS บล็อก | `cms.py` | ตารางบทความ, seed, อัปโหลดรูป |
| Cron | `cron_jobs.py` | ออเดอร์ค้าง, เผยแพร่บล็อกคิวรายวัน |
| Deploy | `nginx-likes-auto.conf`, `docs/deploy.md` | Nginx และขั้นตอนขึ้นเซิร์ฟเวอร์ |

อย่า commit ไฟล์ `.env`, `sms.env`, หรือ `data/app.db` — เป็นข้อมูลจริงของลูกค้า

---

## โครงสร้างโฟลเดอร์

```
py-app/
├── app.py                 # FastAPI
├── templates/             # หน้า HTML ลูกค้า
│   ├── base.html
│   ├── home.html
│   ├── blog.html
│   ├── blog_post.html
│   └── admin/             # แผงแอดมิน
├── static/
│   ├── css/
│   ├── js/
│   └── assets/            # โลโก้ + รูปบล็อก blog-*.jpg
├── docs/
│   ├── structure.md       # แผนผังหมวดไฟล์
│   └── deploy.md
└── data/                  # SQLite (ไม่ขึ้น Git)
```

---

## รันบนเครื่องตัวเอง

ต้องมี Python 3.11+

```bash
cd py-app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app:app --reload --port 8787
```

เปิด http://127.0.0.1:8787

---

## หน้าสำคัญ

- ลูกค้า: `/` `/services` `/blog` `/addfunds` `/orders`
- แอดมิน: `/admin` `/admin/appearance/blog`
- SEO: `/sitemap.xml` `/rss.xml` `/robots.txt`

---

## บล็อกและ SEO

- บทความต้นฉบับอยู่ใน `blog_posts.py` และ `blog_posts_rest.py`
- รูปบทความอยู่ใน `static/assets/blog/` ชื่อขึ้นต้น `blog-`
- `seed_blog()` จะใส่บทที่ยังไม่มี และเติมรูปให้บทเก่าที่ยังไม่มี `<img>`
- บทที่ยังไม่เผยแพร่จะถูกปล่อยทีละบทผ่าน cron (`publish_next_blog`)
- แอดมินแก้บทจาก `/admin/appearance/blog` ได้โดยตรง (ไม่ควรถูก seed ทับถ้ามีรูปแล้ว)

---

## เติมเงิน

ระบบรับสลิปโอนจริงและ QR PromptPay  
**ไม่** เติมเครดิตจากยอดที่พิมพ์ใน QR โดยไม่ผ่านธนาคาร

---

## Deploy

ดู [docs/deploy.md](docs/deploy.md)
