# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from sqlmodel import select, func
from mindweaver.fw.state import BaseState
from .service import ProjectService

logger = logging.getLogger(__name__)


@ProjectService.with_state()
class ProjectState(BaseState):
    """
    Project state provides an overview of project resources and cluster health.
    """

    async def get(self):
        from mindweaver.platform_service.pgsql import (
            PgSqlPlatform,
            PgSqlPlatformState,
        )
        from mindweaver.platform_service.trino import (
            TrinoPlatform,
            TrinoPlatformState,
        )
        from mindweaver.platform_service.hive_metastore import (
            HiveMetastorePlatform,
            HiveMetastorePlatformState,
        )
        from mindweaver.platform_service.superset import (
            SupersetPlatform,
            SupersetPlatformState,
        )
        from mindweaver.platform_service.ranger import (
            RangerPlatform,
            RangerPlatformState,
        )
        from mindweaver.platform_service.solr import (
            SolrPlatform,
            SolrPlatformState,
        )
        from mindweaver.service.k8s_cluster import K8sClusterStatus

        # Helper to get counts
        async def _get_count(plat_cls, state_cls):
            stmt = (
                select(func.count(plat_cls.id))
                .join(
                    state_cls,
                    plat_cls.id == state_cls.platform_id,
                    isouter=True,
                )
                .where(plat_cls.project_id == self.model.id)
                .where(state_cls.active == True)
            )
            res = await self.svc.session.exec(stmt)
            return res.one_or_none() or 0

        pgsql_count = await _get_count(PgSqlPlatform, PgSqlPlatformState)
        trino_count = await _get_count(TrinoPlatform, TrinoPlatformState)
        hive_metastore_count = await _get_count(HiveMetastorePlatform, HiveMetastorePlatformState)
        superset_count = await _get_count(SupersetPlatform, SupersetPlatformState)
        ranger_count = await _get_count(RangerPlatform, RangerPlatformState)
        solr_count = await _get_count(SolrPlatform, SolrPlatformState)

        # Get cluster status
        status_data = {}
        cluster_node_ips = []
        if self.model.k8s_cluster_id:
            stmt_status = select(K8sClusterStatus).where(
                K8sClusterStatus.k8s_cluster_id == self.model.k8s_cluster_id
            )
            result_status = await self.svc.session.exec(stmt_status)
            status_model = result_status.one_or_none()

            if status_model:
                status_data = status_model.model_dump(
                    exclude={"id", "k8s_cluster_id", "last_update"}
                )
                status_data["last_update"] = status_model.last_update.isoformat()
                cluster_node_ips = getattr(status_model, "node_ips", None) or []

        # Dynamic check for Dex OIDC in project namespace
        dex_installed = False
        dex_version = None
        ingress_ports = []
        envoy_gateway_service_type = "NodePort"
        if self.model.k8s_cluster_id and self.model.k8s_namespace:
            from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
            stmt_c = select(K8sCluster).where(K8sCluster.id == self.model.k8s_cluster_id)
            res_c = await self.svc.session.exec(stmt_c)
            cluster_model = res_c.one_or_none()
            if cluster_model:
                envoy_gateway_service_type = cluster_model.envoy_gateway_service_type
                import tempfile
                import asyncio
                from kubernetes import client, config

                def _get_dex_status():
                    try:
                        if cluster_model.type == K8sClusterType.IN_CLUSTER:
                            config.load_incluster_config()
                        else:
                            if not cluster_model.kubeconfig:
                                return False, None, []
                            with tempfile.NamedTemporaryFile(mode="w") as kf:
                                kf.write(cluster_model.kubeconfig)
                                kf.flush()
                                config.load_kube_config(config_file=kf.name)
                        
                        core_v1 = client.CoreV1Api()
                        
                        ports_info = []
                        try:
                            # Helper to extract load balancer ingress
                            def _get_lb_ips(service):
                                ips = []
                                if service.status and service.status.load_balancer and service.status.load_balancer.ingress:
                                    for ing in service.status.load_balancer.ingress:
                                        if ing.ip:
                                            ips.append(ing.ip)
                                        elif ing.hostname:
                                            ips.append(ing.hostname)
                                return ips

                            # 1. Search in project namespace
                            svcs = core_v1.list_namespaced_service(namespace=self.model.k8s_namespace)
                            for svc in svcs.items:
                                if "envoy" in svc.metadata.name or "project-gateway" in svc.metadata.name:
                                    lb_ips = _get_lb_ips(svc)
                                    for p in svc.spec.ports:
                                        ports_info.append({
                                            "name": svc.metadata.name,
                                            "port": p.port,
                                            "node_port": p.node_port if getattr(p, "node_port", None) else None,
                                            "protocol": p.protocol,
                                            "load_balancer_ips": lb_ips,
                                        })
                            # 2. Search in envoy-gateway-system namespace for prefix matching
                            expected_prefix = f"envoy-{self.model.k8s_namespace or self.model.name}-project-gateway"
                            try:
                                eg_svcs = core_v1.list_namespaced_service(namespace="envoy-gateway-system")
                                for svc in eg_svcs.items:
                                    if svc.metadata.name.startswith(expected_prefix):
                                        lb_ips = _get_lb_ips(svc)
                                        for p in svc.spec.ports:
                                            ports_info.append({
                                                "name": svc.metadata.name,
                                                "port": p.port,
                                                "node_port": p.node_port if getattr(p, "node_port", None) else None,
                                                "protocol": p.protocol,
                                                "load_balancer_ips": lb_ips,
                                            })
                            except Exception as eg_e:
                                logger.warning(f"Failed to list services in envoy-gateway-system: {eg_e}")
                        except Exception as e:
                            logger.warning(f"Failed to list Envoy/gateway services: {e}")

                        secrets = core_v1.list_namespaced_secret(namespace=self.model.k8s_namespace)
                        installed = False
                        for secret in secrets.items:
                            if secret.metadata.name.startswith("sh.helm.release.v1.dex"):
                                installed = True
                                break
                        if not installed:
                            svcs = core_v1.list_namespaced_service(
                                namespace=self.model.k8s_namespace,
                                label_selector="app.kubernetes.io/name=dex"
                            )
                            if svcs.items:
                                installed = True
                        
                        version = None
                        if installed:
                            pods = core_v1.list_namespaced_pod(
                                namespace=self.model.k8s_namespace,
                                label_selector="app.kubernetes.io/name=dex"
                            )
                            if pods.items:
                                pod = pods.items[0]
                                version = pod.metadata.labels.get("app.kubernetes.io/version")
                                if not version and pod.spec.containers:
                                    image = pod.spec.containers[0].image
                                    if ":" in image:
                                        version = image.split(":")[-1]
                        return installed, version, ports_info
                    except Exception as e:
                        logger.warning(f"Failed to check project Dex status: {e}")
                        return False, None, []

                dex_installed, dex_version, ingress_ports = await asyncio.to_thread(_get_dex_status)

        return {
            "pgsql": pgsql_count,
            "trino": trino_count,
            "hive_metastore": hive_metastore_count,
            "superset": superset_count,
            "ranger": ranger_count,
            "solr": solr_count,
            "spark": 0,
            "airflow": 0,
            "cluster": status_data,
            "dex_installed": dex_installed,
            "dex_version": dex_version,
            "cluster_node_ips": cluster_node_ips,
            "ingress_ports": ingress_ports,
            "envoy_gateway_service_type": envoy_gateway_service_type,
        }

