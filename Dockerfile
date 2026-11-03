FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ALLOW_DEMO_SEED=1
# Debian bookworm packs tessdata under tesseract-ocr/5/
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libzbar0 curl \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-tha \
    && rm -rf /var/lib/apt/lists/* \
    && (test -d "$TESSDATA_PREFIX" || (test -d /usr/share/tesseract-ocr/4.00/tessdata && ln -s /usr/share/tesseract-ocr/4.00/tessdata /usr/share/tesseract-ocr/5/tessdata) || true) \
    && tesseract --version \
    && tesseract --list-langs \
    && python -c "import shutil; assert shutil.which('tesseract')"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/start.sh
EXPOSE 8000
CMD ["/app/start.sh"]
