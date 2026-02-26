# Mindweaver

Mindweaver is a 100% open-source data & AI orchestration platform, providing an all-in-one solution for data warehousing, data lakes, and AI platforms.

- **Orchestration**: Currently provides orchestration capabilities to deploy key data platform components such as PostgreSQL, Trino, Airflow, Superset, Kafka, and others.
- **Future Roadmap**:
    - **GraphRAG Platform**: Comprehensive support for GraphRAG and ontology management.
    - **SQL RAG**: Implementing SQL RAG with Trino integration.
    - **AI Visualization**: AI-powered dashboard and visualization creation.
    - **Advanced Modeling**: Data Vault modeling support.
- **Roadmap Targets**:
    - **Version 0.1**: Focus on Data Platform deployment orchestration capability.
    - **Version 0.2**: Introduction of Data Ingestion support.
    - **Version 0.3**: Introduction of RAG support.
    - **Version 0.4**: Introduction of Data Vault support.
- **Current Focus**: Priority is placed on streamlining the deployment of dependency components to establish a robust foundation.

## Prerequisites

*   **Python 3.13+**
*   **Node.js** (v18+ recommended) and **npm**
*   **uv** (Python package manager): [Installation instructions](https://github.com/astral-sh/uv)
*   **Docker** and **Docker Compose** (for running backing services)
*   **CloudNativePG Operator** (for Kubernetes deployments): [Installation guide](https://cloudnative-pg.io/documentation/current/installation_operator/)

## Helm Installation

You can install Mindweaver on Kubernetes using the Helm chart hosted on GHCR.

> [!IMPORTANT]
> The **CloudNativePG (CNPG) Operator** must be installed in your cluster before installing the Mindweaver chart, as it is used to manage the PostgreSQL database.

```bash
# 1. Install CNPG Operator (if not already installed)
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm upgrade --install cnpg \
  --namespace cnpg-system \
  --create-namespace \
  cnpg/cloudnative-pg

# 2. Install the Mindweaver chart
helm install mindweaver oci://ghcr.io/kagesenshi/mindweaver/charts/mindweaver --version 0.1.0
```

## Development Environment Setup

### 1. Start Backing Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

This will start:
*   PostgreSQL on `localhost:5432` (User: `postgres`, Password: `password`, DB: `mindweaver`)
*   Redis on `localhost:6379`

### 2. Application Setup

Run the unified setup script from the root directory:

```bash
python setup-dev.py
```

This will automatically:
- Install backend dependencies using `uv`.
- Install frontend dependencies using `npm`.
- Run database migrations.
- Suggest an encryption key.

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
