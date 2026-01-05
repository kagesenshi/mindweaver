# Mindweaver Development Setup

This guide outlines the steps to set up the development environment for Mindweaver, a full-stack application with a Python FastAPI backend and a Flutter frontend.

## Prerequisites

Ensure you have the following installed on your system:

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Flutter SDK](https://docs.flutter.dev/get-started/install)
- [Docker](https://docs.docker.com/get-docker/) (for running the database)

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mindweaver
```

### 2. Start Infrastructure

Start the PostgreSQL database using Docker Compose:

```bash
docker compose up -d
```

### 3. Backend Setup

Navigate to the backend directory, install dependencies, and run database migrations:

```bash
cd backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

cd ..
```

### 4. Frontend Setup

Navigate to the frontend directory, install dependencies, and generate code:

```bash
cd frontend

# Install dependencies
flutter pub get

# Generate serializers
flutter pub run build_runner build --delete-conflicting-outputs

cd ..
```

## Running the Application

To start both the backend and frontend development servers simultaneously, run the helper script from the root directory:

```bash
python3 start-dev.py
```

- **Frontend**: Accessible at `http://localhost:3000`
- **Backend**: Accessible at `http://localhost:8000`

The script monitors both processes and will terminate them if you press `Ctrl+C` or if one of them exits.
