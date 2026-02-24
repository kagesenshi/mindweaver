import asyncio
import logging
import tempfile
import yaml
from typing import Any
from datetime import datetime

from fastapi import Depends
from kubernetes import client, config
from sqlmodel import select

from mindweaver.service import Service, before_create, before_update

from mindweaver.fw.model import ts_now
from .model import Project, ProjectStatus, K8sClusterType

logger = logging.getLogger(__name__)


class ProjectService(Service[Project]):
    @classmethod
    def model_class(cls) -> type[Project]:
        return Project

    async def poll_status(self, model: Project):
        """Poll cluster status and update ProjectStatus"""
        logger.info(f"Polling status for project {model.name}")

        try:

            def _get_k8s_info():
                if model.k8s_cluster_type == K8sClusterType.IN_CLUSTER:
                    config.load_incluster_config()
                else:
                    if not model.k8s_cluster_kubeconfig:
                        raise ValueError(f"Project {model.name} has no kubeconfig")
                    with tempfile.NamedTemporaryFile(mode="w") as kf:
                        kf.write(model.k8s_cluster_kubeconfig)
                        kf.flush()
                        config.load_kube_config(config_file=kf.name)

                core_v1 = client.CoreV1Api()
                version_api = client.VersionApi()

                # Get Version
                ver = version_api.get_code()
                k8s_version = ver.git_version

                # Get Nodes
                nodes = core_v1.list_node()
                node_count = len(nodes.items)
                nodes_status = {}
                cpu_total = 0.0
                ram_total = 0.0

                def _parse_res(res):
                    if res.endswith("Ki"):
                        return float(res[:-2]) / 1024 / 1024
                    if res.endswith("Mi"):
                        return float(res[:-2]) / 1024
                    if res.endswith("Gi"):
                        return float(res[:-2])
                    if res.endswith("m"):
                        return float(res[:-1]) / 1000
                    try:
                        return float(res)
                    except ValueError:
                        return 0.0

                for node in nodes.items:
                    name = node.metadata.name
                    status = "Unknown"
                    for cond in node.status.conditions:
                        if cond.type == "Ready":
                            status = "Ready" if cond.status == "True" else "NotReady"
                            break
                    nodes_status[name] = status

                    # Resource totals
                    cpu_total += _parse_res(node.status.capacity.get("cpu", "0"))
                    # Convert memory to GiB
                    ram_total += _parse_res(node.status.capacity.get("memory", "0"))

                # Check ArgoCD
                argocd_installed = False
                argocd_version = None
                try:
                    # Look for ArgoCD helm release secrets
                    # Helm secrets are named sh.helm.release.v1.{release_name}.v{version}
                    secrets = core_v1.list_secret_for_all_namespaces(
                        label_selector="owner=helm"
                    )
                    for secret in secrets.items:
                        if secret.metadata.name.startswith("sh.helm.release.v1.argocd"):
                            argocd_installed = True
                            break

                    if not argocd_installed:
                        # Fallback to service check (legacy or direct install)
                        svcs = core_v1.list_service_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=argocd-server"
                        )
                        if svcs.items:
                            argocd_installed = True

                    if argocd_installed:
                        # Try to get version from labels of the pod
                        pods = core_v1.list_pod_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=argocd-server"
                        )
                        if pods.items:
                            argocd_version = pods.items[0].metadata.labels.get(
                                "app.kubernetes.io/version"
                            )
                except Exception as e:
                    logger.warning(f"Failed to check ArgoCD presence: {e}")

                return {
                    "k8s_version": k8s_version,
                    "node_count": node_count,
                    "nodes_status": nodes_status,
                    "cpu_total": cpu_total,
                    "ram_total": ram_total,
                    "argocd_installed": argocd_installed,
                    "argocd_version": argocd_version,
                }

            info = await asyncio.to_thread(_get_k8s_info)

            # Update database
            stmt = select(ProjectStatus).where(ProjectStatus.project_id == model.id)
            result = await self.session.exec(stmt)
            status_model = result.one_or_none()

            if not status_model:
                status_model = ProjectStatus(project_id=model.id)
                self.session.add(status_model)

            status_model.status = "online"
            status_model.k8s_version = info["k8s_version"]
            status_model.node_count = info["node_count"]
            status_model.nodes_status = info["nodes_status"]
            status_model.cpu_total = info["cpu_total"]
            status_model.ram_total = info["ram_total"]
            status_model.argocd_installed = info["argocd_installed"]
            status_model.argocd_version = info["argocd_version"]
            status_model.last_update = ts_now()
            status_model.message = None

        except Exception as e:
            logger.error(f"Failed to poll status for project {model.name}: {e}")
            stmt = select(ProjectStatus).where(ProjectStatus.project_id == model.id)
            result = await self.session.exec(stmt)
            status_model = result.one_or_none()
            if not status_model:
                status_model = ProjectStatus(project_id=model.id)
                self.session.add(status_model)
            status_model.status = "error"
            status_model.message = str(e)
            status_model.last_update = ts_now()

        await self.session.flush()

    @before_create
    async def _set_default_namespace(self, model: Project):
        """Set default k8s_namespace to project name if not provided"""
        if not model.k8s_namespace:
            model.k8s_namespace = model.name

    @before_update
    async def _handle_namespace_update(self, model: Project, data: Project):
        """Handle k8s_namespace update, ensuring it defaults to name if cleared"""
        if hasattr(data, "k8s_namespace") and not data.k8s_namespace:
            data.k8s_namespace = model.name

    @classmethod
    def widgets(cls) -> dict[str, Any]:

        return {
            "description": {"order": 5, "column_span": 2},
            "k8s_namespace": {"order": 6, "column_span": 2, "label": "K8S Namespace"},
            "k8s_cluster_type": {
                "order": 10,
                "type": "select",
                "options": [
                    {"label": "In-Cluster", "value": "in-cluster"},
                    {"label": "Remote", "value": "remote"},
                ],
                "label": "K8S Cluster Type",
            },
            "k8s_cluster_kubeconfig": {
                "order": 11,
                "type": "textarea",
                "column_span": 2,
                "label": "Kubeconfig",
            },
        }
