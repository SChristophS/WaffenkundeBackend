FROM python:3.11-slim

WORKDIR /app

# System-Dependencies (optional, hier minimal gehalten)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Requirements zuerst, damit Docker-Layer gecached werden können
COPY requirements.txt requirements.lock ./ 
RUN pip install --upgrade pip && pip install -r requirements.txt

# Restlichen Code kopieren
COPY . .

# Standard-Env für Port (kann per Docker/Compose überschrieben werden)
ENV PORT=2001

EXPOSE 2001

# Gunicorn mit eventlet (für Flask-SocketIO)
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:2001", "run:app"]


