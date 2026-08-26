import re

PACKS = {
    "violet": {
        "label": "Night Violet",
        "hint": "\u0e42\u0e17\u0e19\u0e21\u0e37\u0e14\u0e04\u0e37\u0e19 \u0e21\u0e48\u0e27\u0e07\u0e2a\u0e49\u0e21 \u2014 \u0e42\u0e17\u0e19\u0e2b\u0e25\u0e31\u0e01\u0e02\u0e2d\u0e07\u0e40\u0e27\u0e47\u0e1a",
        "bg": "#080614",
        "text": "#f6f2ff",
        "muted": "#b9adce",
        "accent": "#a855f7",
        "accent2": "#c026d3",
        "cyan": "#67e8f9",
    },
    "navy": {
        "label": "Midnight Navy",
        "hint": "\u0e42\u0e17\u0e19\u0e01\u0e25\u0e32\u0e07\u0e04\u0e37\u0e19\u0e40\u0e22\u0e47\u0e19 \u0e04\u0e23\u0e32\u0e21\u0e21\u0e48\u0e27\u0e07 \u2014 \u0e04\u0e39\u0e48\u0e42\u0e17\u0e19\u0e40\u0e14\u0e35\u0e22\u0e27\u0e01\u0e31\u0e19",
        "bg": "#0b1020",
        "text": "#eef2ff",
        "muted": "#a8b4cc",
        "accent": "#7c6cf0",
        "accent2": "#6366f1",
        "cyan": "#38bdf8",
    },
    "light": {
        "label": "Soft Light",
        "hint": "\u0e1e\u0e37\u0e49\u0e19\u0e2a\u0e27\u0e48\u0e32\u0e07 \u0e21\u0e48\u0e27\u0e07\u0e14\u0e35\u0e22\u0e27 \u2014 \u0e2d\u0e48\u0e32\u0e19\u0e07\u0e48\u0e32\u0e22\u0e15\u0e2d\u0e19\u0e01\u0e25\u0e32\u0e07\u0e27\u0e31\u0e19",
        "bg": "#f5f2fb",
        "text": "#1a1430",
        "muted": "#564c68",
        "accent": "#7c3aed",
        "accent2": "#9333ea",
        "cyan": "#0e7490",
    },
}


COLOR_FIELDS = [
    ("bg", "\u0e1e\u0e37\u0e49\u0e19\u0e2b\u0e25\u0e31\u0e07"),
    ("text", "\u0e15\u0e31\u0e27\u0e2d\u0e31\u0e01\u0e29\u0e23"),
    ("muted", "\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e23\u0e2d\u0e07"),
    ("accent", "\u0e2a\u0e35\u0e2b\u0e25\u0e31\u0e01"),
    ("accent2", "\u0e2a\u0e35\u0e23\u0e2d\u0e07"),
    ("cyan", "\u0e2a\u0e35\u0e44\u0e2e\u0e44\u0e25\u0e15\u0e4c"),
]

KEYS = ("bg", "text", "muted", "accent", "accent2", "cyan")
HEX = re.compile(r"^#([0-9a-fA-F]{6})$")


def is_hex(value):
    return bool(value and HEX.match(str(value).strip()))


def clean_hex(value, fallback):
    raw = (value or "").strip()
    if is_hex(raw):
        return raw.lower()
    return fallback


def pack_id(value):
    key = (value or "violet").strip().lower()
    return key if key in PACKS else "violet"


def theme_switch_on(settings):
    return (settings or {}).get("theme_switch", "1") != "0"


def theme_pack(settings):
    return pack_id((settings or {}).get("theme_pack"))


def pack_colors(settings, pack):
    pack = pack_id(pack)
    base = PACKS[pack]
    out = {k: base[k] for k in KEYS}
    out["label"] = base["label"]
    out["hint"] = base["hint"]
    s = settings or {}
    for key in KEYS:
        out[key] = clean_hex(s.get("theme_%s_%s" % (pack, key)), base[key])
    return out


def _mix(hex_color, other, amount):
    a = hex_color.lstrip("#")
    b = other.lstrip("#")
    ar = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    br = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    mix = [int(ar[i] * (1 - amount) + br[i] * amount) for i in range(3)]
    return "#%02x%02x%02x" % tuple(mix)


def _rgba(hex_color, alpha):
    raw = hex_color.lstrip("#")
    r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    return "rgba(%s,%s,%s,%s)" % (r, g, b, alpha)


def css_for_pack(settings, pack):
    c = pack_colors(settings, pack)
    bg = c["bg"]
    text = c["text"]
    muted = c["muted"]
    accent = c["accent"]
    accent2 = c["accent2"]
    cyan = c["cyan"]
    if pack == "light":
        card = "#ffffff"
        surface = "#fbf9ff"
        stroke = _rgba("#1a1430", 0.12)
        soft = _mix("#ffffff", accent, 0.10)
        glow = _rgba(accent, 0.16)
        glow2 = _rgba(accent2, 0.12)
        glow3 = _rgba(cyan, 0.10)
        nav = "rgba(255,255,255,.88)"
        nav_scrolled = "rgba(255,255,255,.96)"
        ink = text
        ink_dim = muted
        foot = "#ffffff"
        btn_text = "#ffffff"
        grad_text = "linear-gradient(90deg,%s 0%%,%s 55%%,%s 100%%)" % (accent, accent2, cyan)
    else:
        card = _mix(bg, "#ffffff", 0.08)
        surface = _mix(bg, "#ffffff", 0.05)
        stroke = _rgba("#ffffff", 0.12)
        soft = _mix(bg, accent, 0.18)
        glow = _rgba(accent, 0.42)
        glow2 = _rgba(accent2, 0.28)
        glow3 = _rgba(cyan, 0.18)
        nav = _rgba(bg, 0.48)
        nav_scrolled = _rgba(_mix(bg, "#000000", 0.22), 0.90)
        ink = "#ffffff"
        ink_dim = _rgba("#ffffff", 0.72)
        foot = _mix(bg, "#000000", 0.18)
        btn_text = "#ffffff"
        grad_text = "linear-gradient(90deg,%s 0%%,%s 52%%,%s 100%%)" % (accent2, accent, cyan)
    grad = "linear-gradient(135deg,%s 0%%,%s 52%%,%s 100%%)" % (accent, accent2, cyan)
    return {
        "bg": bg, "text": text, "muted": muted, "accent": accent, "accent2": accent2, "cyan": cyan,
        "card": card, "surface": surface, "stroke": stroke, "soft": soft,
        "glow": glow, "glow2": glow2, "glow3": glow3, "grad": grad, "grad_text": grad_text,
        "nav": nav, "nav_scrolled": nav_scrolled, "ink": ink, "ink_dim": ink_dim, "foot": foot,
        "btn_text": btn_text,
    }


def theme_css(settings):
    blocks = []
    for pack in PACKS:
        v = css_for_pack(settings, pack)
        sel = 'html[data-la-pack="%s"]' % pack
        blocks.append(
            "%s {\n"
            "  --la-bg:%s; --la-text:%s; --la-muted:%s; --la-accent:%s; --la-accent2:%s; --la-cyan:%s;\n"
            "  --la-card:%s; --la-surface:%s; --la-stroke:%s; --la-soft:%s;\n"
            "  --la-glow:%s; --la-glow2:%s; --la-glow3:%s; --la-grad:%s; --la-grad-text:%s;\n"
            "  --la-nav:%s; --la-nav-scrolled:%s; --la-ink:%s; --la-ink-dim:%s; --la-foot:%s;\n"
            "  --la-pink:%s; --la-purple:%s; --la-violet:%s; --la-link:%s;\n"
            "  --la-btn:%s; --la-btn-text:%s; --la-shadow:0 16px 40px %s;\n"
            "  --bg:%s; --bg-2:%s; --card:%s; --line:%s; --text:%s; --muted:%s;\n"
            "  --violet:%s; --pink:%s; --cyan:%s; --grad:%s;\n"
            "  --primary-color:%s; --primary-color-dark:%s; --primary-gradient:%s;\n"
            "  --body-bg:%s; --card-bg:%s; --text-primary:%s; --text-secondary:%s; --border-color:%s;\n"
            "}" % (
                sel,
                v["bg"], v["text"], v["muted"], v["accent"], v["accent2"], v["cyan"],
                v["card"], v["surface"], v["stroke"], v["soft"],
                v["glow"], v["glow2"], v["glow3"], v["grad"], v["grad_text"],
                v["nav"], v["nav_scrolled"], v["ink"], v["ink_dim"], v["foot"],
                v["accent2"], v["accent"], v["accent"], v["cyan"],
                v["grad"], v["btn_text"], v["glow"],
                v["bg"], v["surface"], v["card"], v["stroke"], v["text"], v["muted"],
                v["accent"], v["accent2"], v["cyan"], v["grad"],
                v["accent"], v["accent2"], v["grad"],
                v["bg"], v["card"], v["text"], v["muted"], v["stroke"],
            )
        )
    return "\n".join(blocks)


def public_theme_ctx(settings=None):
    s = settings or {}
    packs = []
    for key in PACKS:
        item = pack_colors(s, key)
        item["id"] = key
        packs.append(item)
    return {
        "theme_pack": theme_pack(s),
        "theme_switch": theme_switch_on(s),
        "theme_css": theme_css(s),
        "theme_packs": packs,
        "theme_fields": COLOR_FIELDS,
    }


def save_theme(form):
    from db import save_settings
    values = {}
    pack = pack_id(form.get("theme_pack"))
    values["theme_pack"] = pack
    values["theme_switch"] = "1" if form.get("theme_switch") else "0"
    action = (form.get("action") or "save").strip()
    if action.startswith("reset:"):
        reset_pack = pack_id(action.split(":", 1)[1])
        for key in KEYS:
            values["theme_%s_%s" % (reset_pack, key)] = PACKS[reset_pack][key]
        save_settings(values)
        return
    for pid in PACKS:
        for key in KEYS:
            field = "theme_%s_%s" % (pid, key)
            values[field] = clean_hex(form.get(field), PACKS[pid][key])
    save_settings(values)


def default_settings():
    out = {"theme_pack": "violet", "theme_switch": "1"}
    for pid, meta in PACKS.items():
        for key in KEYS:
            out["theme_%s_%s" % (pid, key)] = meta[key]
    return out
