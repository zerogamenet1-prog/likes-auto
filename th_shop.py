import html
import re

_PAIRS = (
    ("group members", "สมาชิกกลุ่ม"),
    ("page likes", "เพิ่มไลค์เพจ"),
    ("page followers", "ผู้ติดตามเพจ"),
    ("post likes", "เพิ่มไลค์โพสต์"),
    ("post packages", "แพ็กเกจโพสต์"),
    ("community post", "โพสต์คอมมูนิตี้"),
    ("video views", "เพิ่มวิววิดีโอ"),
    ("reel views", "เพิ่มวิวรีล"),
    ("reels views", "เพิ่มวิวรีล"),
    ("story views", "เพิ่มวิวสตอรี่"),
    ("live stream", "ไลฟ์สตรีม"),
    ("live video", "วิดีโอไลฟ์"),
    ("live views", "วิวไลฟ์"),
    ("live viewers", "ผู้ชมไลฟ์"),
    ("live comments", "คอมเมนต์ไลฟ์"),
    ("watch time", "เพิ่มเวลาชม"),
    ("watch hours", "ชั่วโมงการชม"),
    ("channel members", "สมาชิกช่อง"),
    ("auto likes", "ไลค์อัตโนมัติ"),
    ("auto views", "วิวอัตโนมัติ"),
    ("auto followers", "ผู้ติดตามอัตโนมัติ"),
    ("auto comments", "คอมเมนต์อัตโนมัติ"),
    ("custom comments", "คอมเมนต์กำหนดเอง"),
    ("random comments", "คอมเมนต์สุ่ม"),
    ("positive comments", "คอมเมนต์เชิงบวก"),
    ("super comments", "ซูเปอร์คอมเมนต์"),
    ("last 100 posts", "100 โพสต์ล่าสุด"),
    ("last 50 posts", "50 โพสต์ล่าสุด"),
    ("last 30 posts", "30 โพสต์ล่าสุด"),
    ("last 20 posts", "20 โพสต์ล่าสุด"),
    ("last 10 posts", "10 โพสต์ล่าสุด"),
    ("last 30 days", "30 วันล่าสุด"),
    ("high quality", "คุณภาพสูง"),
    ("monetizable", "รับเงินได้"),
    ("targeted", "เจาะกลุ่ม"),
    ("exclusive", "พิเศษ"),
    ("from ads", "จากโฆษณา"),
    ("low quality", "คุณภาพต่ำ"),
    ("non drop", "ไม่ลดยอด"),
    ("no drop", "ไม่ลดยอด"),
    ("no refill", "ไม่มีรับประกันเติม"),
    ("start time", "เริ่มงาน"),
    ("instant start", "เริ่มทันที"),
    ("super fast", "เร็วมาก"),
    ("website traffic", "ทราฟฟิกเว็บไซต์"),
    ("drip feed", "ส่งทีละรอบ"),
    ("quote tweets", "โควททวีต"),
    ("power likes", "พาวเวอร์ไลค์"),
    ("old accounts", "บัญชีเก่า"),
    ("new accounts", "บัญชีใหม่"),
    ("thai clones", "โคลนไทย"),
    ("clone accounts", "บัญชีโคลน"),
    ("refill", "รับประกันเติม"),
    ("guarantee", "รับประกัน"),
    ("followers", "เพิ่มผู้ติดตาม"),
    ("follower", "เพิ่มผู้ติดตาม"),
    ("subscribers", "เพิ่มผู้ติดตาม"),
    ("subscriber", "เพิ่มผู้ติดตาม"),
    ("comments", "เพิ่มคอมเมนต์"),
    ("comment", "เพิ่มคอมเมนต์"),
    ("retweets", "รีทวีต"),
    ("reposts", "รีโพสต์"),
    ("impressions", "การแสดงผล"),
    ("impression", "การแสดงผล"),
    ("engagement", "การมีส่วนร่วม"),
    ("mentions", "แท็ก/เมนชัน"),
    ("mention", "แท็ก/เมนชัน"),
    ("reactions", "รีแอคชัน"),
    ("reaction", "รีแอคชัน"),
    ("bookmarks", "บุ๊กมาร์ก"),
    ("bookmark", "บุ๊กมาร์ก"),
    ("shares", "เพิ่มแชร์"),
    ("share", "เพิ่มแชร์"),
    ("saves", "เพิ่มเซฟ"),
    ("save", "เพิ่มเซฟ"),
    ("likes", "เพิ่มไลค์"),
    ("like", "เพิ่มไลค์"),
    ("views", "เพิ่มวิว"),
    ("view", "เพิ่มวิว"),
    ("plays", "เพิ่มยอดเล่น"),
    ("play", "เพิ่มยอดเล่น"),
    ("listeners", "เพิ่มผู้ฟัง"),
    ("friends", "เพิ่มเพื่อน"),
    ("members", "สมาชิก"),
    ("member", "สมาชิก"),
    ("visitors", "ผู้เข้าชม"),
    ("visitor", "ผู้เข้าชม"),
    ("traffic", "ทราฟฟิก"),
    ("rating", "เพิ่มเรตติ้ง"),
    ("reviews", "เพิ่มรีวิว"),
    ("review", "เพิ่มรีวิว"),
    ("votes", "โหวต"),
    ("vote", "โหวต"),
    ("clones", "โคลน"),
    ("clone", "โคลน"),
    ("accounts", "บัญชี"),
    ("account", "บัญชี"),
    ("packages", "แพ็กเกจ"),
    ("package", "แพ็กเกจ"),
    ("premium", "พรีเมียม"),
    ("organic", "ออร์แกนิก"),
    ("worldwide", "ทั่วโลก"),
    ("thailand", "ไทย"),
    ("recommended", "แนะนำ"),
    ("cheapest", "ราคาถูกสุด"),
    ("fastest", "เร็วสุด"),
    ("instant", "เริ่มทันที"),
    ("express", "ด่วน"),
    ("random", "สุ่ม"),
    ("female", "ผู้หญิง"),
    ("male", "ผู้ชาย"),
    ("active", "แอคทีฟ"),
    ("unique", "ยูนิค"),
    ("brazil", "บราซิล"),
    ("indian", "อินเดีย"),
    ("india", "อินเดีย"),
    ("arab", "อาหรับ"),
    ("korea", "เกาหลี"),
    ("vietnam", "เวียดนาม"),
    ("indonesia", "อินโดนีเซีย"),
    ("philippines", "ฟิลิปปินส์"),
    ("europe", "ยุโรป"),
    ("lifetime", "ตลอดชีพ"),
    ("monthly", "รายเดือน"),
    ("custom", "กำหนดเอง"),
    ("emoji", "อิโมจิ"),
    ("profile", "โปรไฟล์"),
    ("stories", "สตอรี่"),
    ("story", "สตอรี่"),
    ("reels", "รีล"),
    ("reel", "รีล"),
    ("shorts", "ช็อตส์"),
    ("short", "ช็อตส์"),
    ("boost", "บูสต์"),
    ("reach", "รีช"),
    ("power", "พาวเวอร์"),
    ("mixed", "ผสม"),
    ("cheap", "ราคาถูก"),
    ("thai", "ไทย"),
    ("real", "บัญชีจริง"),
    ("bot", "บอท"),
    ("server", "เซิร์ฟเวอร์"),
    ("quality", "คุณภาพ"),
    ("speed", "ความเร็ว"),
    ("delivery", "ส่งงาน"),
    ("subscription", "เติมอัตโนมัติ"),
    ("hours", "ชม."),
    ("hour", "ชม."),
    ("days", "วัน"),
    ("day", "วัน"),
    ("posts", "โพสต์"),
    ("post", "โพสต์"),
    ("fast", "เร็ว"),
    ("slow", "ช้า"),
    ("hot", "มาแรง"),
    ("new", "มาใหม่"),
    ("old", "เก่า"),
    ("mix", "ผสม"),
    ("max", "สูงสุด"),
    ("min", "ขั้นต่ำ"),
    ("hq", "คุณภาพสูง"),
    ("lq", "คุณภาพต่ำ"),
    ("ww", "ทั่วโลก"),
    ("usa", "สหรัฐ"),
    ("us", "สหรัฐ"),
)

_TH_SEARCH = (
    ("ไลค์", ("like", "likes")),
    ("ถูกใจ", ("like", "likes")),
    ("ฟอล", ("follow", "followers")),
    ("ผู้ติดตาม", ("followers", "subscribers")),
    ("วิว", ("view", "views")),
    ("คอมเมนต์", ("comment", "comments")),
    ("แชร์", ("share", "shares")),
    ("ซับ", ("sub", "subscribers")),
    ("ไลฟ์", ("live",)),
    ("สตอรี่", ("story", "stories")),
    ("ถูก", ("cheap",)),
    ("เร็ว", ("fast", "instant")),
    ("ไทย", ("thai", "thailand")),
    ("รับประกัน", ("refill", "guarantee")),
    ("เพจ", ("page",)),
    ("โคลน", ("clone", "clones")),
    ("อิโมจิ", ("emoji",)),
    ("รีล", ("reel", "reels")),
)


def th_text(text):
    out = str(text or "")
    if not out:
        return ""
    for _ in range(3):
        nxt = html.unescape(out)
        if nxt == out:
            break
        out = nxt
    out = out.replace("\xa0", " ")
    for en, th in _PAIRS:
        out = re.sub(r"(?i)(?<![A-Za-z])" + re.escape(en) + r"(?![A-Za-z])", th, out)
    out = re.sub(r"\s{2,}", " ", out).strip(" -|/:")
    return out or str(text)


def th_label(platform, category, featured=False):
    plat = (platform or "").strip() or "อื่น ๆ"
    cat = (category or "").strip() or "ทั่วไป"
    rest = cat
    if rest.lower().startswith(plat.lower()):
        rest = rest[len(plat):].lstrip(" -|/:()")
    pretty = th_text(rest) if rest else "ทั่วไป"
    if pretty.lower() == plat.lower():
        pretty = "ทั่วไป"
    if featured:
        pretty = pretty + " 🔰"
    blob = ("%s %s" % (cat, pretty)).lower()
    if "emoji" in blob or "อิโมจิ" in pretty or "reaction" in blob:
        pretty = pretty + " ❤️"
    elif "clone" in blob or "โคลน" in pretty:
        pretty = pretty + " | 🔥 มาใหม่ 🔥"
    elif "cheap" in blob or "ถูกสุด" in pretty:
        pretty = pretty + " 🔥🔥"
    elif "like" in blob or "ไลค์" in pretty or "ถูกใจ" in pretty:
        pretty = pretty + " 👍"
    elif "follow" in blob or "ผู้ติดตาม" in pretty:
        pretty = pretty + " 🔥"
    elif "live" in blob or "ไลฟ์" in pretty:
        pretty = pretty + " 🔴"
    elif "comment" in blob or "คอมเมนต์" in pretty:
        pretty = pretty + " 💬"
    return "%s - %s" % (plat, pretty)


def search_aliases(q):
    q = (q or "").strip()
    if not q:
        return []
    terms = [q]
    for th, ens in _TH_SEARCH:
        if th in q:
            for en in ens:
                if en not in terms:
                    terms.append(en)
    return terms[:8]


_SPEED_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(k|m)\s*/\s*(day|วัน|d)\b", re.I)


def _facts(text):
    out = {}
    for raw in re.findall(r"\[([^\]]+)\]", str(text or "")):
        if ":" in raw:
            key, val = raw.split(":", 1)
            out[key.strip().lower()] = val.strip()
    return out


def _speed_bit(raw, facts, low):
    speed = facts.get("ความเร็ว") or facts.get("speed") or facts.get("average time") or ""
    speed = th_text(speed)
    match = _SPEED_RE.search(raw or "")
    if match:
        speed = "%s%s/วัน" % (match.group(1).rstrip("0").rstrip(".") if "." in match.group(1) else match.group(1), match.group(2).upper())
    if not speed:
        if "instant" in low or "ทันที" in low:
            speed = "ไวมาก"
        elif "fastest" in low or "express" in low:
            speed = "รวดเร็ว"
        elif "fast" in low or "เร็ว" in low:
            speed = "รวดเร็ว"
        else:
            speed = "ตามคิว"
    if "ไวมาก" in speed or "instant" in low:
        return "🚀🚀🚀 " + speed
    if "รวดเร็ว" in speed or "fast" in low:
        return "🚀🚀 " + speed
    return "🚀 " + speed


def _start_bit(facts, low):
    start = facts.get("เริ่มงาน") or facts.get("start time") or facts.get("start") or ""
    start = th_text(start)
    blob = ("%s %s" % (start, low)).lower()
    if "instant" in blob or start == "ทันที":
        return "⌛ ทันที"
    span = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*(hour|hours|hr|hrs|ชม\.?)", blob, re.I)
    if span:
        return "⌛ เริ่ม %s-%s ชม." % (span.group(1), span.group(2))
    if not start:
        return "⌛ ตามคิว"
    start = start.replace("Hours", "ชม.").replace("hours", "ชม.").replace("Hrs", "ชม.").replace("hrs", "ชม.").replace("Hour", "ชม.").replace("Hr", "ชม.")
    if "ชม" not in start and re.search(r"\d", start):
        start = start + " ชม."
    if not start.startswith("เริ่ม") and start != "ทันที" and start != "ตามคิว":
        start = "เริ่ม " + start
    return "⌛ " + start


def shop_card(item):
    catalog = item.get("catalog_name") or ""
    stored = item.get("name") or ""
    raw = "%s %s" % (catalog, stored)
    low = raw.lower()
    facts = _facts(raw)
    plat = (item.get("platform") or "").strip()
    base = (item.get("category_th") or item.get("category") or item.get("name_short") or stored).split(" · ", 1)[0].strip()
    title = ("%s %s" % (base, plat)).strip() if plat and plat.lower() not in base.lower() else (base or "บริการ")
    bits = []
    bits.append(_speed_bit(raw, facts, low))
    bits.append(_start_bit(facts, low))
    refill_raw = str(item.get("catalog_refill") or facts.get("refill") or facts.get("รับประกันเดิม") or facts.get("รับประกัน") or "")
    refill_low = refill_raw.lower()
    has_refill = refill_low in {"1", "true", "yes"} or ("refill" in low and "no refill" not in low and "ไม่มีรับประกัน" not in stored)
    if has_refill:
        days = re.search(r"(\d+)\s*(day|days|วัน)", low)
        if days:
            bits.append("♻️ ประกัน %s วัน" % days.group(1))
        else:
            bits.append("♻️ มีรับประกัน")
        bits.append("🔔 เติมยอดได้")
    else:
        bits.append("⛔ ไม่มีประกัน")
    if "hq" in low or "premium" in low or "organic" in low or "คุณภาพสูง" in stored or "คุณภาพสูง" in title:
        bits.append("👤 คุณภาพสูง")
    recommend = False
    if "ราคาถูก" in stored:
        bits.append("💎 ราคาถูก")
        bits.append("⚡ แนะนำ")
        recommend = True
    elif "คุณภาพสูง" in stored or "มีรับประกัน" in stored or has_refill:
        bits.append("⚡ แนะนำ")
        recommend = True
    elif "คนไทย" in stored:
        bits.append("🔥 คนไทย")
        bits.append("⚡ แนะนำ")
        recommend = True
    elif "เริ่มเร็ว" in stored:
        bits.append("🔥 เริ่มเร็ว")
    seen = set()
    clean = []
    for bit in bits:
        if bit in seen:
            continue
        seen.add(bit)
        clean.append(bit)
    return {
        "title": title,
        "bits": clean,
        "recommend": recommend,
        "line": " | ".join(clean),
    }


_EXAMPLE_LINKS = (
    ("instagram", "https://www.instagram.com/username"),
    ("facebook", "https://www.facebook.com/yourpage"),
    ("tiktok", "https://www.tiktok.com/@username"),
    ("youtube", "https://www.youtube.com/watch?v=xxxxxxxxxxx"),
    ("telegram", "https://t.me/username"),
    ("twitter", "https://x.com/username"),
    ("spotify", "https://open.spotify.com/track/xxxxxxxxxxx"),
    ("twitch", "https://www.twitch.tv/username"),
    ("whatsapp", "https://wa.me/66xxxxxxxxx"),
    ("shopee", "https://shopee.co.th/product"),
    ("reddit", "https://www.reddit.com/r/example"),
    ("pinterest", "https://www.pinterest.com/pin/xxxxxxxxxxx"),
    ("soundcloud", "https://soundcloud.com/artist/track"),
    ("discord", "https://discord.gg/invite"),
    ("threads", "https://www.threads.net/@username"),
    ("linkedin", "https://www.linkedin.com/in/username"),
    ("snapchat", "https://www.snapchat.com/add/username"),
    ("line", "https://line.me/R/ti/p/@official"),
    ("google", "https://maps.google.com/?cid=0"),
    ("website", "https://yourwebsite.com"),
    ("seo", "https://yourwebsite.com"),
)


_SKIP_LINK = ("pumlike", "pumlf", "ads4u", "km-social", "kmsocial")


def _example_link(platform, facts):
    raw = facts.get("example") or facts.get("example link") or facts.get("link") or facts.get("sample") or facts.get("ลิงก์ตัวอย่าง") or ""
    low = raw.lower()
    if raw.startswith("http") and not any(bad in low for bad in _SKIP_LINK):
        return raw.strip()
    n = (platform or "").lower()
    if n in {"x", "twitter / x"}:
        return "https://x.com/username"
    for key, url in _EXAMPLE_LINKS:
        if key in n:
            return url
    return "https://your-public-link.com"


def _yes_no(val, yes="มี", no="ไม่มี"):
    t = str(val or "").strip().lower()
    if t in {"1", "true", "yes", "y"}:
        return yes
    if t in {"0", "false", "no", "n"}:
        return no
    if t:
        pretty = th_text(val)
        if pretty.lower() in {"yes", "no"}:
            return yes if pretty.lower() == "yes" else no
        return pretty
    return no


def shop_explain(item):
    catalog = item.get("catalog_name") or ""
    stored = item.get("name") or ""
    raw = "%s %s" % (catalog, stored)
    low = raw.lower()
    facts = _facts(raw)
    plat = item.get("platform") or ""
    start = facts.get("เริ่มงาน") or facts.get("start time") or facts.get("start") or ""
    start = th_text(start)
    if not start:
        if "instant" in low or "ทันที" in low:
            start = "ทันที"
        else:
            start = "ตามคิว"
    start = start.replace("Hours", "ชม.").replace("hours", "ชม.").replace("Hrs", "ชม.").replace("hrs", "ชม.")
    if re.search(r"\d+\s*[-–]\s*\d+", start) and "หรือ" not in start:
        start = start + " หรือนานกว่านั้น"
    speed = facts.get("ความเร็ว") or facts.get("speed") or ""
    speed = th_text(speed)
    match = _SPEED_RE.search(raw or "")
    if match:
        num = match.group(1).rstrip("0").rstrip(".") if "." in match.group(1) else match.group(1)
        speed = "%s%s / วัน" % (num, match.group(2).upper())
    if not speed:
        if "instant" in low:
            speed = "เริ่มทันที"
        elif "fast" in low or "เร็ว" in low:
            speed = "รวดเร็ว ตามคิว"
        else:
            speed = "ตามคิวงาน"
    if "instant" not in low and "ทันที" not in speed:
        speed = speed + " (อาจช้าลงได้ตามคิว)"
    if "hq" in low or "premium" in low or "organic" in low or "คุณภาพสูง" in stored:
        quality = "สูง"
    elif "low quality" in low or "lq" in low or "bot" in low or "คุณภาพต่ำ" in stored:
        quality = "ต่ำ"
    else:
        quality = "ปานกลาง"
    qfact = facts.get("quality") or facts.get("คุณภาพ")
    if qfact:
        quality = th_text(qfact)
    refill_raw = item.get("catalog_refill") or facts.get("refill") or facts.get("รับประกันเดิม") or facts.get("รับประกัน") or ""
    refill_low = str(refill_raw).lower().strip()
    if refill_low in {"0", "false", "no", "n"}:
        has_refill = False
    elif refill_low in {"1", "true", "yes", "y"}:
        has_refill = True
    else:
        has_refill = "refill" in low and "no refill" not in low and "refill: no" not in low and "refill:no" not in low
    refill_txt = _yes_no(refill_raw if str(refill_raw).strip() else ("yes" if has_refill else "no"))
    if has_refill:
        days = re.search(r"(\d+)\s*(day|days|วัน)", low)
        if days:
            refill_txt = "มี (%s วัน)" % days.group(1)
        drop = "หากยอดลด มีรับประกันเติมคืน"
    else:
        drop = "มีโอกาสลดยอดได้"
    drop_fact = facts.get("drop") or facts.get("การดรอป")
    if drop_fact:
        drop = th_text(drop_fact)
    avg = facts.get("average time") or facts.get("เวลาเฉลี่ย") or facts.get("avg time") or ""
    avg = th_text(avg)
    notes = [
        {"label": "เริ่มงาน", "value": start},
        {"label": "ความเร็ว", "value": speed},
        {"label": "คุณภาพ", "value": quality},
        {"label": "เติมยอด", "value": refill_txt},
        {"label": "การดรอป", "value": drop},
    ]
    if avg:
        notes.append({"label": "เวลาโดยประมาณ", "value": avg})
    notes.append({"label": "ลิงก์ตัวอย่าง", "value": _example_link(plat, facts)})
    notes.append({"label": "ลิงก์ที่ใช้ได้", "value": "ลิงก์สาธารณะเท่านั้น ไม่ขอรหัสผ่าน"})
    try:
        mn = int(item.get("min_qty") or 0)
        mx = int(item.get("max_qty") or 0)
    except (TypeError, ValueError):
        mn = mx = 0
    if mn or mx:
        notes.append({
            "label": "ช่วงจำนวน",
            "value": "ขั้นต่ำ {:,} - สูงสุด {:,}".format(mn, mx),
        })
    kind = th_text(item.get("catalog_type") or "")
    if kind and kind.lower() not in {"default", "เริ่มต้น"}:
        notes.insert(0, {"label": "ประเภท", "value": kind})
    try:
        from service_fields import order_fields
        fld = order_fields(item)
        if fld.get("needs_comments"):
            notes.insert(0, {"label": "คอมเมนต์", "value": "กรอกทีละบรรทัด 1 บรรทัด = 1 คอมเมนต์"})
    except Exception:
        pass
    return notes

