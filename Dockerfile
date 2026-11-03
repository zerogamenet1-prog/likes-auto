FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ALLOW_DEMO_SEED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libzbar0 curl \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-tha \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/start.sh
EXPOSE 8000
CMD ["/app/start.sh"]
