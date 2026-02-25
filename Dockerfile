# Stage 1: Build frontend
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + static files
FROM python:3.12-slim
WORKDIR /app
COPY backend/ .
COPY allowed_emails.txt .
RUN pip install --no-cache-dir .
COPY --from=frontend /app/frontend/dist ./static

# Cloud Run sets PORT env var (default 8080)
ENV PORT=8080
CMD python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
