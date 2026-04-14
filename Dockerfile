# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS frontend_builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements/base.txt /tmp/base.txt
RUN pip install --no-cache-dir -r /tmp/base.txt

COPY backend/ /app/backend/
COPY docs/validation/allowlist.txt /app/docs/validation/allowlist.txt
COPY --from=frontend_builder /app/frontend/dist /app/frontend_dist
COPY scripts/start_container.sh /app/scripts/start_container.sh

RUN chmod +x /app/scripts/start_container.sh

ENV PORT=8000
EXPOSE 8000

CMD ["/app/scripts/start_container.sh"]
