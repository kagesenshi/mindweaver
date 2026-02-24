# Mindweaver Developer Documentation

Welcome to the Mindweaver developer guide. This documentation is intended for contributors who want to extend, enhance, or debug the platform.

## Chapters

1. **[Architecture](architecture.md)**: Deep dive into the internal design and technologies.
2. **[Backend Development](backend.md)**: Guide on the `fw` layer, services, and platform services.
3. **[Frontend Development](frontend.md)**: Working with React, Dynamic Forms, and providers.
4. **[Testing](testing.md)**: How to write and run backend and frontend tests.

## Technical Stack

- **Backend**: FastAPI, SQLModel (SQLAlchemy based), Pydantic.
- **Frontend**: React, Vite, Tailwind CSS.
- **Background Tasks**: Celery, Redis.
- **Orchestration**: ArgoCD, Kubernetes.
- **Environment Management**: `uv`.

## Developer Environment

Please ensure you have followed the setup instructions in the **[Getting Started](../user/getting-started.md)** guide before diving into development.
