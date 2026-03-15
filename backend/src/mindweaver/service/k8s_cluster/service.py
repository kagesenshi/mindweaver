import asyncio
import logging
import tempfile
from typing import Any

from kubernetes import client, config
from sqlmodel import select

from mindweaver.service import Service
from mindweaver.fw.model import ts_now
from .model import K8sCluster, K8sClusterStatus, K8sClusterType

logger = logging.getLogger(__name__)


class K8sClusterService(Service[K8sCluster]):
    @classmethod
    def model_class(cls) -> type[K8sCluster]:
        return K8sCluster

    async def poll_status(self, model: K8sCluster):
        """Poll cluster status and update K8sClusterStatus"""
        logger.info(f"Polling status for k8s_cluster {model.name}")

        try:
            def _get_version(pod):
                version = pod.metadata.labels.get("app.kubernetes.io/version")
                if not version and pod.spec.containers:
                    # Try to extract from image tag
                    image = pod.spec.containers[0].image
                    if ":" in image:
                        version = image.split(":")[-1]
                return version

            def _get_k8s_info():
                if model.type == K8sClusterType.IN_CLUSTER:
                    config.load_incluster_config()
                else:
                    if not model.kubeconfig:
                        raise ValueError(f"Cluster {model.name} has no kubeconfig")
                    with tempfile.NamedTemporaryFile(mode="w") as kf:
                        kf.write(model.kubeconfig)
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
                    secrets = core_v1.list_secret_for_all_namespaces(
                        label_selector="owner=helm"
                    )
                    for secret in secrets.items:
                        if secret.metadata.name.startswith("sh.helm.release.v1.argocd"):
                            argocd_installed = True
                            break

                    if not argocd_installed:
                        svcs = core_v1.list_service_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=argocd-server"
                        )
                        if svcs.items:
                            argocd_installed = True

                    if argocd_installed:
                        pods = core_v1.list_pod_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=argocd-server"
                        )
                        if pods.items:
                            argocd_version = _get_version(pods.items[0])
                except Exception as e:
                    logger.warning(f"Failed to check ArgoCD presence: {e}")

                # Check Cert Manager
                cert_manager_installed = False
                cert_manager_version = None
                try:
                    for secret in secrets.items:
                        if secret.metadata.name.startswith(
                            "sh.helm.release.v1.cert-manager"
                        ):
                            cert_manager_installed = True
                            break
                    if not cert_manager_installed:
                        svcs = core_v1.list_service_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=cert-manager"
                        )
                        if svcs.items:
                            cert_manager_installed = True

                    if cert_manager_installed:
                        pods = core_v1.list_pod_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=cert-manager"
                        )
                        if pods.items:
                            cert_manager_version = _get_version(pods.items[0])
                except Exception as e:
                    logger.warning(f"Failed to check Cert Manager presence: {e}")

                # Check CNPG
                cnpg_installed = False
                cnpg_version = None
                try:
                    for secret in secrets.items:
                        if secret.metadata.name.startswith("sh.helm.release.v1.cnpg"):
                            cnpg_installed = True
                            break
                    if not cnpg_installed:
                        svcs = core_v1.list_service_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=cloudnative-pg"
                        )
                        if svcs.items:
                            cnpg_installed = True

                    if cnpg_installed:
                        pods = core_v1.list_pod_for_all_namespaces(
                            label_selector="app.kubernetes.io/name=cloudnative-pg"
                        )
                        if pods.items:
                            cnpg_version = _get_version(pods.items[0])
                except Exception as e:
                    logger.warning(f"Failed to check CNPG presence: {e}")

                # Check Mindweaver Cluster Issuer
                cluster_issuer_installed = False
                try:
                    custom_api = client.CustomObjectsApi()
                    issuers = custom_api.list_cluster_custom_object(
                        group="cert-manager.io",
                        version="v1",
                        plural="clusterissuers",
                    )
                    for issuer in issuers.get("items", []):
                        if issuer.get("metadata", {}).get("name") == "mindweaver-selfsigned-issuer":
                            cluster_issuer_installed = True
                            break
                except Exception as e:
                    logger.warning(f"Failed to check Mindweaver Cluster Issuer presence: {e}")

                return {
                    "k8s_version": k8s_version,
                    "node_count": node_count,
                    "nodes_status": nodes_status,
                    "cpu_total": cpu_total,
                    "ram_total": ram_total,
                    "argocd_installed": argocd_installed,
                    "argocd_version": argocd_version,
                    "cert_manager_installed": cert_manager_installed,
                    "cert_manager_version": cert_manager_version,
                    "cnpg_installed": cnpg_installed,
                    "cnpg_version": cnpg_version,
                    "cluster_issuer_installed": cluster_issuer_installed,
                }

            info = await asyncio.to_thread(_get_k8s_info)

            # Update database
            stmt = select(K8sClusterStatus).where(
                K8sClusterStatus.k8s_cluster_id == model.id
            )
            result = await self.session.exec(stmt)
            status_model = result.one_or_none()

            if not status_model:
                status_model = K8sClusterStatus(k8s_cluster_id=model.id)
                self.session.add(status_model)

            status_model.status = "online"
            status_model.k8s_version = info["k8s_version"]
            status_model.node_count = info["node_count"]
            status_model.nodes_status = info["nodes_status"]
            status_model.cpu_total = info["cpu_total"]
            status_model.ram_total = info["ram_total"]
            status_model.argocd_installed = info["argocd_installed"]
            status_model.argocd_version = info["argocd_version"]
            status_model.cert_manager_installed = info["cert_manager_installed"]
            status_model.cert_manager_version = info["cert_manager_version"]
            status_model.cnpg_installed = info["cnpg_installed"]
            status_model.cnpg_version = info["cnpg_version"]
            status_model.cluster_issuer_installed = info["cluster_issuer_installed"]
            status_model.last_update = ts_now()
            status_model.message = None

        except Exception as e:
            logger.error(f"Failed to poll status for cluster {model.name}: {e}")
            stmt = select(K8sClusterStatus).where(
                K8sClusterStatus.k8s_cluster_id == model.id
            )
            result = await self.session.exec(stmt)
            status_model = result.one_or_none()
            if not status_model:
                status_model = K8sClusterStatus(k8s_cluster_id=model.id)
                self.session.add(status_model)
            status_model.status = "error"
            status_model.message = str(e)
            status_model.last_update = ts_now()

        await self.session.flush()

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "description": {"order": 5, "column_span": 2},
            "type": {
                "order": 10,
                "type": "select",
                "options": [
                    {"label": "In-Cluster", "value": "in-cluster"},
                    {"label": "Remote", "value": "remote"},
                ],
                "label": "K8S Cluster Type",
            },
            "kubeconfig": {
                "order": 11,
                "type": "textarea",
                "column_span": 2,
                "label": "Kubeconfig",
            },
        }
