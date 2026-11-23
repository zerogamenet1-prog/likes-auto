import urllib.request
import json
import base64
import os
import subprocess
import time
import wave
import asyncio
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
try:
    import cv2
except Exception:
    cv2 = None

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "likes_auto_studio_ext" / "studio" / "fonts"
MUSIC_DIR = BASE_DIR / "likes_auto_studio_ext" / "studio" / "music"
SFX_DIR = BASE_DIR / "likes_auto_studio_ext" / "studio" / "sfx"
SFX_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_DIR = BASE_DIR / "rendered_clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

def load_default_api_key() -> str:
    k = os.environ.get("GEMINI_API_KEY", "")
    if k:
        return k
    for env_path in [
        BASE_DIR / "py-app" / ".env",
        BASE_DIR / ".env",
        Path(__file__).resolve().parent / ".env"
    ]:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return ""

DEFAULT_API_KEY = load_default_api_key()

def check_has_audio(video_path: Path) -> bool:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        return "audio" in out.lower()
    except Exception:
        return False

def extract_video_keyframes(video_path: Path, max_frames: int = 4) -> list:
    """Extracts high quality keyframes from the video as base64 JPEG strings for AI multimodal analysis."""
    try:
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
        ]).decode().strip() or "6.0")
    except Exception:
        dur = 6.0

    if dur <= 3.0:
        timestamps = [f"{dur*0.5:.2f}"]
    elif dur <= 6.0:
        timestamps = ["0.5", f"{dur*0.5:.2f}", f"{dur*0.85:.2f}"]
    else:
        timestamps = ["1.0", f"{dur*0.3:.2f}", f"{dur*0.6:.2f}", f"{dur*0.85:.2f}"]

    base64_frames = []
    tmp_dir = video_path.parent
    for i, ts in enumerate(timestamps[:max_frames]):
        frame_file = tmp_dir / f"{video_path.stem}_kf_{i}.jpg"
        cmd = ["ffmpeg", "-y", "-ss", ts, "-i", str(video_path), "-vframes", "1", "-q:v", "2", str(frame_file)]
        subprocess.run(cmd, capture_output=True)
        if frame_file.exists():
            try:
                base64_frames.append(base64.b64encode(frame_file.read_bytes()).decode("utf-8"))
            finally:
                try:
                    frame_file.unlink(missing_ok=True)
                except Exception:
                    pass
    return base64_frames

def generate_script(src_video_path: Path = None, product_details: str = "", api_key: str = DEFAULT_API_KEY):
    """Uses Gemini Multimodal Vision to inspect video frames and write a hyper-targeted sales script matching the exact product."""
    frames = extract_video_keyframes(src_video_path) if src_video_path and src_video_path.exists() else []
    effective_key = api_key if (api_key and len(api_key) > 10) else DEFAULT_API_KEY

    system_prompt = f"""คุณคือนักรีวิวและคอนเทนต์ครีเอเตอร์สายป้ายยาขายของมืออาชีพสำหรับคลิปสั้นไวรัล (TikTok / Facebook Reels)

ภารกิจสำคัญที่สุด:
1. ดูภาพสินค้าจริงจากวิดีโอที่แนบมานี้อย่างละเอียดที่สุด: สังเกตว่าในคลิปคือสินค้าอะไร แบรนด์อะไร ชื่อรุ่นอะไร สีอะไร บรรจุภัณฑ์เป็นแบบไหน และมีคุณสมบัติอะไรเด่นชัด
2. แต่งบทพากย์ภาษาไทยขายของแบบเจาะจงสินค้าตัวที่เห็นในคลิปนี้โดยตรง 100% ระบุชื่อสินค้าและแบรนด์จริงให้ชัดเจน ห้ามพูดกว้างๆ ลอยๆ เด็ดขาด!
3. สำคัญที่สุดเรื่องความเป็นธรรมชาติ: แต่งเป็น "ภาษาพูดจริงของคน" (Natural Spoken Thai) สไตล์ครีเอเตอร์รีวิวคุยกับเพื่อน ห้ามใช้ภาษาเขียนหรือศัพท์ทางการแข็งๆ เด็ดขาด!
   - ใช้คำขึ้นต้นและคำเชื่อมแบบธรรมชาติ เช่น "ทุกคน!", "บอกเลยว่า...", "คือดีมาก", "เนี่ย...", "ใครที่กำลัง...", "ตัวนี้เลยจ้า"
   - ใส่เครื่องหมายวรรคตอน เช่น คอมม่า (,) หรือ จุดไข่ปลา (...) ในจุดที่ควรเว้นวรรคหายใจ เพื่อให้เสียง AI เว้นจังหวะพูดเหมือนมนุษย์จริง
{f"ข้อมูลเสริมเพิ่มเติมจากผู้ขาย: {product_details}" if product_details else ""}

โครงสร้างบทพากย์ (ความยาวพูดประมาณ 35-45 คำ พูดจบใน 14-17 วินาที พอดีกับคลิป):
- วินาทีที่ 0-3: Hook เปิดหัวแบบคนคุยกัน ระบุสินค้าที่เห็นในคลิป ตรึงคนดูให้อยากฟังต่อ
- วินาทีที่ 4-11: รีวิวฟังก์ชันจริง บอกจุดเด่น ความคุ้มค่า ของสินค้าตัวนี้ที่เห็นในภาพ
- วินาทีที่ 12-16: Call-to-action ปิดท้าย ชี้เป้าให้กด "พิกัดมุมซ้ายล่าง" อย่างเป็นธรรมชาติ

ตอบกลับเป็น JSON เท่านั้น รูปแบบ:
{{
  "detected_product": "ชื่อสินค้า แบรนด์ และรุ่นที่เห็นในภาพจริง เช่น สีน้ำทาบ้าน TOA ตราปลาฉลาม",
  "title": "หัวข้อคลิปสั้นๆ โดนใจ ระบุชื่อสินค้าจริง",
  "hook": "ประโยคเปิด",
  "thai_script": "บทพากย์ไทยภาษาพูดที่เป็นธรรมชาติสุดๆ รีวิวเจาะจงสินค้าตัวจริง มีเครื่องหมายเว้นวรรคจังหวะหายใจ และลงท้ายด้วยกดพิกัดมุมซ้ายล่างเลยจ้า",
  "subtitle_lines": [
    "วรรค 1 (สั้นไม่เกิน 12 ตัวอักษร)",
    "วรรค 2",
    "วรรค 3",
    "วรรค 4",
    "กดพิกัดมุมซ้ายล่าง"
  ],
  "caption": "แคปชันโพสต์ขายของสไตล์ป้ายยา ระบุชื่อสินค้าจริงพร้อมแฮชแท็ก",
  "hashtags": ["#รีวิวของดี", "#TikTokป้ายยา", "#Shopeeถูกชัวร์", "#ของใช้ดีบอกต่อ"],
  "first_comment": "📌 สนใจสั่งซื้อพิกัดสินค้าจิ้มตรงนี้เลยจ้า: (ใส่ลิงก์พิกัดร้านค้าของคุณ) ตอนนี้มีโค้ดลดเพิ่มด้วยน้า"
}}
"""
    # Multimodal parts: frames + prompt text
    parts = []
    for f in frames:
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": f}})
    parts.append({"text": system_prompt})

    models = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
    ]
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={effective_key}"
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": effective_key}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                raw = res["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw)
        except Exception:
            continue

    # Fallback to high converting default script if offline or hitch
    prod_name = product_details or "สินค้าสุดคุ้มตัวเด็ด"
    return {
        "detected_product": prod_name,
        "title": f"ของดีบอกต่อ {prod_name}",
        "hook": "ทุกคน! ใครกำลังมองหาตัวช่วยดีๆ ต้องดูคลิปนี้ด่วนเลย",
        "thai_script": f"ทุกคน! ใครกำลังมองหา {prod_name} คุ้มราคา, บอกเลยว่าตัวนี้คือห้ามพลาดเด็ดขาด... ใช้งานง่าย, คุณภาพดีเกินเบอร์มาก! ใครสนใจชี้พิกัดส่วนลดพิเศษไว้ให้แล้วในคลิป, จิ้มพิกัดมุมซ้ายล่างได้เลยจ้า",
        "subtitle_lines": [
            "ทุกคนต้องดูด่วน",
            f"ของดี {prod_name[:8]}",
            "คุณภาพดีเกินเบอร์",
            "ใช้งานง่ายสุดๆ",
            "กดพิกัดมุมซ้ายล่าง"
        ],
        "caption": f"ของดีบอกต่อ {prod_name} คุ้มค่าเกินราคาแน่นอน #รีวิวของดี #TikTokป้ายยา #Shopeeถูกชัวร์ #ของใช้ดีบอกต่อ",
        "hashtags": ["#รีวิวของดี", "#TikTokป้ายยา", "#Shopeeถูกชัวร์", "#ของใช้ดีบอกต่อ"],
        "first_comment": "📌 สนใจสั่งซื้อพิกัดสินค้าจิ้มตรงนี้เลยจ้า: (ใส่ลิงก์พิกัดร้านค้าของคุณ) ตอนนี้มีโค้ดลดเพิ่มด้วยน้า"
    }


def synthesize_voice_edge(script_text: str, voice_name: str, out_wav_path: Path):
    """High quality fallback voice synthesis using Edge-TTS Neural Thai voices with custom personality rate and pitch."""
    voice_configs = {
        "kore": ("th-TH-PremwadeeNeural", "+4%", "+2Hz"),    # หญิง - นุ่มนวล คมชัด มีชีวิตชีวา แนะนำยอดนิยม
        "aoede": ("th-TH-PremwadeeNeural", "+0%", "+0Hz"),   # หญิง - ละมุน ฟังสบาย อบอุ่น เป็นมิตร
        "leda": ("th-TH-PremwadeeNeural", "+2%", "+0Hz"),    # หญิง - หวาน อ่อนโยน น่ารัก สดใส
        "zephyr": ("th-TH-PremwadeeNeural", "+7%", "+0Hz"),  # หญิง - มั่นใจ กระฉับกระเฉง คล่องแคล่ว ทันสมัย
        "puck": ("th-TH-NiwatNeural", "+5%", "+4Hz"),        # ชาย - สดใส วัยรุ่น มีพลัง กระตือรือร้น
        "fenrir": ("th-TH-NiwatNeural", "+0%", "+0Hz"),      # ชาย - ทุ้ม อบอุ่น สไตล์รีวิวเรียลๆ
        "charon": ("th-TH-NiwatNeural", "-4%", "-5Hz"),      # ชาย - สุขุม นิ่ง ผู้ใหญ่ น่าเชื่อถือ มืออาชีพ
    }
    target_voice, rate, pitch = voice_configs.get((voice_name or "kore").lower(), ("th-TH-PremwadeeNeural", "+0%", "+0Hz"))
    mp3_tmp = out_wav_path.with_suffix(".mp3")
    clean_text = script_text.strip()
    cmd = ["edge-tts", "--text", clean_text, "--voice", target_voice]
    if rate and rate != "+0%": cmd.append(f"--rate={rate}")
    if pitch and pitch != "+0Hz": cmd.append(f"--pitch={pitch}")
    cmd.extend(["--write-media", str(mp3_tmp)])

    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or not mp3_tmp.exists() or mp3_tmp.stat().st_size == 0:
        fb_cmd = ["edge-tts", "--text", clean_text, "--voice", target_voice, "--write-media", str(mp3_tmp)]
        subprocess.run(fb_cmd, capture_output=True, check=True)

    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(mp3_tmp), "-ar", "24000", "-ac", "1", str(out_wav_path)], capture_output=True, check=True)
    finally:
        mp3_tmp.unlink(missing_ok=True)


def synthesize_voice(script_text: str, voice_name: str = "Kore", api_key: str = DEFAULT_API_KEY, out_wav_path: Path = None):
    """
    Synthesizes voiceover exclusively using Google AI Studio (https://aistudio.google.com/generate-speech).
    Uses official Gemini TTS models (gemini-3.8-flash-lite-tts, gemini-3.1-flash-tts-preview) for 100% natural, lifelike human voice.
    """
    tts_models = [
        "gemini-3.8-flash-lite-tts",
        "gemini-3.1-flash-tts-preview",
        "gemini-3.8-flash-tts",
        "gemini-2.5-flash-preview-tts",
    ]
    clean_voice = voice_name if voice_name in ["Kore", "Aoede", "Puck", "Fenrir", "Charon", "Leda", "Zephyr"] else "Kore"
    effective_key = api_key if (api_key and len(api_key) > 10) else DEFAULT_API_KEY

    payload = {
        "contents": [{"parts": [{"text": script_text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": clean_voice}
                }
            }
        }
    }
    encoded_payload = json.dumps(payload).encode("utf-8")

    for model in tts_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={effective_key}"
        req = urllib.request.Request(
            url,
            data=encoded_payload,
            headers={"Content-Type": "application/json", "x-goog-api-key": effective_key}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                inline = res["candidates"][0]["content"]["parts"][0]["inlineData"]
                raw_bytes = base64.b64decode(inline["data"])
                
                # If RIFF header is present (standard WAV from gemini-3.8-flash-lite-tts)
                if raw_bytes.startswith(b"RIFF"):
                    out_wav_path.write_bytes(raw_bytes)
                else:
                    # Headerless 24kHz 16-bit mono PCM (from gemini-3.1-flash-tts-preview)
                    with wave.open(str(out_wav_path), "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(raw_bytes)
                return
        except Exception:
            continue

    # Fallback to Neural Edge-TTS if all Google AI Studio models fail or network disconnects
    synthesize_voice_edge(script_text, voice_name, out_wav_path)


def wrap_thai_title(raw_text: str, font_title=None, max_px_width: int = 580):
    text = raw_text.strip()
    for prefix in ['รีวิว', 'แนะนำ', 'เปิดตัว']:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    try:
        from pythainlp import word_tokenize
        from pythainlp.corpus.common import thai_words
        from pythainlp.util import Trie
        custom_words = set(thai_words())
        custom_words.update(['วินเทจ', 'สแตนเลส', 'โปรดักชัน', 'คัลเลอร์บาร์', 'บลูทูธ', 'ไวรัล', 'พรีเมียม', 'สมาร์ทโฟน', 'คัลเลอร์'])
        trie = Trie(custom_words)
        raw_tokens = word_tokenize(text, custom_dict=trie, engine="newmm")
        tokens = []
        for t in raw_tokens:
            if tokens and (len(t) <= 1 or t in ['ๆ', 'ฯ'] or t.startswith('์')):
                tokens[-1] += t
            else:
                tokens.append(t)
    except Exception:
        tokens = text.split()

    lines = []
    curr = ""
    for tok in tokens:
        test_str = curr + tok
        if font_title:
            tw = font_title.getbbox(test_str)[2] - font_title.getbbox(test_str)[0]
            fits = tw <= max_px_width
        else:
            fits = len(test_str) <= 18
            
        if fits:
            curr = test_str
        else:
            if curr:
                lines.append(curr.strip())
            curr = tok
    if curr:
        lines.append(curr.strip())
    return [l for l in lines if l][:3]


def draw_star(draw, center, size, fill=(255, 215, 0)):
    cx, cy = center
    points = []
    for i in range(10):
        r = size if i % 2 == 0 else size / 2.3
        angle = i * math.pi / 5 - math.pi / 2
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill)


def format_thumbnail_texts(title: str, detected_product: str) -> tuple[str, str]:
    """
    Format title and product into a punchy, high-CTR 2-tier viral headline.
    Line 1: Hero Keyword / Product (highlighted in sticker box)
    Line 2: Punchline / Benefit / Hook (crisp white text with heavy outline)
    """
    p = (detected_product or "").strip()
    t = (title or "").strip()
    
    stop_words = ["ด้วย", "กับ", "ของ", "โดย", "และ", "หรือ", "เพื่อ", "ที่", "มี", "ใน", "จาก", "ให้", "เป็น", "คือ", "ไว้", "กัน", "น้า", "นะ", "จ้า"]

    def clean_sub(s: str) -> str:
        s = s.strip(" :!-|,•–—/\\")
        changed = True
        while changed:
            changed = False
            for w in stop_words:
                if s.endswith(" " + w) or s.endswith(w):
                    s = s[:-len(w)].strip(" :!-|,•–—/\\")
                    changed = True
                if s.startswith(w + " "):
                    s = s[len(w):].strip(" :!-|,•–—/\\")
                    changed = True
        return s.strip()

    if p and len(p) <= 30:
        hero = p
        if t and t != p:
            sub = t.replace(p, "").strip()
            sub = clean_sub(sub)
            if len(sub) >= 4 and len(sub) <= 35:
                if len(hero) <= 12 and len(sub) <= 18:
                    return f"{hero} {sub}", "คุณภาพพรีเมียม คุ้มเกินราคา!"
                return hero, sub
        return hero, "คุณภาพพรีเมียม คุ้มเกินราคา!"
        
    for sep in [":", " - ", " | ", "! ", " "]:
        if sep in t:
            parts = [x.strip() for x in t.split(sep) if x.strip()]
            if len(parts) >= 2:
                h = parts[0]
                s = clean_sub(" ".join(parts[1:]))
                if len(h) <= 28 and len(s) <= 35:
                    return h, s
                    
    if len(t) > 20:
        words = t.split()
        mid = len(words) // 2
        return " ".join(words[:mid]), clean_sub(" ".join(words[mid:]))
        
    return t or "ไอเทมเด็ดตัวท็อป", "ของดีบอกต่อ คุ้มเกินราคา!"


def select_best_thumbnail_frame(video_path: Path) -> Image.Image:
    """
    Select the sharpest, clearest, best-lit hero frame where the product is prominently presented
    and there is ample headroom for titles (avoiding covering head/hat).
    """
    if cv2 is not None:
        try:
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                dur = total / fps if fps > 0 else 10.0
                
                best_score = -1.0
                best_frame = None
                # Prioritize early hook shots (0.08 - 0.28) where products are clearly showcased
                sample_percentages = [0.08, 0.14, 0.20, 0.28, 0.38, 0.50, 0.65, 0.80]
                for p in sample_percentages:
                    t = dur * p
                    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        continue
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    h_f, w_f = gray.shape
                    
                    # ROI for product presentation (center zone)
                    roi = gray[int(h_f * 0.20):int(h_f * 0.85), int(w_f * 0.15):int(w_f * 0.85)]
                    lap = cv2.Laplacian(roi, cv2.CV_64F).var()
                    mean_val = float(roi.mean())
                    std_val = float(roi.std())
                    
                    # Headroom check: lower variance in top 16% means clean open sky/backdrop (no head overlap!)
                    top_roi = gray[:int(h_f * 0.16), :]
                    top_std = float(top_roi.std())
                    headroom_bonus = max(0, 35 - top_std) * 3.0
                    
                    # Early hook bonus: the presenter holds the hero item front & center in opening seconds
                    early_bonus = 35.0 if p <= 0.22 else 0.0
                    
                    light_penalty = max(0, 50 - mean_val) * 1.5 + max(0, mean_val - 215) * 1.5
                    score = lap * 0.5 + std_val * 2.0 + headroom_bonus + early_bonus - light_penalty
                    if score > best_score:
                        best_score = score
                        best_frame = frame
                cap.release()
                if best_frame is not None:
                    rgb = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
                    return Image.fromarray(rgb).convert("RGBA")
        except Exception:
            pass

    # Fallback extraction via ffmpeg
    temp_frame = video_path.parent / f"temp_frame_{int(time.time())}.jpg"
    cmd = ["ffmpeg", "-y", "-ss", "00:00:01.000", "-i", str(video_path), "-vframes", "1", "-q:v", "2", str(temp_frame)]
    subprocess.run(cmd, capture_output=True)
    if temp_frame.exists():
        im = Image.open(temp_frame).convert("RGBA")
        temp_frame.unlink(missing_ok=True)
        return im
        
    return Image.new("RGBA", (720, 1280), (24, 24, 32, 255))


def draw_sparkle(draw, center, r, fill=(255, 230, 0, 255)):
    cx, cy = center
    pts = [
        (cx, cy - r), (cx + r * 0.28, cy - r * 0.28),
        (cx + r, cy), (cx + r * 0.28, cy + r * 0.28),
        (cx, cy + r), (cx - r * 0.28, cy + r * 0.28),
        (cx - r, cy), (cx - r * 0.28, cy - r * 0.28)
    ]
    draw.polygon(pts, fill=fill)


def draw_text_stroke(draw, pos, text, font, fill, stroke_fill=(0,0,0,255), stroke_w=3, shadow_offset=(0,0), shadow_fill=None):
    x, y = pos
    if shadow_fill and shadow_offset != (0, 0):
        sx, sy = shadow_offset
        draw.text((x + sx, y + sy), text, font=font, fill=shadow_fill)
    for dx in range(-stroke_w, stroke_w + 1):
        for dy in range(-stroke_w, stroke_w + 1):
            if dx * dx + dy * dy <= stroke_w * stroke_w:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_fill)
    draw.text((x, y), text, font=font, fill=fill)


def create_viral_thumbnail(
    video_path: Path,
    out_thumb_path: Path,
    title: str = '',
    detected_product: str = '',
    badge_text: str = '',
    thumb_style: str = 'creator_viral'
) -> Path:
    # 1. Select the sharpest, clearest product hero frame with ample headroom
    base_img = select_best_thumbnail_frame(video_path)
    w, h = base_img.size

    # 2. Enhance contrast, saturation & micro-sharpness for high-end presentation
    base_img = ImageEnhance.Color(base_img).enhance(1.16)
    base_img = ImageEnhance.Contrast(base_img).enhance(1.08)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 3. Smooth Vignette Scrim Overlays
    top_scrim_h = int(min(260, h * 0.22))
    for y in range(top_scrim_h):
        alpha = int(140 * (1.0 - (y / top_scrim_h) ** 1.25))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    bot_scrim_h = int(min(180, h * 0.16))
    for y in range(h - bot_scrim_h, h):
        alpha = int(140 * (((y - (h - bot_scrim_h)) / bot_scrim_h) ** 1.3))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    # Fonts
    font_bold_path = FONTS_DIR / "Kanit-Bold.ttf"
    if not font_bold_path.exists():
        font_bold_path = FONTS_DIR / "Prompt-Bold.ttf"
    font_mitr_path = FONTS_DIR / "Mitr-Bold.ttf"
    if not font_mitr_path.exists():
        font_mitr_path = font_bold_path

    hero_txt, sub_txt = format_thumbnail_texts(title, detected_product)
    style = (thumb_style or 'creator_viral').lower()

    if style == 'lifestyle_food':
        # ===== Style 1: Lifestyle & Food (Reference 1 - Bubbly Two-Tone + Cute Sparkles + Ribbon Tape) =====
        f_b1 = ImageFont.truetype(str(font_mitr_path), max(30, int(w * 0.070)))
        f_b2 = ImageFont.truetype(str(font_mitr_path), max(34, int(w * 0.082)))
        f_tape = ImageFont.truetype(str(font_mitr_path), max(15, int(w * 0.030)))

        words = hero_txt.split()
        if len(words) >= 2:
            s1 = " ".join(words[:len(words)//2])
            s2 = " ".join(words[len(words)//2:])
        else:
            s1 = "รวมของดี"
            s2 = hero_txt

        b1 = f_b1.getbbox(s1)
        b2 = f_b1.getbbox(s2)
        tot_w = (b1[2]-b1[0]) + 10 + (b2[2]-b2[0])
        start_x = (w - tot_w) // 2
        start_y = int(h * 0.024)

        draw_text_stroke(draw, (start_x, start_y), s1, f_b1, fill=(255,255,255), stroke_fill=(0,0,0,255), stroke_w=5, shadow_offset=(3,4), shadow_fill=(0,0,0,160))
        draw_text_stroke(draw, (start_x + (b1[2]-b1[0]) + 10, start_y), s2, f_b1, fill=(255, 230, 0), stroke_fill=(0,0,0,255), stroke_w=5, shadow_offset=(3,4), shadow_fill=(0,0,0,160))

        # Line 2: Big punchy keyword
        p_txt = sub_txt if len(sub_txt) <= 20 else "ติดกระแส"
        b3 = f_b2.getbbox(p_txt)
        w3 = b3[2] - b3[0]
        x3 = (w - w3) // 2
        y3 = start_y + (b1[3]-b1[1]) + 16
        draw_text_stroke(draw, (x3, y3), p_txt, f_b2, fill=(255, 230, 0), stroke_fill=(0,0,0,255), stroke_w=6, shadow_offset=(4,5), shadow_fill=(0,0,0,200))

        # Cute Sparkles
        draw_sparkle(draw, (start_x - 18, start_y + 14), 11, fill=(255, 255, 255))
        draw_sparkle(draw, (start_x + tot_w + 18, start_y + 18), 13, fill=(255, 230, 0))
        draw_sparkle(draw, (x3 + w3 + 18, y3 + 26), 11, fill=(255, 255, 255))

        # Bottom Cute Pastel Tape
        tape_txt = f"🎀 {detected_product or hero_txt} • พิกัดในคลิปจ้า ✨"
        if len(tape_txt) > 36:
            tape_txt = "🎀 พิกัดส่วนลดในคลิป • กดสั่งซื้อด่วน ✨"
        tb = f_tape.getbbox(tape_txt)
        tape_w = (tb[2]-tb[0]) + 36
        tape_h = (tb[3]-tb[1]) + 14
        tape_x = (w - tape_w) // 2
        tape_y = h - tape_h - 16

        draw.rounded_rectangle([tape_x+2, tape_y+3, tape_x+tape_w+2, tape_y+tape_h+3], radius=14, fill=(0,0,0,140))
        draw.rounded_rectangle([tape_x, tape_y, tape_x+tape_w, tape_y+tape_h], radius=14, fill=(253, 232, 236, 245), outline=(244, 114, 182, 240), width=2)
        draw.text((tape_x + (tape_w - (tb[2]-tb[0]))//2, tape_y + (tape_h - (tb[3]-tb[1]))//2 - 2), tape_txt, font=f_tape, fill=(157, 23, 77))

    elif style == 'ecommerce_shop':
        # ===== Style 2: Ecommerce Shop (Reference 4 - Top Capsule + 3 Feature Badges + Gradient Buy Button) =====
        f_top = ImageFont.truetype(str(font_mitr_path), max(26, int(w * 0.054)))
        f_sub = ImageFont.truetype(str(font_bold_path), max(17, int(w * 0.032)))
        f_badge = ImageFont.truetype(str(font_bold_path), max(14, int(w * 0.025)))
        f_cta = ImageFont.truetype(str(font_bold_path), max(17, int(w * 0.032)))

        # Top Neon Yellow Capsule
        top_txt = hero_txt
        bb_top = f_top.getbbox(top_txt)
        tw = (bb_top[2]-bb_top[0]) + 36
        th = (bb_top[3]-bb_top[1]) + 14
        tx, ty = (w - tw)//2, int(h * 0.020)
        draw.rounded_rectangle([tx+2, ty+3, tx+tw+2, ty+th+3], radius=14, fill=(0,0,0,140))
        draw.rounded_rectangle([tx, ty, tx+tw, ty+th], radius=14, fill=(255, 230, 0, 250), outline=(255,255,255,240), width=2)
        draw.text((tx + (tw - (bb_top[2]-bb_top[0]))//2, ty + (th - (bb_top[3]-bb_top[1]))//2 - 2), top_txt, font=f_top, fill=(15, 23, 42))

        # Sub Model Pill
        sub_badge = f"{detected_product or sub_txt} • ของแท้ 100%"
        if len(sub_badge) > 34:
            sub_badge = f"{sub_txt} • ของแท้ 100%"
        bb_sub = f_sub.getbbox(sub_badge)
        sw = (bb_sub[2]-bb_sub[0]) + 24
        sh = (bb_sub[3]-bb_sub[1]) + 8
        sx, sy = (w - sw)//2, ty + th + 10
        draw.rounded_rectangle([sx+2, sy+2, sx+sw+2, sy+sh+2], radius=sh//2, fill=(0,0,0,130))
        draw.rounded_rectangle([sx, sy, sx+sw, sy+sh], radius=sh//2, fill=(15, 23, 42, 230), outline=(250, 204, 21, 230), width=1)
        draw.text((sx + 12, sy + (sh - (bb_sub[3]-bb_sub[1]))//2 - 2), sub_badge, font=f_sub, fill=(254, 240, 138))

        # 3 Feature Pills row
        features = [('✔ ระบายน้ำดี', (16, 185, 129)), ('✔ ทนแดด 5 ปี', (245, 158, 11)), ('✔ เก็บปลายทาง', (139, 92, 246))]
        tot_fw = sum(f_badge.getbbox(ft[0])[2] - f_badge.getbbox(ft[0])[0] + 28 for ft in features) + 16
        fx = (w - tot_fw)//2
        fy = sy + sh + 10
        for ft_txt, ft_col in features:
            fb = f_badge.getbbox(ft_txt)
            fw = (fb[2]-fb[0]) + 24
            fh = (fb[3]-fb[1]) + 8
            draw.rounded_rectangle([fx, fy, fx+fw, fy+fh], radius=6, fill=ft_col, outline=(255,255,255,220), width=1)
            draw.text((fx + 12, fy + (fh - (fb[3]-fb[1]))//2 - 1), ft_txt, font=f_badge, fill=(255,255,255))
            fx += fw + 8

        # Bottom Purple-Pink Gradient Buy Button
        cta_txt = "✨ กดสั่งซื้อจากคลิปนี้เลย! ✨"
        cb = f_cta.getbbox(cta_txt)
        cw = (cb[2]-cb[0]) + 44
        ch = (cb[3]-cb[1]) + 18
        cx = (w - cw)//2
        cy = h - ch - 16

        for step in range(cw):
            ratio = step / cw
            r = int(139 * (1 - ratio) + 236 * ratio)
            g = int(92 * (1 - ratio) + 72 * ratio)
            b = int(246 * (1 - ratio) + 153 * ratio)
            draw.line([(cx + step, cy + 4), (cx + step, cy + ch - 4)], fill=(r, g, b, 255), width=1)
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=ch//2, outline=(255,255,255,230), width=2)
        draw.text((cx + (cw - (cb[2]-cb[0]))//2, cy + (ch - (cb[3]-cb[1]))//2 - 2), cta_txt, font=f_cta, fill=(255,255,255))
        draw_sparkle(draw, (cx + 14, cy + ch//2), 6)
        draw_sparkle(draw, (cx + cw - 14, cy + ch//2), 6)

    elif style == 'curated_picker':
        # ===== Style 3: Curated List / Item Picker (Reference 2) =====
        f_top = ImageFont.truetype(str(font_bold_path), max(28, int(w * 0.056)))
        f_sub = ImageFont.truetype(str(font_bold_path), max(22, int(w * 0.040)))
        f_tag = ImageFont.truetype(str(font_bold_path), max(14, int(w * 0.024)))
        f_cta = ImageFont.truetype(str(font_bold_path), max(17, int(w * 0.032)))

        # Header Sticker Cloud
        top_txt = f"ชี้เป้า: {hero_txt}"
        bb_top = f_top.getbbox(top_txt)
        tw = (bb_top[2]-bb_top[0]) + 30
        th = (bb_top[3]-bb_top[1]) + 14
        tx, ty = (w - tw)//2, int(h * 0.024)
        draw.rounded_rectangle([tx+2, ty+3, tx+tw+2, ty+th+3], radius=14, fill=(0,0,0,140))
        draw.rounded_rectangle([tx, ty, tx+tw, ty+th], radius=14, fill=(255, 255, 255, 245), outline=(37, 99, 235, 240), width=2)
        draw.text((tx + 15, ty + (th - (bb_top[3]-bb_top[1]))//2 - 2), top_txt, font=f_top, fill=(15, 23, 42))

        # Yellow Highlight Bar for Subtitle
        bb_sub = f_sub.getbbox(sub_txt)
        sw = (bb_sub[2]-bb_sub[0]) + 26
        sh = (bb_sub[3]-bb_sub[1]) + 10
        sx, sy = (w - sw)//2, ty + th + 10
        draw.rounded_rectangle([sx+2, sy+2, sx+sw+2, sy+sh+2], radius=8, fill=(0,0,0,130))
        draw.rounded_rectangle([sx, sy, sx+sw, sy+sh], radius=8, fill=(255, 230, 0, 250), outline=(255,255,255,230), width=2)
        draw.text((sx + 13, sy + (sh - (bb_sub[3]-bb_sub[1]))//2 - 2), sub_txt, font=f_sub, fill=(0, 0, 0))

        # Red Free/Hot Stamp
        st_txt = "ตัวท็อป"
        st_b = f_tag.getbbox(st_txt)
        stw = (st_b[2]-st_b[0]) + 14
        sth = (st_b[3]-st_b[1]) + 8
        stx = tx + tw - 8
        sty = ty - 8
        draw.rounded_rectangle([stx, sty, stx+stw, sty+sth], radius=6, fill=(220, 38, 38, 255), outline=(255,255,255,255), width=2)
        draw.text((stx + 7, sty + 1), st_txt, font=f_tag, fill=(255,255,255))

        # Bottom CTA
        cta_txt = "📌 พิกัดในคลิป >> กดสั่งซื้อด่วน"
        cb = f_cta.getbbox(cta_txt)
        cw = (cb[2]-cb[0]) + 36
        ch = (cb[3]-cb[1]) + 16
        cx, cy = (w - cw)//2, h - ch - 16
        draw.rounded_rectangle([cx+2, cy+3, cx+cw+2, cy+ch+3], radius=14, fill=(0,0,0,150))
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=14, fill=(37, 99, 235, 250), outline=(255,255,255,240), width=2)
        draw.text((cx + 18, cy + (ch - (cb[3]-cb[1]))//2 - 2), cta_txt, font=f_cta, fill=(255,255,255))

    else:
        # ===== Style 4: Creator Viral Hook (Default, Reference 3 & 5 - 3D Contrast Headline + Feature Checks) =====
        f_tag = ImageFont.truetype(str(font_bold_path), max(14, int(w * 0.026)))
        f_h1 = ImageFont.truetype(str(font_bold_path), max(28, int(w * 0.058)))
        f_h2 = ImageFont.truetype(str(font_bold_path), max(32, int(w * 0.068)))
        f_check = ImageFont.truetype(str(font_bold_path), max(13, int(w * 0.028)))
        f_cta = ImageFont.truetype(str(font_bold_path), max(16, int(w * 0.033)))

        # 1. Top Angled Crimson Tag
        tag_txt = badge_text or "🔥 ตัวเด็ดติดกระแส • รีวิวของแท้ 100%"
        tb = f_tag.getbbox(tag_txt)
        tw = (tb[2]-tb[0]) + 26
        th = (tb[3]-tb[1]) + 10
        tx, ty = (w - tw) // 2, int(h * 0.018)
        draw.rounded_rectangle([tx+2, ty+2, tx+tw+2, ty+th+2], radius=6, fill=(0,0,0,130))
        draw.rounded_rectangle([tx, ty, tx+tw, ty+th], radius=6, fill=(225, 29, 72, 245), outline=(255,255,255,230), width=2)
        draw.text((tx + 13, ty + (th - (tb[3]-tb[1]))//2 - 2), tag_txt, font=f_tag, fill=(255,255,255))

        # 2. Hero 3D Headline (White 3D + Deep Dropshadow)
        bb1 = f_h1.getbbox(hero_txt)
        w1 = bb1[2] - bb1[0]
        x1 = (w - w1) // 2
        y1 = ty + th + 10
        draw_text_stroke(draw, (x1, y1), hero_txt, f_h1, fill=(255,255,255), stroke_fill=(0,0,0,255), stroke_w=4, shadow_offset=(4, 5), shadow_fill=(0,0,0,200))

        # Line 2: Neon Yellow Headline with heavy 5px outline
        bb2 = f_h2.getbbox(sub_txt)
        w2 = bb2[2] - bb2[0]
        x2 = (w - w2) // 2
        y2 = y1 + (bb1[3]-bb1[1]) + 14
        draw_text_stroke(draw, (x2, y2), sub_txt, f_h2, fill=(255, 230, 0), stroke_fill=(0,0,0,255), stroke_w=5, shadow_offset=(4, 5), shadow_fill=(0,0,0,220))

        # 3. Checkmarks list on right side
        checks = ['✔ ตรงปก 100%', '✔ ทนทาน ใช้งานดี', '✔ มีโค้ดลดในคลิป']
        chk_y = y2 + (bb2[3]-bb2[1]) + 14
        for c in checks:
            cb = f_check.getbbox(c)
            cw = (cb[2]-cb[0]) + 18
            ch = (cb[3]-cb[1]) + 8
            cx = w - cw - 20
            draw.rounded_rectangle([cx, chk_y, cx + cw, chk_y + ch], radius=6, fill=(15, 23, 42, 220), outline=(250, 204, 21, 230), width=1)
            draw.text((cx + 9, chk_y + 1), c, font=f_check, fill=(254, 240, 138))
            chk_y += ch + 6

        # 4. Bottom CTA Emerald Button
        cta_txt = "✨ พิกัดส่วนลดในคลิป >> กดสั่งซื้อเลย! ✨"
        ctab = f_cta.getbbox(cta_txt)
        ctaw = (ctab[2]-ctab[0]) + 36
        ctah = (ctab[3]-ctab[1]) + 18
        ctax = (w - ctaw) // 2
        ctay = h - ctah - 14

        draw.rounded_rectangle([ctax+2, ctay+3, ctax+ctaw+2, ctay+ctah+3], radius=16, fill=(0,0,0,160))
        draw.rounded_rectangle([ctax, ctay, ctax+ctaw, ctay+ctah], radius=16, fill=(16, 185, 129, 250), outline=(255,255,255,240), width=2)
        draw.text((ctax + 18, ctay + (ctah - (ctab[3]-ctab[1]))//2 - 2), cta_txt, font=f_cta, fill=(255,255,255))
        draw_sparkle(draw, (ctax + 12, ctay + ctah//2), 6)
        draw_sparkle(draw, (ctax + ctaw - 12, ctay + ctah//2), 6)

    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    final_img.save(str(out_thumb_path), "JPEG", quality=95)
    return out_thumb_path


def process_studio_render(
    video_bytes: bytes,
    product_details: str = "",
    voice: str = "Kore",
    font: str = "mitr",
    music: bool = True,
    bgm_track: str = "bgm1",
    sfx_choice: str = "auto",
    audio_mode: str = "dub",
    sub_color: str = "#ffffff",
    sub_border: str = "#000000",
    sub_scale: int = 100,
    sub_pos_y: int = 75,
    presenter_bytes: bytes = None,
    presenter_filename: str = "",
    presenter_corner: str = "bottom_right",
    presenter_size: int = 220,
    api_key: str = DEFAULT_API_KEY,
    thumb_style: str = "creator_viral"
):
    key = api_key.strip() if api_key and api_key.strip() else DEFAULT_API_KEY
    timestamp = int(time.time())
    job_prefix = f"reel_{timestamp}"

    # 1. Save uploaded source video
    src_video_path = CLIPS_DIR / f"{job_prefix}_src.mp4"
    src_video_path.write_bytes(video_bytes)

    # 2. Generate Script using Multimodal Vision on real video frames
    script_data = generate_script(src_video_path, product_details, key)
    thai_script = script_data.get("thai_script", "คลิปขายของอัตโนมัติ กดพิกัดมุมซ้ายล่างเลยจ้า")

    # 3. Handle Voice & Audio
    is_dub = (audio_mode or "dub").lower() == "dub"
    voice_path = CLIPS_DIR / f"{job_prefix}_voice.wav"

    if is_dub:
        synthesize_voice(thai_script, voice, key, out_wav_path=voice_path)
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)]
        try:
            voice_dur = float(subprocess.check_output(probe_cmd).decode().strip() or "15.0")
        except Exception:
            voice_dur = 15.0
    else:
        # Source audio mode: use original video duration
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(src_video_path)]
        try:
            voice_dur = float(subprocess.check_output(probe_cmd).decode().strip() or "15.0")
        except Exception:
            voice_dur = 15.0

    # 4. Generate Subtitles ASS
    sub_lines = script_data.get("subtitle_lines", [])
    if not sub_lines:
        sub_lines = [thai_script[:20], thai_script[20:40], "กดพิกัดมุมซ้ายล่าง"]

    step_sec = voice_dur / max(1, len(sub_lines))
    events = []
    for i, line in enumerate(sub_lines):
        start_s = i * step_sec
        end_s = (i + 1) * step_sec
        start_fmt = f"0:{int(start_s//60):02d}:{start_s%60:05.2f}"
        end_fmt = f"0:{int(end_s//60):02d}:{end_s%60:05.2f}"
        if "พิกัด" in line or "ซ้ายล่าง" in line or i == len(sub_lines) - 1:
            styled_line = f"{{\\c&H00D4B606&}}{line}"
        else:
            styled_line = line
        events.append(f"Dialogue: 0,{start_fmt},{end_fmt},Default,,0,0,0,,{styled_line}")

    # Map all 19 Thai fonts from Pubilo
    font_map = {
        "mitr": "Mitr",
        "kanit": "Kanit",
        "sarabun": "Sarabun",
        "prompt": "Prompt",
        "anuphan": "Anuphan",
        "noto": "Noto Sans Thai",
        "chonburi": "Chonburi",
        "charm": "Charm",
        "baijamjuree": "Bai Jamjuree",
        "mali": "Mali",
        "pridi": "Pridi",
        "pattaya": "Pattaya",
        "chakrapetch": "Chakra Petch",
        "sriracha": "Sriracha",
        "itim": "Itim",
        "k2d": "K2D",
        "athiti": "Athiti",
        "taviraj": "Taviraj",
        "ibmplex": "IBM Plex Sans Thai"
    }
    font_family = font_map.get(font.lower(), "Mitr")
    font_size = int(58 * (sub_scale / 100))

    # Calculate vertical position
    margin_v = max(100, int(1280 * (100 - sub_pos_y) / 100) - 80)

    # Subtitle colors (ASS hex is &H00BBGGRR&)
    def hex_to_ass(h, fallback="&H00FFFFFF&"):
        try:
            h = h.lstrip('#')
            if len(h) == 6:
                r, g, b = h[0:2], h[2:4], h[4:6]
                return f"&H00{b}{g}{r}&".upper()
        except Exception:
            pass
        return fallback

    ass_text_color = hex_to_ass(sub_color, "&H00FFFFFF&")
    ass_border_color = hex_to_ass(sub_border, "&H00000000&")

    ass_path = CLIPS_DIR / f"{job_prefix}_sub.ass"
    ass_content = f"""[Script Info]
Title: LikesAuto Studio Video
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_family},{font_size},{ass_text_color},&H000000FF,{ass_border_color},&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"
    ass_path.write_text(ass_content, encoding="utf-8")

    # 5. FFmpeg Merge & Render
    out_video_path = CLIPS_DIR / f"{job_prefix}_final.mp4"

    # Resolve BGM path
    bgm_name = (bgm_track or "bgm1").lower().strip()
    if not bgm_name.endswith(".mp3"):
        bgm_name = f"{bgm_name}.mp3"
    bgm_path = MUSIC_DIR / bgm_name
    if not bgm_path.exists():
        bgm_path = MUSIC_DIR / "bgm1.mp3"

    has_bgm = music and (bgm_track != "none") and bgm_path.exists()

    # Resolve SFX files
    pop_path = SFX_DIR / "sfx_pop.wav"
    ding_path = SFX_DIR / "sfx_ding.wav"
    has_pop = sfx_choice in ["auto"] and pop_path.exists()
    has_ding = sfx_choice in ["auto", "minimal"] and ding_path.exists()

    ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
    fonts_escaped = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")

    target_dur = f"{voice_dur + 0.35:.2f}"

    # Handle Presenter / Character Overlay
    has_presenter = bool(presenter_bytes and len(presenter_bytes) > 0)
    presenter_path = None
    is_img = True
    if has_presenter:
        ext = Path(presenter_filename).suffix.lower() if presenter_filename else ".png"
        if not ext:
            ext = ".png"
        presenter_path = CLIPS_DIR / f"{job_prefix}_presenter{ext}"
        presenter_path.write_bytes(presenter_bytes)
        is_img = ext in [".png", ".jpg", ".jpeg", ".webp"]

    # Build FFmpeg command dynamically
    cmd = ["ffmpeg", "-y"]
    cmd.extend(["-stream_loop", "-1", "-i", str(src_video_path)])  # Input 0: Source Video
    
    current_input_idx = 1
    voice_input_idx = None
    if is_dub:
        cmd.extend(["-i", str(voice_path)])  # Voice
        voice_input_idx = current_input_idx
        current_input_idx += 1

    bgm_input_idx = None
    if has_bgm:
        cmd.extend(["-stream_loop", "-1", "-i", str(bgm_path)])  # BGM
        bgm_input_idx = current_input_idx
        current_input_idx += 1

    presenter_input_idx = None
    if has_presenter:
        if is_img:
            cmd.extend(["-loop", "1", "-i", str(presenter_path)])
        else:
            cmd.extend(["-stream_loop", "-1", "-i", str(presenter_path)])
        presenter_input_idx = current_input_idx
        current_input_idx += 1

    pop_input_idx = None
    if has_pop:
        cmd.extend(["-i", str(pop_path)])
        pop_input_idx = current_input_idx
        current_input_idx += 1

    ding_input_idx = None
    if has_ding:
        cmd.extend(["-i", str(ding_path)])
        ding_input_idx = current_input_idx
        current_input_idx += 1

    # Filters
    filters = []
    # Video subtitles filter
    if has_presenter:
        filters.append(f"[0:v]subtitles='{ass_escaped}':fontsdir='{fonts_escaped}'[v_sub]")
        filters.append(f"[{presenter_input_idx}:v]scale={max(100, int(presenter_size))}:-1[p_scaled]")
        
        # Corner coordinates
        corner = (presenter_corner or "bottom_right").lower()
        if corner == "bottom_left":
            ov_pos = "x=24:y=H-h-24"
        elif corner == "top_right":
            ov_pos = "x=W-w-24:y=24"
        elif corner == "top_left":
            ov_pos = "x=24:y=24"
        else:
            ov_pos = "x=W-w-24:y=H-h-24"
            
        filters.append(f"[v_sub][p_scaled]overlay={ov_pos}[v]")
    else:
        filters.append(f"[0:v]subtitles='{ass_escaped}':fontsdir='{fonts_escaped}'[v]")

    # Audio filters with SFX (Pop at 400ms, Ding at CTA)
    cta_delay_ms = int(max(1.0, voice_dur - 3.2) * 1000)

    audio_inputs = []
    if is_dub:
        filters.append(f"[{voice_input_idx}:a]volume=1.2[voice]")
        audio_inputs.append("[voice]")
    else:
        has_src_audio = check_has_audio(src_video_path)
        if has_src_audio:
            filters.append(f"[0:a]volume=1.0[orig]")
            audio_inputs.append("[orig]")
        else:
            filters.append(f"aevalsrc=0:d={target_dur}:s=44100[orig]")
            audio_inputs.append("[orig]")

    if has_bgm:
        filters.append(f"[{bgm_input_idx}:a]volume=0.20[bgm]")
        audio_inputs.append("[bgm]")

    if has_pop:
        filters.append(f"[{pop_input_idx}:a]adelay=400|400,volume=0.85[sfx_p]")
        audio_inputs.append("[sfx_p]")

    if has_ding:
        filters.append(f"[{ding_input_idx}:a]adelay={cta_delay_ms}|{cta_delay_ms},volume=0.85[sfx_d]")
        audio_inputs.append("[sfx_d]")

    if len(audio_inputs) > 1:
        mix_inputs = "".join(audio_inputs)
        filters.append(f"{mix_inputs}amix=inputs={len(audio_inputs)}:duration=first:dropout_transition=2[a]")
    else:
        filters.append(f"{audio_inputs[0]}anull[a]")

    cmd.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-threads", "0",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-t", target_dur,
        str(out_video_path)
    ])

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed: {res.stderr[-300:]}")

    # 6. Generate Viral High-Converting Thumbnail
    thumb_path = CLIPS_DIR / f"{job_prefix}_thumb.jpg"
    try:
        create_viral_thumbnail(
            video_path=src_video_path,
            out_thumb_path=thumb_path,
            title=script_data.get("title", ""),
            detected_product=script_data.get("detected_product", ""),
            thumb_style=thumb_style
        )
    except Exception as e:
        thumb_cmd = [
            "ffmpeg", "-y",
            "-ss", "00:00:01",
            "-i", str(out_video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path)
        ]
        subprocess.run(thumb_cmd, capture_output=True)

    # Copy to latest finished reel and thumb for preview
    latest_path = BASE_DIR / "likes_auto_finished_reel.mp4"
    latest_path.write_bytes(out_video_path.read_bytes())

    latest_thumb = BASE_DIR / "likes_auto_finished_thumb.jpg"
    if thumb_path.exists():
        latest_thumb.write_bytes(thumb_path.read_bytes())

    return {
        "ok": True,
        "video_url": f"/rendered_clips/{out_video_path.name}",
        "thumbnail_url": f"/rendered_clips/{thumb_path.name}" if thumb_path.exists() else "/likes_auto_finished_thumb.jpg",
        "detected_product": script_data.get("detected_product", ""),
        "title": script_data.get("title", ""),
        "script": script_data.get("thai_script", ""),
        "caption": f"{script_data.get('caption', '')}\n\n{' '.join(script_data.get('hashtags', []))}",
        "first_comment": script_data.get("first_comment", "📌 สนใจสั่งซื้อพิกัดสินค้าจิ้มตรงนี้เลยจ้า: (ใส่ลิงก์พิกัดร้านค้าของคุณ)"),
        "hashtags": script_data.get("hashtags", []),
        "duration": voice_dur
    }
