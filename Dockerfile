# Backend Base Stage for common dependencies
FROM python:3.13-slim AS backend-base

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Create a non-root user and group
RUN groupadd --system app \
 && useradd --system --gid app --create-home --home-dir /home/app app

RUN apt-get update && apt-get install -y postgresql && rm -rf /var/lib/apt/lists/*

USER app
# Set working directory
WORKDIR /app

# Copy dependency files
COPY --chown=app:app backend .

# Install dependencies (only production by default)
RUN uv sync --frozen --no-dev

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Backend Test Stage
FROM backend-base AS test

RUN uv sync --frozen
CMD ["uv", "run", "pytest", "tests"]

# Backend Production Stage
FROM backend-base AS backend
# Expose port
EXPOSE 8000

# Run migrations and start the application
CMD ["uvicorn", "mindweaver.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Build Stage
FROM ghcr.io/cirruslabs/flutter:stable AS frontend-builder
WORKDIR /app
# Copy pubspec files first to leverage Docker cache
COPY frontend/pubspec.yaml frontend/pubspec.lock ./
RUN flutter pub get
# Copy the rest of the frontend source
COPY frontend .
RUN flutter build web --release

# Frontend Production Stage
FROM nginx:stable-alpine AS frontend
COPY --from=frontend-builder /app/build/web /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
