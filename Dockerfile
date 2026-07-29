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

# Install Helm and kubectl required by cluster actions
RUN apt-get update && apt-get install -y curl ca-certificates tar \
    && cd /tmp \
    && curl -fsSLO https://get.helm.sh/helm-v3.21.1-linux-amd64.tar.gz \
    && curl -fsSLO https://get.helm.sh/helm-v3.21.1-linux-amd64.tar.gz.sha256sum \
    && sha256sum -c helm-v3.21.1-linux-amd64.tar.gz.sha256sum \
    && tar -xzf helm-v3.21.1-linux-amd64.tar.gz \
    && install -m 0755 linux-amd64/helm /usr/local/bin/helm \
    && curl -fsSLo /usr/local/bin/kubectl https://dl.k8s.io/release/v1.36.2/bin/linux/amd64/kubectl \
    && curl -fsSLo /tmp/kubectl.sha256 https://dl.k8s.io/release/v1.36.2/bin/linux/amd64/kubectl.sha256 \
    && echo "$(cat /tmp/kubectl.sha256)  /usr/local/bin/kubectl" | sha256sum --check \
    && chmod 0755 /usr/local/bin/kubectl \
    && rm -rf /var/lib/apt/lists/* /tmp/linux-amd64 \
       /tmp/helm-v3.21.1-linux-amd64.tar.gz \
       /tmp/helm-v3.21.1-linux-amd64.tar.gz.sha256sum \
       /tmp/kubectl.sha256

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
COPY container/nginx.conf /etc/nginx/nginx.conf
COPY container/start.sh /app/start.sh
RUN chmod +x /app/start.sh && \
    chown app:app /app/start.sh /usr/share/nginx/html

USER app
EXPOSE 8080
CMD ["/app/start.sh"]
