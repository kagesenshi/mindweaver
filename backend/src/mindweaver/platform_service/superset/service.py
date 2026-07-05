# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
import base64
from typing import Any, Optional
from kubernetes import client, config
from pydantic import ValidationError

from mindweaver.fw.exc import FieldValidationError
from mindweaver.platform_service.base import PlatformService
from mindweaver.fw.model import ts_now, NamedBase
from mindweaver.fw.service import redefine_model
from mindweaver.platform_service.pgsql.service import PgSqlPlatformService
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.datasource_service import DatabaseSourceService
from mindweaver.platform_service.trino.service import TrinoPlatformService
from mindweaver.crypto import decrypt_password

from .model import SupersetPlatform, SupersetPlatformState

logger = logging.getLogger(__name__)


class SupersetPlatformService(PlatformService[SupersetPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[SupersetPlatformState] = SupersetPlatformState

    @classmethod
    def schema_class(cls) -> type[NamedBase]:
        """
        Provide custom schema class, filtering out OIDC fields if they are disabled.
        """
        from mindweaver.config import settings
        exclude_fields = []
        if not settings.enable_superset_oidc:
            exclude_fields.extend(["oidc_enabled", "oidc_client_secret"])
        return redefine_model(
            f"{cls.model_class().__name__}Schema",
            cls.model_class(),
            exclude=exclude_fields
        )

    @classmethod
    def model_class(cls) -> type[SupersetPlatform]:
        return SupersetPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/superset"

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["admin_password", "superset_secret_key", "oidc_client_secret"]

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["admin_password", "superset_secret_key", "oidc_client_secret"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "override_image": {
                "order": 6,
                "label": "Override Image",
                "type": "boolean",
            },
            "platform_pgsql_id": {
                "order": 10,
                "label": "PostgreSQL Metadata DB",
                "type": "relationship",
                "endpoint": "/api/v1/platform/pgsql",
                "field": "id",
            },
            "database_source_ids": {
                "order": 20,
                "label": "Database Sources",
                "type": "relationship",
                "endpoint": "/api/v1/database-sources",
                "field": "id",
                "multiselect": True,
            },
            "trino_ids": {
                "order": 21,
                "label": "Trino Platforms",
                "type": "relationship",
                "endpoint": "/api/v1/platform/trino",
                "field": "id",
                "multiselect": True,
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
                "max": 32,
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
                "roles": ["Admin", "Alpha", "Gamma", "sql_lab", "Public"],
            },
            "oidc_enabled": {
                "order": 26,
                "label": "Enable OIDC Authentication",
                "type": "boolean",
            },
            "sqllab_enabled": {
                "order": 27,
                "label": "Enable SQL Lab",
                "type": "boolean",
            },
        }

    async def template_vars(self, model: SupersetPlatform) -> dict:
        vars = model.model_dump()
        resolved_img, resolved_tag = await self.resolve_image(
            model, "superset", "ghcr.io/kagesenshi/mindweaver/superset:latest"
        )
        vars["image"] = f"{resolved_img}:{resolved_tag}"
        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model, "superset", "main", "https://apache.github.io/superset", "superset", "0.15.0"
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
        # Prefer pgbouncer if host is available in extra_data
        vars["db_host"] = pgsql_state.extra_data.get("pgbouncer_host") if pgsql_state else None
        if vars["db_host"]:
            vars["db_port"] = 5432  # Default pgbouncer port in our templates
        else:
            # Fallback to direct cluster service
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

        # 3. Resolve Data Sources
        datasources = []
        if model.database_source_ids:
            ds_svc = await DatabaseSourceService.get_service(self.request, self.session)
            for ds_id in model.database_source_ids:
                ds = await ds_svc.get(ds_id)
                engine = ds.engine
                if engine == "postgresql":
                    engine = "postgresql+asyncpg"
                sqlalchemy_uri = f"{engine}://{ds.login}:{decrypt_password(ds.password) if ds.password else ''}@{ds.host}:{ds.port}/{ds.database}"
                datasources.append(
                    {
                        "database_name": ds.name,
                        "sqlalchemy_uri": sqlalchemy_uri,
                        "expose_in_sqllab": True,
                    }
                )

        if model.trino_ids:
            trino_svc = await TrinoPlatformService.get_service(
                self.request, self.session
            )
            for trino_id in model.trino_ids:
                trino_model = await trino_svc.get(trino_id)
                trino_state = await trino_svc.platform_state(trino_model)
                if trino_state and trino_state.active:
                    # Use internal URI for Superset -> Trino communication
                    trino_namespace = await trino_svc._resolve_namespace(trino_model)
                    sqlalchemy_uri = f"trino://admin@{trino_model.name}.{trino_namespace}.svc.cluster.local:8443/"
                    extra_dict = {
                        "metadata_params": {},
                        "engine_params": {
                            "connect_args": {
                                "http_scheme": "https",
                                "verify": "/etc/ssl/certs/mindweaver-ca.crt"
                            }
                        },
                        "allow_multi_catalog": True
                    }
                    encrypted_extra_dict = {
                        "auth_method": "certificate",
                        "auth_params": {
                            "cert": "/etc/superset/trino-certs/tls.crt",
                            "key": "/etc/superset/trino-certs/tls.key"
                        }
                    }
                    datasources.append(
                        {
                            "database_name": trino_model.name,
                            "sqlalchemy_uri": sqlalchemy_uri,
                            "expose_in_sqllab": True,
                            "impersonate_user": True,
                            "extra": extra_dict,
                            "encrypted_extra": encrypted_extra_dict,
                            "is_trino": True,
                        }
                    )

        vars["datasources"] = datasources

        # 4. Handle custom image (handled above by resolve_image)

        # 5. Merge auth_role_mapping by entity
        merged_mapping = {}
        for m in model.auth_role_mapping:
            # Handle both object and dict for resilience
            entity = getattr(m, "entity", None) or (m.get("entity") if isinstance(m, dict) else None)
            role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
            
            if not entity or not role:
                continue

            if role == "sql_lab" and not model.sqllab_enabled:
                continue

            if entity not in merged_mapping:
                merged_mapping[entity] = []
            if role not in merged_mapping[entity]:
                merged_mapping[entity].append(role)
        vars["auth_role_mapping"] = merged_mapping

        # 6. OIDC config
        vars["oidc_enabled"] = model.oidc_enabled
        vars["oidc_client_id"] = model.name
        vars["oidc_client_secret"] = vars.get("oidc_client_secret", "")
        vars["oidc_internal_issuer"] = f"http://{project.name}-dex.{vars['namespace']}.svc.cluster.local:5556/dex"
        if vars["ingress_domain"]:
            vars["oidc_external_issuer"] = f"https://dex.{vars['ingress_domain']}/dex"
        else:
            vars["oidc_external_issuer"] = vars["oidc_internal_issuer"]

        return vars

    async def deploy(self, model: SupersetPlatform):
        """used to deploy/upgrade the service"""
        await super().deploy(model)
        if model.oidc_enabled:
            from mindweaver.tasks.project_tasks import install_dex_project_task
            install_dex_project_task.delay(model.project_id)

# Register the poller class
from .poller import SupersetPoller
