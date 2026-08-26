from pathlib import Path
p = Path(r"C:\Users\VIPLIKE\Desktop\likes-auto.com\py-app\templates\admin\settings_hub.html")
t = p.read_text(encoding="utf-8")
t = t.replace("\u0e44\u0e0b\u0e14\u0e4c\u0e1a\u0e32\u0e23)", "\u0e44\u0e0b\u0e14\u0e4c\u0e1a\u0e32\u0e23)")
# fix missing mai-tho on bar if present as bar without last tone - current may already be บาร์
t = t.replace("\u0e0b\u0e48\u0e2d\u0e19\u0e40\u0e2e\u0e19\u0e38", "\u0e0b\u0e48\u0e2d\u0e19\u0e40\u0e21\u0e19\u0e39")
p.write_text(t.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
print("typos", "\u0e0b\u0e48\u0e2d\u0e19\u0e40\u0e21\u0e19\u0e39" in t)
