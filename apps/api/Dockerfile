# SkinSync API and worker image (same image, different command).
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Tesseract for label OCR; libgl not needed with opencv-python-headless.
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app
COPY apps/api/requirements.txt .
# pip is only needed to build the image. Removing it also removes its bundled copies of urllib3,
# msgpack and setuptools, which image scanners report even though the app never uses them.
RUN pip install -r requirements.txt \
    && pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip
COPY apps/api/ /app/
COPY knowledge/ /knowledge/
RUN mkdir -p /data/storage && chown -R app:app /data
USER app
ENV SKINSYNC_KNOWLEDGE_DIR=/knowledge SKINSYNC_STORAGE_DIR=/data/storage
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').status==200 else 1)"
CMD ["sh", "-c", "alembic upgrade head && python -m skinsync.cli bootstrap && exec uvicorn skinsync.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*' --workers ${API_WORKERS:-2}"]
