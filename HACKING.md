# Hacking Mindweaver

Welcome to the Mindweaver development guide. This document provides technical details on how to set up your environment, follow coding standards, and navigate the project's unique architecture.

---

## 🛠️ Development Environment Setup

### 1. Prerequisites
- **Python 3.13+**
- **Node.js v18+** & **npm**
- **uv** (Python package manager)
- **Docker** & **Docker Compose**

### 2. Infrastructure
Mindweaver relies on PostgreSQL and Redis. Start them using the root Docker Compose:
```bash
docker-compose up -d
```

### 3. Setup the Application
Mindweaver provides a unified setup script to install dependencies and initialize the database:
```bash
python setup-dev.py
```

This script will:
1.  Run `uv sync` in the `backend/` directory.
2.  Run `npm install` in the `frontend/` directory.
3.  Run database migrations.
4.  Generate a suggested encryption key.

### 4. Environment Configuration
Edit `.env` file in the `backend/` directory if you need to override defaults:
```env
MINDWEAVER_FERNET_KEY=<your-generated-key>
```
*Note: Database defaults (postgres/password) are already configured for local development.*

### 5. Database Migrations
If you make changes to the SQLModel definitions in `backend/src/mindweaver/fw/model.py` or other model files, you must generate a migration:

1.  **Generate a revision**:
    ```bash
    cd backend
    uv run mindweaver db revision -m "description of changes" --autogenerate
    ```
2.  **Review the migration**: Check the newly created file in `backend/migration/versions/`.
3.  **Apply the migration**:
    ```bash
    uv run mindweaver db migrate
    ```

### 6. Running the Stack
Use the development script from the root directory:
```bash
python start-dev.py
```
This starts the Backend (8000), Frontend (3000), Celery Scheduler, and Celery Worker.

---

## 🏗️ Backend Development

### Core Patterns
Mindweaver uses a structured CRUD framework built on **FastAPI** and **SQLModel**.

1.  **Models**: Use `NamedBase` (standard) or `ProjectScopedNamedBase` (multi-tenant).
2.  **Services**: Inherit from `Service`. This provides automatic CRUD endpoints, validation, and JSON:API compliant responses.
3.  **Hooks**: Use `@before_create`, `@after_update`, etc., in your service classes to inject custom logic.
4.  **Platform Services**: Inherit from `PlatformService` for managing external resources (Kubernetes). These use Jinja2 templates in `backend/src/mindweaver/templates`.

### Sensitive Data
Sensitive fields (passwords, tokens) must be handled via `SecretHandlerMixin`.
- List fields in `redacted_fields()`.
- The API will return `__REDACTED__` for these fields.
- Use `__CLEAR__` to empty a field or send a new value to re-encrypt.

### CLI reference
- `uv run mindweaver db revision -m "description" --autogenerate`: Create a new migration.
- `uv run mindweaver db migrate`: Apply migrations.
- `uv run mindweaver crypto rotate-key --old-key X --new-key Y`: Rotate encryption keys for database records.

---

## 🎨 Frontend Development

### Dynamic Forms
Mindweaver leverages **Dynamic Forms** that are reflexively built from backend metadata.
- Most CRUD UI is handled automatically by passing the `entityPath` to the `DynamicForm` component.
- UX properties (like field order, labels, and spans) should be configured in the **Backend Service** via the `widgets()` method.

### State Management
- Prefer local state and context for small clusters of components.
- API interactions are centralized in `frontend/src/api.js`.

---

## 🧪 Testing

### Backend
Tests use `pytest` and a real PostgreSQL instance (via `pytest-postgresql`).
```bash
uv run --package mindweaver pytest backend/tests
```
- **Fixtures**: Use `crud_client` for standard testing and `project_scoped_crud_client` for multi-tenant features.

### Docker-based Testing
To run the full suite (including system-level checks) in a containerized environment:
```bash
./run-all-tests.sh
```
This builds a test-targeted Docker image and runs it.

---

## 📜 Coding Standards
- **Standard**: Follow [PROJECT_CONSTITUTION.md](PROJECT_CONSTITUTION.md).
- **Imports**: Always at the top of the file. No in-function imports unless strictly necessary for pickling or circular dependency resolution.
- **Async**: Use `async`/`await` for all I/O operations.
- **Docstrings**: All functions must have descriptive docstrings.

---

## ❓ Troubleshooting
- **Database Issues**: If migrations are stuck, you can reset the public schema (dev only) with `uv run mindweaver db reset` (requires `MINDWEAVER_ENABLE_DB_RESET=true`).
- **Celery**: If tasks aren't executing, ensure Redis is running and the worker is healthy in the `start-dev.py` logs.
