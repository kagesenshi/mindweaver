# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import tempfile
import logging
from datetime import datetime, timezone
from kubernetes import client, config
from mindweaver.fw.action import BaseAction

from .service import PgSqlPlatformService

logger = logging.getLogger(__name__)


@PgSqlPlatformService.register_action("backup")
class PgSqlBackupAction(BaseAction):
    """Action to trigger a CNPG backup."""

    async def available(self) -> bool:
        """Only available for active platforms."""
        state = await self.svc.platform_state(self.model)
        return state is not None and state.active

    async def __call__(self, **kwargs):
        """Creates a Backup custom resource in Kubernetes."""
        kubeconfig = await self.svc.kubeconfig(self.model)
        namespace = await self.svc._resolve_namespace(self.model)

        def _create_backup():
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()
                    k8s_client = config.new_client_from_config(config_file=kf.name)

            custom_api = client.CustomObjectsApi(k8s_client)

            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
            backup_name = f"backup-{timestamp}"

            backup_body = {
                "apiVersion": "postgresql.cnpg.io/v1",
                "kind": "Backup",
                "metadata": {"name": backup_name, "namespace": namespace},
                "spec": {
                    "method": "barmanObjectStore",
                    "cluster": {"name": self.model.name},
                },
            }

            try:
                custom_api.create_namespaced_custom_object(
                    group="postgresql.cnpg.io",
                    version="v1",
                    namespace=namespace,
                    plural="backups",
                    body=backup_body,
                )
                logger.info(
                    f"Triggered backup {backup_name} for cluster {self.model.name}"
                )
                return {"status": "success", "backup_name": backup_name}
            except client.exceptions.ApiException as e:
                logger.error(f"Failed to trigger backup: {e}")
                raise RuntimeError(f"Failed to trigger backup: {e.reason}")

        return await asyncio.to_thread(_create_backup)
