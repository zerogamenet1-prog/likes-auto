def L(href, text):
    return '<a href="%s">%s</a>' % (href, text)


HOME = L("/", "ปั้มไลค์")
SVC = L("/services", "ราคาปั้มไลค์")
IG = L("/instagram", "ปั้มไลค์ Instagram")
TT = L("/tiktok", "ปั้มวิว TikTok")
FB = L("/facebook", "ปั้มไลค์ Facebook")
YT = L("/youtube", "เพิ่มยอดวิว YouTube")
FAQ = L("/faq", "ไม่ขอรหัสผ่าน")
SIGN = L("/signup", "สมัครฟรี")
API = L("/api", "API เปิดร้านต่อ")
HOW = L("/#howto", "วิธีใช้งาน")
PAY = L("/#pay", "พร้อมเพย์")
ADS = L("/blog/pump-likes-vs-ads", "ยิงแอด")
MKT = L("/blog/social-proof-marketing", "การตลาดออนไลน์")


def fig(name, alt, cap=""):
    key = (name or "likes").strip()
    if key.endswith(".jpg") or key.endswith(".png") or key.endswith(".webp"):
        fname = key.rsplit("/", 1)[-1]
    else:
        stem = key if key.startswith("blog-") else "blog-" + key
        fname = stem + ".jpg"
    cap_html = "<figcaption>%s</figcaption>" % cap if cap else ""
    return (
        '<figure class="la-blog-fig">'
        '<img src="/static/assets/blog/%s" alt="%s" width="1280" height="720" loading="lazy">'
        "%s</figure>"
    ) % (fname, alt, cap_html)


def h3(text):
    return "<h3>%s</h3>" % text


def p(text):
    return "<p>%s</p>" % text


def ul(items):
    return "<ul>" + "".join("<li>%s</li>" % x for x in items) + "</ul>"


def story(imgs, intro, sections, outro):
    parts = []
    if imgs:
        parts.append(fig(*imgs[0]))
    parts.extend(p(x) for x in intro)
    for i, sec in enumerate(sections):
        title, paras, bullets = sec[0], sec[1], (sec[2] if len(sec) > 2 else None)
        if imgs and i + 1 < len(imgs):
            parts.append(fig(*imgs[i + 1]))
        parts.append(h3(title))
        parts.extend(p(x) for x in paras)
        if bullets:
            parts.append(ul(bullets))
    parts.extend(p(x) for x in outro)
    return "".join(parts)


def know_proof():
    return (
        "โซเชียลพรูฟคือหลักการตลาดที่คนใช้พฤติกรรมของคนอื่นเป็นทางลัดในการตัดสินใจ "
        "เมื่อเห็นเพจมีไลค์ รีวิว หรือผู้ติดตาม สมองจะแปลว่าความเสี่ยงต่ำกว่าเพจว่าง "
        "ร้านใหม่ที่ลูกค้ายังไม่รู้จักจึงเสียเปรียบ แม้สินค้าจะดี เพราะข้อมูลที่ใช้ตัดสินมีน้อย "
        "ยอดในช่วงต้นจึงเป็นสัญญาณประกอบ ไม่ใช่การหลอกให้ซื้อของไม่ได้คุณภาพ"
    )


def know_algo():
    return (
        "แพลตฟอร์มโซเชียลไม่โชว์โพสต์ให้ทุกคนพร้อมกัน แต่สุ่มทดสอบกับกลุ่มเล็กก่อน "
        "ถ้ามีสัญญาณมีส่วนร่วม เช่น ไลค์ ดูจบ แชร์ หรือคอมเมนต์ ในช่วงชั่วโมงแรก ระบบมีโอกาสขยายวง "
        "นี่คือเหตุผลที่ร้านใช้%s เป็นตัวจุดไฟ ไม่ใช่การแทนที่แคปชัน รูปสินค้า และการตอบแชท" % HOME
    )


def know_funnel():
    return (
        "กรวยการตลาดมีชั้นรู้จัก สนใจ ไว้ใจ แล้วค่อยซื้อ "
        "ยอดไลค์ช่วยชั้นรู้จักและไว้ใจ ส่วน%s ช่วยดึงคนที่ยังไม่เคยเห็นเพจ "
        "ของจริง รีวิว และการตอบเร็วช่วยชั้นซื้อ ถ้าขาดชั้นใดชั้นหนึ่ง งบจะรั่วแม้ยอดบนจอจะดูดี" % ADS
    )


def know_safe():
    return (
        "แผงที่ปลอดภัยจะไม่ขอรหัสผ่านโซเชียล เพราะงานส่งไลค์ วิว หรือผู้ติดตามใช้ลิงก์สาธารณะได้ "
        "ใครขอรหัสเท่ากับได้สิทธิ์ทั้งบัญชี รวมถึงโฆษณา ข้อความลูกค้า และอีเมลกู้คืน "
        "Likes Auto ยึด%s เป็นหลัก สั่งเองจากแผงหลัง%s เติม%s ได้ทันที" % (FAQ, SIGN, PAY)
    )


def know_budget():
    return (
        "ร้านเล็กไม่ต้องเทงบโฆษณาทั้งก้อนก่อนมีโซเชียลพรูฟ "
        "แบ่งเป็นสามถังคือ คอนเทนต์ (รูป คลิป โปร) %s จำนวนทดลอง และ%s เมื่อเพจพร้อมรับแขก "
        "วัดผลจากคนทักและยอดขาย ไม่ใช่แค่ตัวเลขบนจอ" % (HOME, ADS)
    )


def know_content():
    return (
        "คอนเทนต์ที่ขายได้มักมีสามอย่างครบคือ ภาพชัด ข้อเสนอเข้าใจในสามวินาที และทางไปต่อ "
        "เช่น ลิงก์ไบโอ ตะกร้า หรือเบอร์คุย "
        "ยอดไลค์ช่วยให้คนหยุดดู แต่ถ้าภาพมัวหรือไม่บอกว่าขายอะไร คนก็เลื่อนผ่านเหมือนเดิม"
    )


DAILY_IMGS = {
    "ig": ["instagram", "likes", "plan", "brand"],
    "tt": ["tiktok", "live", "chart", "student"],
    "fb": ["facebook", "comments", "cafe", "funnel"],
    "yt": ["youtube", "chart", "plan", "student"],
    "x": ["comments", "ads", "plan", "likes"],
    "tg": ["comments", "team", "api", "plan"],
}


def daily_imgs_for(plat_name):
    if plat_name.startswith("Instagram"):
        names = DAILY_IMGS["ig"]
    elif plat_name.startswith("TikTok"):
        names = DAILY_IMGS["tt"]
    elif plat_name.startswith("Facebook"):
        names = DAILY_IMGS["fb"]
    elif plat_name.startswith("YouTube"):
        names = DAILY_IMGS["yt"]
    elif plat_name.startswith("X"):
        names = DAILY_IMGS["x"]
    elif plat_name.startswith("Telegram"):
        names = DAILY_IMGS["tg"]
    else:
        names = ["likes", "funnel", "plan", "order"]
    return names


def daily_story(niche, goal_name, plat_name, plat_link):
    names = daily_imgs_for(plat_name)
    imgs = [
        (names[0], "%s %s" % (plat_name, niche), "ภาพประกอบ %s สำหรับ%s" % (plat_name, niche)),
        (names[1], "โซเชียลพรูฟและการตลาด", "ยอดไลค์เป็นสัญญาณประกอบ ไม่ใช่การแทนที่สินค้า"),
        (names[2], "วางแผนคอนเทนต์", "แผนรายสัปดาห์ช่วยให้งบไม่กระจัดกระจาย"),
        (names[3], "สั่งงานจากแผง", "ใช้ลิงก์สาธารณะ ไม่ฝากรหัสผ่าน"),
    ]
    return story(
        imgs,
        [
            "คนทำ%s มักเจอปัญหาเดียวกันคือ ลงของดีแต่คนยังไม่กล้ากด เพราะเพจหรือคลิปดูเงียบเกินไป "
            "การ%s บน%s จึงถูกใช้เป็นเครื่องมือชั้นต้นของ%s ไม่ใช่ทางลัดเลี่ยงงานจริง" % (niche, goal_name, plat_name, MKT),
            know_proof(),
            know_algo(),
        ],
        [
            (
                "ทำความรู้จักลูกค้า%s ก่อนซื้อยอด" % niche,
                [
                    "ก่อนสั่ง%s ให้ตอบให้ได้ว่าลูกค้าคือใคร เขาค้นหาอะไร และโพสต์ชิ้นไหนคือตัวแทนร้าน "
                    "ถ้ายังไม่มีภาพสินค้าชัดหรือคลิปสั้นที่จบในแปดวินาที ยอดที่ซื้อมาจะช่วยได้น้อย" % plat_link,
                    know_content(),
                ],
                [
                    "เลือกโพสต์หรือคลิปที่ดีที่สุดชิ้นเดียวมาทดลองก่อน",
                    "เขียนแคปชันให้รู้ว่าขายอะไร ราคาประมาณ และให้ทักยังไง",
                    "อย่ากระจายงบไปสิบโพสต์จนแต่ละชิ้นไม่เห็นผล",
                ],
            ),
            (
                "วางจำนวนให้เข้ากับขนาดเพจ",
                [
                    know_budget(),
                    "เพจหรือช่องที่เพิ่งเปิด ควรเริ่มแพ็กเล็กจาก%s ดูว่ากราฟและการทักเป็นอย่างไร ค่อยเพิ่มรอบถัดไปดีกว่ากระชากทีเดียวแล้วหยุด" % SVC,
                ],
                [
                    "ใช้ Drip-feed ถ้าไม่อยากให้ยอดพุ่งก้อนเดียว",
                    "อย่าสั่งซ้ำลิงก์เดิมจนกว่าจะรู้ผลรอบแรก",
                    "เช็กลิงก์สาธารณะตาม%s ทุกครั้ง" % FAQ,
                ],
            ),
            (
                "ใช้คู่ยิงแอดเมื่อเพจพร้อม",
                [
                    know_funnel(),
                    "เมื่อหน้าตาเพจเริ่มมีชีวิต ค่อยใช้%s หาคนใหม่ คนที่คลิกโฆษณาแล้วเจอเพจว่าง มักเด้งออก งบต่อผลลัพธ์เลยแพงขึ้น" % ADS,
                ],
                [
                    "วัดจากคนทักและยอดขาย ไม่ใช่แค่ยอดไลค์",
                    "เก็บรีวิวลูกค้าจริงไว้ในไฮไลต์หรือเพลย์ลิสต์",
                    "ตอบแชทให้ทันภายในชั่วโมงทำการ",
                ],
            ),
            (
                "เริ่มจากแผงโดยไม่ฝากรหัส",
                [
                    know_safe(),
                    "ขั้นตอนสั้น ๆ คือ %s เลือกบริการ%s ใส่ลิงก์ กำหนดจำนวน แล้วส่งงาน ระบบ%s ทำงานต่อให้ทั้งวัน" % (SIGN, plat_link, HOW),
                ],
                [
                    "เติมเครดิต%s ไว้ล่วงหน้าถ้าลงคลิปดึก" % PAY,
                    "ร้านต่อเชื่อม%s ได้เมื่อมีลูกค้าประจำ" % API,
                    "ดูเรทล่าสุดที่%s" % SVC,
                ],
            ),
        ],
        [
            "สรุปแล้วการ%s สำหรับ%s บน%s คุ้มเมื่อทำคู่กับคอนเทนต์ชัดและการวัดผลที่เป็นยอดขาย ไม่ใช่การไล่ตัวเลขบนจออย่างเดียว เริ่มทดลองได้วันนี้ที่%s" % (goal_name, niche, plat_name, SIGN),
        ],
    )