#!/usr/bin/env bash
# Render native Python has no apt — vendor a static tesseract + eng tessdata.
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -r requirements.txt

VENDOR="vendor/tesseract"
mkdir -p "$VENDOR/tessdata"
if [ ! -x "$VENDOR/tesseract" ]; then
  echo "Downloading static tesseract…"
  curl -fsSL -o /tmp/tesseract.x86_64 \
    "https://github.com/DanielMYT/tesseract-static/releases/download/tesseract-5.5.0/tesseract.x86_64"
  chmod +x /tmp/tesseract.x86_64
  mv /tmp/tesseract.x86_64 "$VENDOR/tesseract"
fi
if [ ! -f "$VENDOR/tessdata/eng.traineddata" ]; then
  echo "Downloading eng.traineddata…"
  curl -fsSL -o "$VENDOR/tessdata/eng.traineddata" \
    "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"
fi
"$VENDOR/tesseract" --list-langs || true
echo "render_build ok"
