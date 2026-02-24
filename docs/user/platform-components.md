# Platform Components

This chapter covers the deployment and management of data platform components.

## Support Components

Mindweaver currently supports the orchestration of the following components:

- **PostgreSQL**: Relational database for metadata and application data.
- **Trino**: Distributed SQL query engine for big data.
- **Airflow**: Workflow orchestration platform.
- **Superset**: Data exploration and visualization platform.
- **Kafka**: Distributed event streaming platform.

## Deploying a Component

To deploy a component, follow these steps in the Mindweaver UI:

1. **Select Project**: Navigate to the project where you want to deploy the component.
2. **Choose Service**: Go to the corresponding service section (e.g., "PostgreSQL").
3. **Configure Settings**: Fill in the required fields (e.g., name, cluster selection, resource limits).
4. **Deploy**: Click the **Deploy** button. This will trigger the backend to:
    - Render the Kubernetes manifests using Jinja2 templates.
    - Sync the desired state with ArgoCD.
    - Start the deployment process on the target Kubernetes cluster.

## Monitoring Status

You can monitor the status of your components directly from the dashboard.
- **Active**: Indicates if the component is enabled in the platform.
- **Status**: Reflects the current deployment status from ArgoCD/Kubernetes.

## Decommissioning

If you no longer need a component, use the **Decommission** action. This will gracefully remove the resources from the Kubernetes cluster while maintaining historical metadata in Mindweaver (unless explicitly deleted).
