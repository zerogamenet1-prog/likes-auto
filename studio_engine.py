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


def create_viral_thumbnail(
    video_path: Path,
    out_thumb_path: Path,
    title: str = '',
    detected_product: str = '',
    badge_text: str = ''
) -> Path:
    temp_frame = out_thumb_path.parent / f"temp_{out_thumb_path.stem}.jpg"
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:01.000",
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(temp_frame)
    ]
    subprocess.run(cmd, capture_output=True)
    if not temp_frame.exists():
        cmd[2] = "00:00:00.200"
        subprocess.run(cmd, capture_output=True)
    
    if temp_frame.exists():
        base_img = Image.open(temp_frame).convert("RGBA")
        try:
            temp_frame.unlink(missing_ok=True)
        except Exception:
            pass
    else:
        base_img = Image.new("RGBA", (720, 1280), (24, 24, 32, 255))
        
    w, h = base_img.size
    
    # 1. Enhance contrast and vibrance
    enhancer_con = ImageEnhance.Contrast(base_img)
    base_img = enhancer_con.enhance(1.15)
    enhancer_col = ImageEnhance.Color(base_img)
    base_img = enhancer_col.enhance(1.20)
    
    # 2. Scrim Overlay
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Top gradient for badges & title readability
    top_scrim_h = int(min(380, h * 0.38))
    for y in range(top_scrim_h):
        alpha = int(175 * (1.0 - (y / top_scrim_h) ** 1.3))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
        
    # Bottom gradient for CTA readability
    bottom_scrim_h = int(min(320, h * 0.32))
    for y in range(h - bottom_scrim_h, h):
        alpha = int(195 * (((y - (h - bottom_scrim_h)) / bottom_scrim_h) ** 1.2))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    # Font setup
    font_bold_path = FONTS_DIR / "Kanit-Bold.ttf"
    if not font_bold_path.exists():
        font_bold_path = FONTS_DIR / "Prompt-Bold.ttf"
        
    f_badge_size = max(22, int(w * 0.040))
    f_title_size = max(42, int(w * 0.080))
    f_cta_size = max(26, int(w * 0.046))
    
    font_badge = ImageFont.truetype(str(font_bold_path), f_badge_size)
    font_title = ImageFont.truetype(str(font_bold_path), f_title_size)
    font_cta = ImageFont.truetype(str(font_bold_path), f_cta_size)
    
    # Top Badge: Eye-catching Red/Pink Pill with drawn Gold Star
    if not badge_text:
        badge_text = "BEST SELLER 2026 : สินค้าตัวท็อป ของแท้ 100%"
    
    bb = font_badge.getbbox(badge_text)
    txt_w = bb[2] - bb[0]
    txt_h = bb[3] - bb[1]
    star_offset = 28
    bw = txt_w + 48 + star_offset
    bh = txt_h + 18
    bx = (w - bw) // 2
    by = int(h * 0.065)
    
    # Badge shadow & background
    draw.rounded_rectangle([bx + 2, by + 3, bx + bw + 2, by + bh + 3], radius=bh // 2, fill=(0, 0, 0, 120))
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=(239, 68, 68, 245), outline=(255, 255, 255, 230), width=2)
    # Draw vector gold star on the left of badge
    draw_star(draw, (bx + 20, by + bh // 2), 9, fill=(255, 230, 0, 255))
    draw.text((bx + 20 + star_offset, by + (bh - txt_h) // 2 - 2), badge_text, font=font_badge, fill=(255, 255, 255))
    
    # Process Title Lines
    raw_title = title.strip() or detected_product.strip() or "ไอเทมเด็ด คุ้มค่าเกินราคามาก!"
    lines = wrap_thai_title(raw_title, font_title=font_title, max_px_width=int(w * 0.84))
    if len(lines) == 1:
        lines.append("คุ้มเกินราคา พลาดไม่ได้!")

    # Title Positioning & High-Contrast Typography
    ty = by + bh + int(h * 0.035)
    line_colors = [
        (255, 238, 0, 255),   # Bright Neon Yellow
        (255, 255, 255, 255), # Crisp Pure White
        (56, 189, 248, 255)   # Radiant Cyan / Light Blue
    ]
    
    for i, line in enumerate(lines[:3]):
        t_bb = font_title.getbbox(line)
        tw = t_bb[2] - t_bb[0]
        th = t_bb[3] - t_bb[1]
        tx = (w - tw) // 2
        
        # Heavy Stroke / Outline
        stroke_w = max(2, int(w * 0.006))
        for dx in range(-stroke_w, stroke_w + 1):
            for dy in range(-stroke_w, stroke_w + 1):
                if dx or dy:
                    draw.text((tx + dx, ty + dy), line, font=font_title, fill=(0, 0, 0, 255))
                    
        # Deep drop shadow
        draw.text((tx + 3, ty + 4), line, font=font_title, fill=(0, 0, 0, 230))
        
        # Fill color
        col = line_colors[i % len(line_colors)]
        draw.text((tx, ty), line, font=font_title, fill=col)
        ty += th + int(h * 0.022)

    # Bottom CTA Pill Button (Shopee / Reels action trigger)
    cta_text = "ชี้พิกัดส่วนลดในคลิป >> กดสั่งซื้อด่วน"
    cb = font_cta.getbbox(cta_text)
    cw = (cb[2] - cb[0]) + 52
    ch = (cb[3] - cb[1]) + 24
    cx = (w - cw) // 2
    cy = h - ch - int(h * 0.08)
    
    draw.rounded_rectangle([cx + 3, cy + 4, cx + cw + 3, cy + ch + 4], radius=16, fill=(0, 0, 0, 120))
    draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=16, fill=(16, 185, 129, 245), outline=(255, 255, 255, 230), width=3)
    draw.text((cx + (cw - (cb[2] - cb[0])) // 2, cy + (ch - (cb[3] - cb[1])) // 2 - 2), cta_text, font=font_cta, fill=(255, 255, 255))

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
    api_key: str = DEFAULT_API_KEY
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
            detected_product=script_data.get("detected_product", "")
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
