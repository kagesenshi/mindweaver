# Core Concepts

Understanding the core concepts of Mindweaver will help you manage your data platform components effectively.

## Projects

In Mindweaver, a **Project** is a logical grouping of resources. Most metadata and platform components are scoped to a project. This allows you to organize your infrastructure by environment (e.g., Development, Staging, Production), team, or application.

## Kubernetes Clusters

Mindweaver interacts with external **Kubernetes Clusters** to deploy and manage components. You must register your cluster by providing its `kubeconfig` and specifying the target namespace. Mindweaver uses **ArgoCD** to orchestrate these deployments, ensuring that the state of your cluster matches the metadata defined in the platform.

## Platform Components

**Platform Components** are the actual services you deploy (e.g., PostgreSQL, Trino, Airflow). 
- **State Management**: Each platform component has an associated state that tracks whether it is currently active and its deployment status.
- **Templates**: Components are defined using Jinja2 templates for Kubernetes manifests, which Mindweaver renders based on your configuration.
- **Actions**: Standard actions like `_deploy` and `_decommission` are used to manage the lifecycle of these components.

## Metadata Management

Beyond deployment, Mindweaver acts as a centralized metadata registry for:

- **Data Sources**: Configurations and authentication details for external databases.
- **S3 Connections**: Storage configurations for data lakes.
- **AI Agents & Knowledge Bases**: Managing the integration of AI capabilities within your data platform.

## Encryption & Security

Sensitive information (like passwords and tokens) is always encrypted before being stored in the database. When viewing these resources via the API, sensitive fields are redacted (`__REDACTED__`) to ensure security.
