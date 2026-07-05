# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
import secrets
from typing import Any, Optional
from kubernetes import client, config

from mindweaver.platform_service.base import PlatformService
from mindweaver.fw.model import ts_now, NamedBase
from mindweaver.fw.service import redefine_model
from mindweaver.platform_service.pgsql.service import PgSqlPlatformService
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.service.s3_storage.service import S3StorageService
from mindweaver.crypto import decrypt_password, encrypt_password

from .model import AirflowPlatform, AirflowPlatformState

logger = logging.getLogger(__name__)


class AirflowPlatformService(PlatformService[AirflowPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[AirflowPlatformState] = AirflowPlatformState

    @classmethod
    def schema_class(cls) -> type[NamedBase]:
        """
        Provide custom schema class, filtering out OIDC fields if they are disabled.
        """
        from mindweaver.config import settings
        exclude_fields = []
        if not settings.enable_airflow_oidc:
            exclude_fields.extend(["oidc_enabled", "oidc_client_secret"])
        return redefine_model(
            f"{cls.model_class().__name__}Schema",
            cls.model_class(),
            exclude=exclude_fields
        )

    @classmethod
    def model_class(cls) -> type[AirflowPlatform]:
        return AirflowPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/airflow"

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["admin_password", "fernet_key", "webserver_secret_key", "oidc_client_secret"]

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["admin_password", "fernet_key", "webserver_secret_key", "oidc_client_secret"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "redis_enabled": {
                "order": 8,
                "label": "Deploy Redis Broker",
                "type": "boolean",
            },
            "s3_storage_id": {
                "order": 9,
                "label": "S3 Storage (Remote Logging)",
                "type": "relationship",
                "endpoint": "/api/v1/s3_storages",
                "field": "id",
            },
            "logs_s3_bucket": {
                "order": 9.5,
                "label": "Logs S3 Bucket",
                "type": "string",
            },
            "platform_pgsql_id": {
                "order": 10,
                "label": "PostgreSQL Metadata DB",
                "type": "relationship",
                "endpoint": "/api/v1/platform/pgsql",
                "field": "id",
            },
            "dags_git_sync_enabled": {
                "order": 15,
                "label": "Enable Git-Sync for DAGs",
                "type": "boolean",
            },
            "git_repo_id": {
                "order": 16,
                "label": "DAGs Git Repository",
                "type": "relationship",
                "endpoint": "/api/v1/git_repos",
                "field": "name",
            },
            "dags_git_branch": {
                "order": 17,
                "label": "DAGs Git Branch",
                "type": "string",
            },
            "dags_git_subpath": {
                "order": 18,
                "label": "DAGs Git Subpath",
                "type": "string",
            },
            "cpu_request": {
                "order": 30,
                "type": "range",
                "min": 0.1,
                "max": 8,
                "step": 0.1,
            },
            "cpu_limit": {
                "order": 31,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "mem_request": {
                "order": 32,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 33,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Limit (Gi)",
            },
            "auth_role_mapping": {
                "order": 25,
                "label": "Auth Role Mapping",
                "type": "auth-role-mapping",
                "roles": ["Admin", "User", "Op", "Viewer", "Public"],
            },
            "oidc_enabled": {
                "order": 26,
                "label": "Enable OIDC Authentication",
                "type": "boolean",
            },
        }

    async def template_vars(self, model: AirflowPlatform) -> dict:
        vars = model.model_dump()
        resolved_img, resolved_tag = await self.resolve_image(
            model, "airflow", "ghcr.io/kagesenshi/mindweaver/airflow:3.2.2-rev.5"
        )
        vars["image"] = f"{resolved_img}:{resolved_tag}"
        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model, "airflow", "main", "https://airflow.apache.org", "airflow", "1.22.0"
        )
        vars["chart_repo"] = chart_repo
        vars["chart_name"] = chart_name
        vars["chart_version"] = chart_version
        vars["override_image"] = True
        vars["namespace"] = await self._resolve_namespace(model)
        project = await self.project(model)
        vars["ingress_domain"] = project.ingress_domain
        vars["project_name"] = project.name



        # 0. Decrypt internal secrets
        for field in self.redacted_fields():
            val = getattr(model, field, None)
            if val:
                try:
                    vars[field] = decrypt_password(val)
                except Exception:
                    vars[field] = val

        # 1. Resolve PostgreSQL
        pgsql_svc = await PgSqlPlatformService.get_service(self.request, self.session)
        pgsql_model = await pgsql_svc.get(model.platform_pgsql_id)
        pgsql_state = await pgsql_svc.platform_state(pgsql_model)

        if not getattr(self, "_decommissioning", False) and (not pgsql_state or not pgsql_state.active):
            raise ValueError(f"Selected PostgreSQL {pgsql_model.name} is not active")

        # 1.1 Determine Host and Port
        vars["db_host"] = pgsql_state.extra_data.get("pgbouncer_host") if pgsql_state else None
        if vars["db_host"]:
            vars["db_port"] = 5432
        else:
            pgsql_ns = await pgsql_svc._resolve_namespace(pgsql_model)
            vars["db_host"] = f"{pgsql_model.name}-rw.{pgsql_ns}.svc.cluster.local"
            vars["db_port"] = 5432

        # 1.2 Credentials
        vars["db_user"] = (pgsql_state.db_user or "app") if pgsql_state else "app"
        vars["db_name"] = (pgsql_state.db_name or "app") if pgsql_state else "app"

        db_pass_enc = (pgsql_state.db_pass or "") if pgsql_state else ""
        if db_pass_enc:
            try:
                vars["db_pass"] = decrypt_password(db_pass_enc)
            except Exception:
                vars["db_pass"] = db_pass_enc
        else:
            vars["db_pass"] = ""

        # 2. Resolve LDAP from Project
        project = await self.project(model)
        if project.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(project.ldap_config_id)
            vars["ldap"] = ldap_config.model_dump()
            if ldap_config.bind_password:
                try:
                    vars["ldap"]["bind_password"] = decrypt_password(
                        ldap_config.bind_password
                    )
                except Exception:
                    vars["ldap"]["bind_password"] = ldap_config.bind_password

        # 3. Handle custom image (handled above by resolve_image)

        # 4. Merge auth_role_mapping by entity
        merged_mapping = {}
        for m in model.auth_role_mapping:
            entity = getattr(m, "entity", None) or (m.get("entity") if isinstance(m, dict) else None)
            role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)

            if not entity or not role:
                continue

            if entity not in merged_mapping:
                merged_mapping[entity] = []
            if role not in merged_mapping[entity]:
                merged_mapping[entity].append(role)
        vars["auth_role_mapping"] = merged_mapping

        # 5. OIDC config
        vars["oidc_enabled"] = model.oidc_enabled
        vars["oidc_client_id"] = model.name
        vars["oidc_client_secret"] = vars.get("oidc_client_secret", "")
        vars["oidc_internal_issuer"] = f"http://{project.name}-dex.{vars['namespace']}.svc.cluster.local:5556/dex"
        if vars["ingress_domain"]:
            vars["oidc_external_issuer"] = f"https://dex.{vars['ingress_domain']}/dex"
        else:
            vars["oidc_external_issuer"] = vars["oidc_internal_issuer"]

        # 6. DAGs git-sync config
        vars["dags_git_sync_enabled"] = model.dags_git_sync_enabled
        vars["dags_git_branch"] = model.dags_git_branch
        vars["dags_git_subpath"] = model.dags_git_subpath
        vars["git_repo"] = None
        vars["ssh_key"] = None
        vars["dags_git_repo"] = ""

        if model.dags_git_sync_enabled and model.git_repo_id:
            from mindweaver.service.git_repo.service import GitRepoService
            git_repo_svc = await GitRepoService.get_service(self.request, self.session)
            git_repo = await git_repo_svc.get(model.git_repo_id)
            vars["dags_git_repo"] = git_repo.url

            git_repo_dict = git_repo.model_dump()
            if git_repo.password:
                try:
                    git_repo_dict["password"] = decrypt_password(git_repo.password)
                except Exception:
                    git_repo_dict["password"] = git_repo.password
            vars["git_repo"] = git_repo_dict

            if git_repo.ssh_key_id:
                from mindweaver.service.ssh_key.service import SSHKeyService
                ssh_key_svc = await SSHKeyService.get_service(self.request, self.session)
                ssh_key = await ssh_key_svc.get(git_repo.ssh_key_id)
                ssh_key_dict = ssh_key.model_dump()
                if ssh_key.private_key:
                    try:
                        ssh_key_dict["private_key"] = decrypt_password(ssh_key.private_key)
                    except Exception:
                        ssh_key_dict["private_key"] = ssh_key.private_key
                vars["ssh_key"] = ssh_key_dict

        # 7. Executor (always CeleryExecutor)
        vars["executor"] = "CeleryExecutor"

        # 8. Redis (Celery broker)
        vars["redis_enabled"] = model.redis_enabled
        redis_password = secrets.token_urlsafe(10)
        vars["redis_password"] = redis_password

        # 9. S3 Storage for remote logging
        s3_enabled = bool(model.s3_storage_id and model.logs_s3_bucket)
        vars["s3_enabled"] = s3_enabled
        vars["logs_s3_bucket"] = model.logs_s3_bucket
        if s3_enabled:
            s3_svc = S3StorageService(self.request, self.session)
            s3_storage = await s3_svc.get(model.s3_storage_id)
            vars["s3_region"] = s3_storage.region
            vars["s3_access_key"] = s3_storage.access_key
            if s3_storage.secret_key:
                try:
                    vars["s3_secret_key"] = decrypt_password(s3_storage.secret_key)
                except Exception:
                    vars["s3_secret_key"] = s3_storage.secret_key
            if s3_storage.endpoint_url:
                # Strip protocol from endpoint for S3 connection URI
                endpoint = s3_storage.endpoint_url
                for prefix in ["https://", "http://"]:
                    if endpoint.startswith(prefix):
                        endpoint = endpoint[len(prefix):]
                        break
                endpoint = endpoint.rstrip("/")
                vars["s3_endpoint"] = endpoint
                vars["s3_endpoint_url"] = s3_storage.endpoint_url

        return vars

    async def deploy(self, model: AirflowPlatform):
        """used to deploy/upgrade the service"""
        # Generate admin_password if not set (e.g. for existing records)
        if not model.admin_password:
            model.admin_password = encrypt_password(secrets.token_urlsafe(16))
            self.session.add(model)
            await self.session.flush()
        await super().deploy(model)
        if model.oidc_enabled:
            from mindweaver.tasks.project_tasks import install_dex_project_task
            install_dex_project_task.delay(model.project_id)
router = AirflowPlatformService.router()

# Register the poller class
from .poller import AirflowPoller
