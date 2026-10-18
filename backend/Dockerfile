# Imagen del backend (FastAPI). Incluye ffmpeg (extraer audio) y Node.js (lo necesita yt-dlp para YouTube).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg nodejs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Carpeta de archivos subidos (en la nube gratuita el disco es efímero)
RUN mkdir -p /app/subidas

EXPOSE 8000

# Render, Hugging Face Spaces, etc. inyectan $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
