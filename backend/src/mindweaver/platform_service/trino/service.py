# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import httpx
import bcrypt
import secrets
import logging
import asyncio
import tempfile
import base64
import random
import string
import yaml
import jinja2 as j2
import json


from typing import Any, Optional, Literal
from kubernetes import client, config
from pydantic import ValidationError

from mindweaver.fw.exc import FieldValidationError
from mindweaver.fw.service import before_create, before_delete, VALIDATION_MODE
from mindweaver.platform_service.base import PlatformService, _get_jinja_env
from mindweaver.fw.model import ts_now
from mindweaver.platform_service.hive_metastore.service import (
    HiveMetastorePlatformService,
)
from mindweaver.datasource_service import DatabaseSourceService
from mindweaver.service.s3_storage.service import S3StorageService
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.crypto import decrypt_password
from mindweaver.fw.util import generate_password

from .model import TrinoPlatform, TrinoPlatformState

logger = logging.getLogger(__name__)


class TrinoPlatformService(PlatformService[TrinoPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[TrinoPlatformState] = TrinoPlatformState
    SUPPORTED_CATALOG_DRIVERS = ["postgresql", "mysql", "trino", "mssql"]

    @classmethod
    def model_class(cls) -> type[TrinoPlatform]:
        return TrinoPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/trino"

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["internal_shared_secret", "admin_password"]

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["internal_shared_secret", "admin_password"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "process_forwarded": {
                "order": 9,
                "label": "Process X-Forwarded Headers",
                "type": "boolean",
            },
            "replica_count": {
                "order": 10,
                "type": "range",
                "min": 1,
                "max": 10,
                "step": 1,
            },
            "cpu_request": {
                "order": 11,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "cpu_limit": {
                "order": 12,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "mem_request": {
                "order": 13,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 14,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Limit (Gi)",
            },
            "hms_ids": {
                "order": 20,
                "label": "Hive Metastores",
                "type": "relationship",
                "endpoint": "/api/v1/platform/hive-metastore",
                "field": "id",
                "multiselect": True,
            },
            "database_source_ids": {
                "order": 21,
                "label": "Database Sources",
                "type": "relationship",
                "endpoint": "/api/v1/database-sources",
                "field": "id",
                "multiselect": True,
            },
            "rules": {
                "order": 30,
                "label": "Access Control Rules",
                "type": "json",
                "column_span": 2,
                "placeholder": '{\n  "catalogs": [\n    {\n      "user": "admin",\n      "catalog": ".*",\n      "allow": "all"\n    }\n  ]\n}',
            },
        }

    @before_create(before="_handle_redacted_create")
    async def generate_passwords(self, model: TrinoPlatform):
        """Autogenerate random passwords for Trino components."""
        model.admin_password = generate_password()

    async def get_preferred_catalog(self, model: TrinoPlatform) -> Optional[str]:
        """
        Determines the preferred catalog for CLI examples.
        Priority: Hive/Iceberg (Lakehouse) > Data Source
        """
        if model.hms_ids:
            hms_svc = await HiveMetastorePlatformService.get_service(
                self.request, self.session
            )
            hms_model = await hms_svc.get(model.hms_ids[0])
            return hms_model.name

        if model.database_source_ids:
            ds_svc = await DatabaseSourceService.get_service(self.request, self.session)
            ds_model = await ds_svc.get(model.database_source_ids[0])
            return ds_model.name

        return None

    async def template_vars(self, model: TrinoPlatform) -> dict:
        vars = model.model_dump(exclude=self.redacted_fields())
        resolved_img, resolved_tag = await self.resolve_image(
            model, "trino", "trinodb/trino:latest"
        )
        vars["image"] = f"{resolved_img}:{resolved_tag}"
        vars["image_tag"] = resolved_tag
        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model, "trino", "main", "https://trinodb.github.io/charts", "trino", "1.41.0"
        )
        vars["chart_repo"] = chart_repo
        vars["chart_name"] = chart_name
        vars["chart_version"] = chart_version
        vars["override_image"] = True
        vars["namespace"] = await self._resolve_namespace(model)
        project = await self.project(model)
        vars["project_name"] = project.name
        vars["ingress_domain"] = project.ingress_domain

        # HTTPS is mandatory
        vars["enable_https"] = True

        if model.internal_shared_secret:
            try:
                vars["internal_shared_secret"] = decrypt_password(
                    model.internal_shared_secret
                )
            except Exception:
                vars["internal_shared_secret"] = model.internal_shared_secret

        # 1. Resolve HMS and Data Sources Catalogs
        catalogs = []
        if model.hms_ids:
            hms_svc = await HiveMetastorePlatformService.get_service(
                self.request, self.session
            )
            for hms_id in model.hms_ids:
                hms_model = await hms_svc.get(hms_id)
                hms_state = await hms_svc.platform_state(hms_model)

                if not getattr(self, "_decommissioning", False) and (not hms_state or not hms_state.active):
                    raise ValueError(
                        f"Managed Hive Metastore {hms_model.name} is not active"
                    )

                hms_namespace = await hms_svc._resolve_namespace(hms_model)
                hms_uri = (
                    hms_state.hms_uri
                    or f"thrift://{hms_model.name}.{hms_namespace}.svc.cluster.local:9083"
                )

                catalog = {
                    "catalog": hms_model.name,
                    "properties": {
                        "connector.name": "lakehouse",
                        "hive.metastore.uri": hms_uri,
                    },
                }

                if hms_model.s3_storage_id:
                    s3_svc = await S3StorageService.get_service(
                        self.request, self.session
                    )
                    s3_model = await s3_svc.get(hms_model.s3_storage_id)
                    catalog["properties"]["fs.native-s3.enabled"] = "true"
                    catalog["properties"]["s3.endpoint"] = s3_model.endpoint_url

                    # Default region to us-east-1 if empty or if endpoint_url is set (local)
                    s3_region = s3_model.region
                    if not s3_region or not s3_region.strip() or s3_model.endpoint_url:
                        s3_region = "us-east-1"
                    catalog["properties"]["s3.region"] = s3_region

                    catalog["properties"]["s3.aws-access-key"] = s3_model.access_key
                    if s3_model.secret_key:
                        try:
                            catalog["properties"]["s3.aws-secret-key"] = (
                                decrypt_password(s3_model.secret_key)
                            )
                        except Exception:
                            catalog["properties"][
                                "s3.aws-secret-key"
                            ] = s3_model.secret_key
                    catalog["properties"]["s3.path-style-access"] = "true"

                catalogs.append(catalog)

        # 2. Resolve Database Sources
        if model.database_source_ids:
            ds_svc = await DatabaseSourceService.get_service(self.request, self.session)
            for ds_id in model.database_source_ids:
                ds = await ds_svc.get(ds_id)

                # Default mapping of engines to trino catalog connectors
                # Some typical ones: postgresql -> postgresql, mysql -> mysql
                connector_name = "sqlserver" if ds.engine == "mssql" else ds.engine

                catalog = {
                    "catalog": ds.name,
                    "properties": {
                        "connector.name": connector_name,
                    },
                }

                # Common properties
                if ds.engine == "mssql":
                    jdbc_prefix = "jdbc:sqlserver://"
                    resource_path = f";databaseName={ds.database}" if ds.database else ""
                    encrypt = "true" if ds.enable_ssl else "false"
                    trust_cert = "false" if ds.verify_ssl else "true"
                    resource_path += f";encrypt={encrypt};trustServerCertificate={trust_cert}"
                else:
                    jdbc_prefix = f"jdbc:{ds.engine}://"
                    resource_path = f"/{ds.database}" if ds.database else ""

                host_port = f"{ds.host}" + (f":{ds.port}" if ds.port else "")

                if ds.engine in ("postgresql", "mysql", "mssql"):
                    catalog["properties"][
                        "connection-url"
                    ] = f"{jdbc_prefix}{host_port}{resource_path}"
                    if ds.login:
                        catalog["properties"]["connection-user"] = ds.login
                    if ds.password:
                        try:
                            decrypted = decrypt_password(ds.password)
                            catalog["properties"]["connection-password"] = decrypted
                        except Exception:
                            catalog["properties"]["connection-password"] = ds.password

                # Extend with additional driver parameters
                for param, pval in ds.parameters.items():
                    if param.startswith("trino."):
                        catalog["properties"][param.replace("trino.", "", 1)] = str(
                            pval
                        )
                    else:
                        catalog["properties"][param] = str(pval)

                catalogs.append(catalog)

        vars["catalogs"] = catalogs

        # 3. Resolve LDAP Configuration from Project
        if project.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(project.ldap_config_id)

            ldap_props = {
                "ldap.url": ldap_config.server_url,
                "ldap.allow-insecure": (
                    "true" if not ldap_config.verify_ssl else "false"
                ),
            }

            if ldap_config.bind_dn:
                ldap_props["ldap.bind-dn"] = ldap_config.bind_dn
                if ldap_config.bind_password:
                    try:
                        ldap_props["ldap.bind-password"] = decrypt_password(
                            ldap_config.bind_password
                        )
                    except Exception:
                        ldap_props["ldap.bind-password"] = ldap_config.bind_password

                ldap_props["ldap.user-base-dn"] = ldap_config.user_search_base
                ldap_props["ldap.group-auth-pattern"] = (
                    ldap_config.user_search_filter.replace("{0}", "${USER}")
                )
            else:
                # Direct bind fallback
                # Trino direct bind usually expects a pattern that evaluates to the full DN
                # If we only have base and filter, we can try to guess or use a pattern if provided
                # For now we use the filter as the basis but Trino direct bind name is user-bind-pattern
                dn_pattern = f"{ldap_config.username_attr}=${{USER}},{ldap_config.user_search_base}"
                ldap_props["ldap.user-bind-pattern"] = dn_pattern

            vars["ldap"] = ldap_props

        vars["ranger_enabled"] = False

        # Resolve password authenticators list (LDAP first, then file/local)
        auth_files = []
        if vars.get("ldap"):
            auth_files.append("/etc/trino/ldap.properties")
        
        # Admin file authentication is always enabled
        auth_files.append("/etc/trino/file.properties")
        vars["file_auth_enabled"] = True
        
        admin_pass = ""
        if model.admin_password:
            try:
                admin_pass = decrypt_password(model.admin_password)
            except Exception:
                admin_pass = model.admin_password
        if not admin_pass:
            admin_pass = "admin"
            
        hashed_admin = bcrypt.hashpw(admin_pass.encode("utf-8"), bcrypt.gensalt(10))
        hashed_admin_str = hashed_admin.decode("utf-8")
        if hashed_admin_str.startswith("$2b$"):
            hashed_admin_str = "$2y$" + hashed_admin_str[4:]
        vars["admin_trino_password_hash"] = hashed_admin_str



        if auth_files:
            vars["password_authenticator_config_files"] = ",".join(auth_files)

        vars["jwt_enabled"] = True
        vars["jwt_key_file"] = f"http://{project.name}-dex.{vars['namespace']}.svc.cluster.local:5556/dex/keys"

        vars["preferred_catalog"] = await self.get_preferred_catalog(model)

        # Resolve Access Control Rules (rules.json)
        rules = dict(model.rules) if model.rules else {}
        impersonation_rules = rules.get("impersonation", [])
        if not isinstance(impersonation_rules, list):
            impersonation_rules = [impersonation_rules]
        else:
            # Copy to avoid mutating the original dict/list in-place if it is stored in model
            impersonation_rules = list(impersonation_rules)

        automated_rule = {
            "originalUser": f"CN=.*\\.{vars['namespace']}\\.svc\\.cluster\\.local",
            "newUser": ".*",
            "allow": True
        }

        # Check if automated rule is already present in impersonation_rules
        is_already_present = False
        for rule in impersonation_rules:
            if isinstance(rule, dict) and rule.get("originalUser") == automated_rule["originalUser"] and rule.get("newUser") == automated_rule["newUser"] and rule.get("allow") == automated_rule["allow"]:
                is_already_present = True
                break

        if not is_already_present:
            impersonation_rules.append(automated_rule)

        rules["impersonation"] = impersonation_rules
        vars["rules_json"] = json.dumps(rules, indent=2)

        return vars

    async def render_manifests(self, model: TrinoPlatform) -> str:
        """
        Renders the manifests from the template directory, excluding
        the ranger-sync-job.yaml.j2 template.
        """
        if not self.template_directory:
            raise ValueError(
                f"template_directory not set for {self.__class__.__name__}"
            )

        if not os.path.exists(self.template_directory):
            raise ValueError(
                f"template_directory {self.template_directory} does not exist"
            )

        # Load templates
        env = _get_jinja_env(self.template_directory)
        templates = env.list_templates()

        rendered_manifests = []
        vars = await self.template_vars(model)

        for template_name in templates:
            if not template_name.endswith((".yaml", ".yml", ".yml.j2", ".yaml.j2")):
                continue
            template = env.get_template(template_name)
            rendered = template.render(**vars)
            rendered_manifests.append(rendered)

        if not rendered_manifests:
            logger.warning(f"No templates found in {self.template_directory}")
            return ""

        return "---\n" + "\n---\n".join(rendered_manifests)




    async def deploy(self, model: TrinoPlatform):
        """
        Deploys/upgrades the Trino service.
        """
        db_updated = False
        if not model.admin_password:
            model.admin_password = generate_password()
            db_updated = True
        if db_updated:
            self.session.add(model)
            coro = self.session.flush()
            if asyncio.iscoroutine(coro):
                await coro

        await super().deploy(model)

# Register the poller class
from .poller import TrinoPoller
