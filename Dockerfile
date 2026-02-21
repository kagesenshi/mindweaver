# Frontend Builder
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
ENV VITE_API_URL=/api/v1
RUN npm run build

# Backend Base & Final Image
FROM python:3.13-slim AS backend-base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy backend configuration
COPY backend/pyproject.toml backend/uv.lock ./

# Install production dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY backend/src ./src
COPY backend/migration ./migration
COPY backend/alembic.ini ./
COPY backend/README.md ./

# Set up user and permissions
RUN groupadd -r app && useradd -m -g app -s /sbin/nologin app && \
    mkdir -p /var/lib/nginx /var/log/nginx && \
    chown -R app:app /app /var/lib/nginx /var/log/nginx

# Test Stage
FROM backend-base AS test
COPY backend/tests ./tests
USER app
RUN uv sync --frozen
CMD ["uv", "run", "pytest", "tests"]

# Final Image
FROM backend-base
# Copy assets from frontend-builder
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy configurations
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && \
    chown app:app /app/start.sh /usr/share/nginx/html

USER app
EXPOSE 8080
CMD ["/app/start.sh"]
