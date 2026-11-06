"""
Updates Data Provider for Likes Auto
Supplies curated, high-converting service updates (Price Drops, New Services, Speed Boosts, Thai Services)
with full Google SEO Schema support.
"""

from typing import Dict, List, Any

# Curated list of service updates
UPDATES_LIST = [
    {
        "id": 104,
        "date": "2026-11-04",
        "date_th": "4 พ.ย. 2026",
        "platform": "TikTok",
        "plat_icon": "ri-tiktok-fill",
        "plat_color": "#25f4ee",
        "name": "ปั้มไลค์ TikTok คนไทยแท้ 100% บัญชีมีโปรไฟล์ มีตัวตน ไม่ลด",
        "type": "price_down",
        "type_label": "ปรับลดราคา",
        "badge_class": "badge-price-drop",
        "badge_icon": "ri-price-tag-3-line",
        "old_rate": 12.00,
        "new_rate": 8.74,
        "discount_pct": "-27%",
        "min_qty": 50,
        "max_qty": 50000,
        "speed": "10,000 - 30,000 / วัน",
        "refill": "รับประกัน 30 วัน",
        "note": "ปรับลดเรทลง 27% สำหรับแคมเปญกระตุ้นอัลกอริทึม TikTok ส่งยอดไวใน 1-3 นาที",
        "is_thai": True,
    },
    {
        "id": 108,
        "date": "2026-11-04",
        "date_th": "4 พ.ย. 2026",
        "platform": "TikTok",
        "plat_icon": "ri-tiktok-fill",
        "plat_color": "#25f4ee",
        "name": "ปั้มวิว TikTok วิดีโอสั้น / ไวรัลคลิป ปลดล็อกฟีด สำหรับผู้ใช้งานใหม่",
        "type": "new",
        "type_label": "บริการมาใหม่",
        "badge_class": "badge-new",
        "badge_icon": "ri-sparkling-fill",
        "old_rate": None,
        "new_rate": 0.38,
        "discount_pct": "เปิดตัวใหม่",
        "min_qty": 100,
        "max_qty": 10000000,
        "speed": "1,000,000 / วัน",
        "refill": "ไม่ลด ไม่ตก",
        "note": "เซิร์ฟเวอร์เปิดใหม่ ส่งยอดเร็วพิเศษ เริ่มต้นทันทีหลังวางลิงก์ เหมาะสำหรับดันคลิปเข้าฟีด For You",
        "is_thai": False,
    },
    {
        "id": 201,
        "date": "2026-11-03",
        "date_th": "3 พ.ย. 2026",
        "platform": "Instagram",
        "plat_icon": "ri-instagram-line",
        "plat_color": "#f43f5e",
        "name": "ปั้มผู้ติดตาม Instagram (IG) คนไทยแท้ 100% มีรูปโปรไฟล์ มีสตอรี่",
        "type": "price_down",
        "type_label": "ปรับลดราคา",
        "badge_class": "badge-price-drop",
        "badge_icon": "ri-price-tag-3-line",
        "old_rate": 19.50,
        "new_rate": 14.03,
        "discount_pct": "-28%",
        "min_qty": 50,
        "max_qty": 20000,
        "speed": "2,000 - 5,000 / วัน",
        "refill": "รับประกัน 30 วัน",
        "note": "ปรับลดราคาลง 28% คัดเฉพาะบัญชีผู้ใช้งานคนไทยแท้ เพิ่มความน่าเชื่อถือให้โปรไฟล์ร้านค้า",
        "is_thai": True,
    },
    {
        "id": 205,
        "date": "2026-11-03",
        "date_th": "3 พ.ย. 2026",
        "platform": "Instagram",
        "plat_icon": "ri-instagram-line",
        "plat_color": "#f43f5e",
        "name": "ปั้มวิว IG Reels & วิดีโอ ยอดขึ้นทันที อัตราการดูจบสูง (High Retention)",
        "type": "speed_up",
        "type_label": "เพิ่มความเร็ว",
        "badge_class": "badge-speed-up",
        "badge_icon": "ri-flashlight-line",
        "old_rate": 1.20,
        "new_rate": 0.85,
        "discount_pct": "เร็วขึ้น 2 เท่า",
        "min_qty": 100,
        "max_qty": 5000000,
        "speed": "500,000 / วัน",
        "refill": "ยอดถาวร",
        "note": "อัปเกรดเซิร์ฟเวอร์ระบบ Reels Direct ส่งยอดเร็วกว่าเดิม 2 เท่า ช่วยเพิ่มโอกาสขึ้นหน้า Explore",
        "is_thai": False,
    },
    {
        "id": 302,
        "date": "2026-11-02",
        "date_th": "2 พ.ย. 2026",
        "platform": "Facebook",
        "plat_icon": "ri-facebook-circle-fill",
        "plat_color": "#3b82f6",
        "name": "ปั้มไลค์โพสต์ Facebook คนไทยแท้ 100% บัญชีมีตัวตนจริง สลับอิโมจิได้",
        "type": "price_down",
        "type_label": "ปรับลดราคา",
        "badge_class": "badge-price-drop",
        "badge_icon": "ri-price-tag-3-line",
        "old_rate": 12.00,
        "new_rate": 8.74,
        "discount_pct": "-27%",
        "min_qty": 50,
        "max_qty": 50000,
        "speed": "5,000 - 15,000 / วัน",
        "refill": "ปลอดภัย 100%",
        "note": "เรทพิเศษสำหรับเพจและพ่อค้าแม่ค้าออนไลน์ ยอดไลค์คนไทยแท้ ช่วยเปิดการมองเห็นโพสต์และไลฟ์",
        "is_thai": True,
    },
    {
        "id": 315,
        "date": "2026-11-02",
        "date_th": "2 พ.ย. 2026",
        "platform": "Facebook",
        "plat_icon": "ri-facebook-circle-fill",
        "plat_color": "#3b82f6",
        "name": "ปั้มผู้ติดตามเพจ Facebook (Page Followers) คนไทยแท้ มีตัวตน",
        "type": "new",
        "type_label": "บริการมาใหม่",
        "badge_class": "badge-new",
        "badge_icon": "ri-sparkling-fill",
        "old_rate": None,
        "new_rate": 45.00,
        "discount_pct": "มาใหม่",
        "min_qty": 50,
        "max_qty": 20000,
        "speed": "1,000 - 3,000 / วัน",
        "refill": "รับประกัน 60 วัน",
        "note": "บริการเปิดใหม่สำหรับเพจธุรกิจและอินฟลูเอนเซอร์ คนไทยแท้กดติดตาม เพิ่มความน่าเชื่อถือสูงสุด",
        "is_thai": True,
    },
    {
        "id": 401,
        "date": "2026-11-01",
        "date_th": "1 พ.ย. 2026",
        "platform": "YouTube",
        "plat_icon": "ri-youtube-fill",
        "plat_color": "#ef4444",
        "name": "ปั้มวิว YouTube คลิปปกติ และ Shorts ดูจบ 100% เพิ่มชั่วโมงรับชม",
        "type": "price_down",
        "type_label": "ปรับลดราคา",
        "badge_class": "badge-price-drop",
        "badge_icon": "ri-price-tag-3-line",
        "old_rate": 22.00,
        "new_rate": 16.92,
        "discount_pct": "-23%",
        "min_qty": 100,
        "max_qty": 1000000,
        "speed": "20,000 - 50,000 / วัน",
        "refill": "รับประกัน 30 วัน",
        "note": "ปรับลดเรทลง 23% ยอดวิวคุณภาพสูง แหล่งที่มา Suggest Video / Browse Features ปลอดภัยต่อช่อง",
        "is_thai": False,
    },
    {
        "id": 408,
        "date": "2026-11-01",
        "date_th": "1 พ.ย. 2026",
        "platform": "YouTube",
        "plat_icon": "ri-youtube-fill",
        "plat_color": "#ef4444",
        "name": "ปั้ม 4,000 ชั่วโมง YouTube สำหรับเปิดสร้างรายได้ (Monetization Pack)",
        "type": "new",
        "type_label": "บริการมาใหม่",
        "badge_class": "badge-new",
        "badge_icon": "ri-sparkling-fill",
        "old_rate": None,
        "new_rate": 399.00,
        "discount_pct": "แพ็กเกจพิเศษ",
        "min_qty": 500,
        "max_qty": 4000,
        "speed": "200 - 500 ชม. / วัน",
        "refill": "รับประกันผ่านเกณฑ์",
        "note": "บริการยอดฮิตสำหรับครีเอเตอร์ที่ต้องการเปิดสร้างรายได้ YouTube Partner Program ส่งยอดชั่วโมงครบถ้วน",
        "is_thai": False,
    },
    {
        "id": 502,
        "date": "2026-10-31",
        "date_th": "31 ต.ค. 2026",
        "platform": "Twitter / X",
        "plat_icon": "ri-twitter-x-fill",
        "plat_color": "#94a3b8",
        "name": "ปั้มรีทวีต X (Twitter) และบุ๊กมาร์ก ช่วยดันเทรนด์ทวิตเตอร์ไทยแลนด์",
        "type": "speed_up",
        "type_label": "เพิ่มความเร็ว",
        "badge_class": "badge-speed-up",
        "badge_icon": "ri-flashlight-line",
        "old_rate": 18.00,
        "new_rate": 12.50,
        "discount_pct": "เร็วขึ้น 3 เท่า",
        "min_qty": 50,
        "max_qty": 20000,
        "speed": "10,000 / วัน",
        "refill": "ไม่ลด",
        "note": "ปรับปรุงระบบรีทวีตส่งไวใน 1-2 นาที เหมาะสำหรับแคมเปญปั่นเทรนด์ X ให้ติดกระแส",
        "is_thai": True,
    },
    {
        "id": 601,
        "date": "2026-10-30",
        "date_th": "30 ต.ค. 2026",
        "platform": "Shopee",
        "plat_icon": "ri-shopping-bag-2-line",
        "plat_color": "#fb923c",
        "name": "ปั้มผู้ติดตามร้านค้า Shopee คนไทยแท้ เพิ่มความน่าเชื่อถือให้ร้านค้าใหม่",
        "type": "new",
        "type_label": "บริการมาใหม่",
        "badge_class": "badge-new",
        "badge_icon": "ri-sparkling-fill",
        "old_rate": None,
        "new_rate": 49.00,
        "discount_pct": "บริการใหม่",
        "min_qty": 50,
        "max_qty": 10000,
        "speed": "500 - 1,500 / วัน",
        "refill": "รับประกัน 30 วัน",
        "note": "ช่วยเพิ่มผู้ติดตามร้านค้า Shopee ร้านดูน่าเชื่อถือ ลูกค้าตัดสินใจซื้อง่ายขึ้นอย่างเห็นได้ชัด",
        "is_thai": True,
    },
    {
        "id": 701,
        "date": "2026-10-29",
        "date_th": "29 ต.ค. 2026",
        "platform": "Telegram",
        "plat_icon": "ri-telegram-fill",
        "plat_color": "#38bdf8",
        "name": "ปั้มสมาชิกกลุ่ม / แชนแนล Telegram สมาชิกแอ็กทีฟ มีโพสต์ มีตัวตน",
        "type": "price_down",
        "type_label": "ปรับลดราคา",
        "badge_class": "badge-price-drop",
        "badge_icon": "ri-price-tag-3-line",
        "old_rate": 35.00,
        "new_rate": 24.50,
        "discount_pct": "-30%",
        "min_qty": 100,
        "max_qty": 50000,
        "speed": "5,000 / วัน",
        "refill": "รับประกัน 30 วัน",
        "note": "ปรับลดราคา 30% สำหรับกลุ่มเทรดเดอร์ นักลงทุน และแบรนด์ที่ต้องการสร้างคอมมูนิตี้",
        "is_thai": False,
    },
    {
        "id": 115,
        "date": "2026-10-28",
        "date_th": "28 ต.ค. 2026",
        "platform": "TikTok",
        "plat_icon": "ri-tiktok-fill",
        "plat_color": "#25f4ee",
        "name": "ปั้มผู้ติดตาม TikTok คนไทยแท้ 100% เปิดตะกร้า TikTok Shop ได้ทันที",
        "type": "price_down",
        "type_label": "ปรับลดราคา",
        "badge_class": "badge-price-drop",
        "badge_icon": "ri-price-tag-3-line",
        "old_rate": 65.00,
        "new_rate": 48.00,
        "discount_pct": "-26%",
        "min_qty": 50,
        "max_qty": 20000,
        "speed": "1,000 - 3,000 / วัน",
        "refill": "รับประกัน 30 วัน",
        "note": "ยอดนิยมสำหรับผู้ที่ต้องการครบ 1,000 ผู้ติดตามเพื่อเปิดตะกร้า TikTok Shop และไลฟ์สด",
        "is_thai": True,
    }
]

# FAQ for Google SEO & Schema.org FAQPage
UPDATES_FAQS = [
    {
        "q": "บริการที่ประกาศปรับลดราคา สมาชิกทุกคนได้ราคานี้เลยหรือไม่?",
        "a": "ใช่ครับ ทุกบริการที่ระบุว่าปรับลดราคาในหน้านี้ จะมีผลกับสมาชิกทุกคนทันที ทั้งลูกค้ารายย่อยและผู้ใช้งานผ่าน API โดยราคาต่อ 1,000 หน่วยในระบบจะปรับลดลงโดยอัตโนมัติ ไม่ต้องกรอกโค้ดส่วนลดใดๆ เพิ่มเติม"
    },
    {
        "q": "Likes Auto มีการอัปเดตบริการและราคาบ่อยแค่ไหน?",
        "a": "เรามีการตรวจสอบประสิทธิภาพและความเร็วของเซิร์ฟเวอร์ทุกวัน หากมีบริการใหม่ที่มีคุณภาพสูงกว่าหรือผู้ให้บริการปรับลดต้นทุน เราจะนำมาอัปเดตบนหน้านี้ทันทีเฉลี่ยสัปดาห์ละ 2-4 ครั้ง เพื่อให้ลูกค้าได้เรทที่คุ้มค่าที่สุดในไทย"
    },
    {
        "q": "บริการที่มีป้าย 'บริการมาใหม่' มีการรับประกันยอดหรือไม่?",
        "a": "บริการใหม่ทุกรายการผ่านการทดสอบเสถียรภาพและคุณภาพก่อนเปิดให้สั่งซื้อจริง หากบริการใดมีระบุ 'รับประกัน 30 วัน' หรือ 'รับประกัน 60 วัน' หากยอดมีการลดลง สามารถกดขอรีฟิล (เติมยอดฟรี) ในระบบได้ตลอด 24 ชั่วโมง"
    },
    {
        "q": "หากเชื่อมต่อผ่าน API จะได้รับบริการใหม่และเรทลดราคานี้อัตโนมัติหรือไม่?",
        "a": "ผู้ที่เชื่อมต่อผ่าน API สามารถดึงรายการบริการผ่าน Endpoint `/api/v2?action=services` ได้ทันที โดยระบบจะส่งรหัส Service ID, ชื่อบริการ และเรทราคาใหม่ล่าสุดให้โดยอัตโนมัติ"
    },
    {
        "q": "ต้องการให้เพิ่มบริการเฉพาะทาง สามารถแจ้งขอได้ทางไหน?",
        "a": "ลูกค้าและตัวแทนจำหน่ายสามารถเปิดตั๋วช่วยเหลือ (Ticket) หรือติดต่อแอดมินผ่าน Line Support ได้ตลอด 24 ชั่วโมง ทีมงานพร้อมจัดหาบริการที่ตรงกับความต้องการของธุรกิจคุณครับ"
    }
]


def get_updates_data(update_type: str = "", platform: str = "", q: str = "") -> Dict[str, Any]:
    """Filters updates and calculates metrics."""
    typ = (update_type or "").strip().lower()
    plat = (platform or "").strip().lower()
    query = (q or "").strip().lower()

    filtered = []
    for item in UPDATES_LIST:
        # Match type filter
        if typ and typ != "all":
            if typ == "thai" and not item["is_thai"]:
                continue
            elif typ != "thai" and item["type"] != typ:
                continue

        # Match platform filter
        if plat and plat != "all":
            if plat not in item["platform"].lower():
                continue

        # Match text search
        if query:
            needle_match = (
                query in str(item["id"])
                or query in item["name"].lower()
                or query in item["platform"].lower()
                or query in item["note"].lower()
            )
            if not needle_match:
                continue

        filtered.append(item)

    # Compute platform counts
    platforms = [
        {"name": "ทั้งหมด", "slug": "all", "count": len(UPDATES_LIST)},
        {"name": "TikTok", "slug": "tiktok", "count": sum(1 for x in UPDATES_LIST if "tiktok" in x["platform"].lower())},
        {"name": "Instagram", "slug": "instagram", "count": sum(1 for x in UPDATES_LIST if "instagram" in x["platform"].lower())},
        {"name": "Facebook", "slug": "facebook", "count": sum(1 for x in UPDATES_LIST if "facebook" in x["platform"].lower())},
        {"name": "YouTube", "slug": "youtube", "count": sum(1 for x in UPDATES_LIST if "youtube" in x["platform"].lower())},
        {"name": "Twitter / X", "slug": "twitter", "count": sum(1 for x in UPDATES_LIST if "twitter" in x["platform"].lower())},
        {"name": "Shopee", "slug": "shopee", "count": sum(1 for x in UPDATES_LIST if "shopee" in x["platform"].lower())},
        {"name": "Telegram", "slug": "telegram", "count": sum(1 for x in UPDATES_LIST if "telegram" in x["platform"].lower())},
    ]

    # Metrics
    total_count = len(UPDATES_LIST)
    price_drops = sum(1 for x in UPDATES_LIST if x["type"] == "price_down")
    new_services = sum(1 for x in UPDATES_LIST if x["type"] == "new")
    speed_boosts = sum(1 for x in UPDATES_LIST if x["type"] == "speed_up")
    thai_services = sum(1 for x in UPDATES_LIST if x["is_thai"])

    return {
        "updates": filtered,
        "all_updates": UPDATES_LIST,
        "total_count": total_count,
        "price_drops": price_drops,
        "new_services": new_services,
        "speed_boosts": speed_boosts,
        "thai_services": thai_services,
        "active_type": typ or "all",
        "active_plat": plat or "all",
        "search_query": query,
        "platforms": platforms,
        "faqs": UPDATES_FAQS,
    }

