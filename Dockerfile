FROM python:3.12-slim

# libheif runtime for HEIC thumbnails; ffmpeg optional for future video thumbs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libheif1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

ENV PORT=8080 \
    GPMC_CONFIG_DIR=/config \
    GPMC_SYNC_DIR=/sync \
    GPMC_HOME=/config/gpmc_home

RUN mkdir -p /config /sync

EXPOSE 8080
VOLUME ["/config", "/sync"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8080\")}/api/health').read()" || exit 1

CMD ["python", "run.py"]
