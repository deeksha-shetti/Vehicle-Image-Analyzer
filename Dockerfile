# ==========================================
# Multi-Stage Unified Dockerfile
# Frontend + Express API + Python Worker
# ==========================================

# 1. Build Stage for Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 2. Main Runtime Stage (Python 3.10 + Node.js + OCR Tools)
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (Node.js 18, Tesseract OCR, OpenCV runtime libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python Worker Dependencies
COPY worker/requirements.txt /app/worker/
RUN pip install --no-cache-dir -r /app/worker/requirements.txt

# Install API Dependencies
COPY api/package*.json /app/api/
RUN cd /app/api && npm install --only=production

# Copy Application Source Code
COPY api/ /app/api/
COPY worker/ /app/worker/

# Copy Built Frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy & prepare startup supervisor script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Environment Defaults
ENV PORT=3000
ENV NODE_ENV=production
EXPOSE 3000

CMD ["/bin/bash", "/app/start.sh"]
