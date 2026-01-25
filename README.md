# Mindweaver

This is a full-stack application with a Python backend and a React frontend.

## Prerequisites

*   **Python 3.13+**
*   **Node.js** (v18+ recommended) and **npm**
*   **uv** (Python package manager): [Installation instructions](https://github.com/astral-sh/uv)
*   **Docker** and **Docker Compose** (for running backing services)

## Development Environment Setup

### 1. Start Backing Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

This will start:
*   PostgreSQL on `localhost:5432` (User: `postgres`, Password: `password`, DB: `mindweaver`)
*   Redis on `localhost:6379`

### 2. Backend Setup

Navigate to the `backend` directory:

```bash
cd backend
```

Install dependencies:

```bash
uv sync
```

Configure environment variables. Create a `.env` file in the `backend` directory (or export these variables in your shell):

```bash
echo "MINDWEAVER_DB_USER=postgres" > .env
echo "MINDWEAVER_DB_PASS=password" >> .env
```

Run database migrations:

```bash
uv run mindweaver db migrate
```

(Optional) Generate an encryption key:

```bash
uv run mindweaver crypto generate-key
```

### 3. Frontend Setup

Navigate to the `frontend` directory:

```bash
cd ../frontend
```

Install dependencies:

```bash
npm install
```

## Running the Application

From the **root directory** of the repository, run the development script:

```bash
python start-dev.py
```

This script will start:
*   Frontend development server (typically on `http://localhost:3000`)
*   Backend API server (on `http://localhost:8000`)
*   Celery Scheduler
*   Celery Worker

## Running Tests

### Backend

To run backend tests:

```bash
uv run --package mindweaver pytest backend/tests
```

### Frontend

The frontend is a React application built with Vite. Currently, there is no test script defined in `frontend/package.json`.

## Architecture

*   **Backend**: Python, FastAPI, SQLModel, Celery, Alembic. Located in `backend/`.
*   **Frontend**: React, Vite, Tailwind CSS. Located in `frontend/`.
*   **Infrastructure**: Docker Compose for local development (Postgres, Redis). Kubernetes manifests in `k8s/`.
