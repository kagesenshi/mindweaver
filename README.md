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

## Kubernetes Deployment Requirements

### Prerequisites

*   **Kubernetes**: v1.28+ (tested with k3s)
*   **Load Balancer**: Required for external access to services.
    *   **Self-hosted** (`k3s` with `docker` containerd): **[MetalLB](https://metallb.io/)** is recommended.
    *   **Cloud providers** (EKS, GKE, AKS): Default cloud load balancer.
    *   **On-premise**: Ensure firewall rules are configured for the required ports.

### Install k3s with Load Balancer Support

For self-hosted Kubernetes using **k3s**, follow these steps:

```bash
# 1. Install k3s
curl -sfL https://get.k3s.io | sh -

# 2. Start k3s
k3s server \
    --disable traefik \
    --disable servicelb \
    --cluster-cidr 192.168.0.0/16,fd42:0:0/64 \
    --service-cidr 10.96.0.0/12,fd43:0:0/64 \
```

**For a single node, k3s automatically sets up the necessary configuration** without any extra setup needed.

### Set up MetalLB

After k3s is installed, configure **MetalLB** for external access to services:

1.  **Obtain a physical device or virtual router** that provides external IP addresses.
    -   Use your **cloud provider's virtual router** options like AWS EC2, Azure VM, or GCE.
    -   Ensure the device provides IP addresses through the **physical links** at the bottom.

3.  **Choose the right MetalLB mode** for your network:
    -   **Layer 2** mode: Required when using a single homogeneous network. Provides cluster-wide IP routing.
    -   **Layer 3** mode: Required when using a multi-homed, homogeneous, or heterogeneous network with a physical router.

If your secondary IP and primary IP are in the same /24 CIDR, MetalLB will instruct k3s for Layer 2 routing and advertise the secondary one.

Install MetalLB:

```bash
# Apply MetalLB manifest
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/main/manifests/metallb.yaml

# Wait for MetalLB controller pod to be created
kubectl wait --for=condition=ready pod --selector app=metallb -n metallb-system --timeout=120s
```

**Make sure to check MetalLB status using `kubectl get pods -n metallb-system` and ensure it's running successfully.**

## Development Environment Setup

### 1. Start Backing Services

Start PostgreSQL and Redis (the backing services) using Docker Compose:

```bash
docker compose up -d
```

This will start:
*   PostgreSQL on `localhost:5432` (User: `postgres`, Password: `password`, DB: `mindweaver`)
*   Redis on `localhost:6379`

If you would like to run the backend application services (`web`, `scheduler`, and `worker`) inside Docker container environments with code hot-reloading from volume mounts, run docker-compose specifying the `app` profile:

```bash
docker compose --profile app up -d
```

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

### Running Locally
From the **root directory** of the repository, run the development script:

```bash
python start-dev.py
```

This script will start:
*   Frontend development server (typically on `http://localhost:3000`)
*   Backend API server (on `http://localhost:8000`)
*   Celery Scheduler
*   Celery Worker

### Running in Docker
If you started the application using `docker compose --profile app up -d`, the application containers are automatically running. The FastAPI backend will be exposed on `http://localhost:8000` and the React frontend development server will be exposed on `http://localhost:3000`.

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
