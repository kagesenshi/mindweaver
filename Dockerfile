# Frontend Builder
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

# Backend Base
FROM python:3.13-slim AS backend-base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
RUN apt-get update && apt-get install -y libpq-dev postgresql && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/src ./src
COPY backend/migration ./migration
COPY backend/alembic.ini ./
COPY backend/README.md ./
COPY backend/tests ./tests

# Create non-root user
RUN groupadd -r app && useradd -m -g app -s /sbin/nologin app && chown app:app -R /app 
USER app
# Install prod dependencies
RUN uv sync --frozen --no-dev

# Test Stage
FROM backend-base AS test
RUN uv sync --frozen
CMD ["uv", "run", "pytest", "tests"]

# Final Image
FROM python:3.13-slim
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Copy venv from backend-base
COPY --from=backend-base /app/.venv /app/.venv

# Copy code
COPY backend/src /app/src
COPY backend/migration /app/migration
COPY backend/alembic.ini /app/alembic.ini

# Copy frontend
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Configs
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

RUN groupadd -r app && useradd -r -g app -s /sbin/nologin app

# Set ownership
RUN chown -R app:app /app /var/lib/nginx /var/log/nginx /usr/share/nginx/html

USER app

EXPOSE 8080
CMD ["/app/start.sh"]
