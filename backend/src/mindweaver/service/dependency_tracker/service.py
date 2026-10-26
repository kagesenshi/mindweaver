# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from typing import Any, Optional
from sqlmodel import select, delete
from mindweaver.fw.service import Service
from mindweaver.fw.registry import SERVICE_REGISTRY
from .model import DependencyTracker
from . import permission

logger = logging.getLogger(__name__)


class DependencyTrackerService(Service[DependencyTracker]):
    """Service for managing dependency tracker data and tracking service dependencies."""

    permissions = permission

    @classmethod
    def model_class(cls) -> type[DependencyTracker]:
        """Return the model class managed by this service."""
        return DependencyTracker

    @classmethod
    def service_path(cls) -> str:
        """Override service path to keep it clean and singular."""
        return "/dependency-tracker"

    async def get_dependents(self, model_uuid: str) -> list[DependencyTracker]:
        """Return all active dependency entries that depend on the given service UUID."""
        stmt = select(DependencyTracker).where(
            DependencyTracker.dependency_uuid == str(model_uuid)
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def get_dependencies(self, model_uuid: str) -> list[DependencyTracker]:
        """Return all dependency entries where the given service UUID is the source."""
        stmt = select(DependencyTracker).where(
            DependencyTracker.service_uuid == str(model_uuid)
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def clear_dependencies(self, model_uuid: str):
        """Remove all dependency records for which model_uuid is the source service."""
        stmt = delete(DependencyTracker).where(
            DependencyTracker.service_uuid == str(model_uuid)
        )
        await self.session.exec(stmt)
        await self.session.flush()

    async def track_service_dependencies(
        self, service: Any, model: Any
    ) -> list[DependencyTracker]:
        """
        Inspect the widget list of the service and find relationship widgets.
        Create an entry in the dependency tracker for each dependency relationship.
        """
        source_uuid = str(getattr(model, "uuid", ""))
        source_name = str(getattr(model, "name", ""))
        source_type = service.service_type()

        widgets = service.get_widgets()
        new_entries: list[DependencyTracker] = []

        for field_name, widget_meta in widgets.items():
            if field_name in ("project_id", "id", "uuid"):
                continue
            if not isinstance(widget_meta, dict):
                continue
            if widget_meta.get("type") != "relationship":
                continue

            val = getattr(model, field_name, None)
            if val is None or val == "":
                continue

            # Determine if multi-select
            is_multiselect = (
                widget_meta.get("multiselect", False)
                or widget_meta.get("multi_select", False)
                or isinstance(val, (list, tuple, set))
            )

            if is_multiselect:
                if not isinstance(val, (list, tuple, set)):
                    items = [val]
                else:
                    items = list(val)
            else:
                items = [val]

            for item in items:
                if item is None or item == "":
                    continue

                dep_uuid, dep_name, dep_type = await self._resolve_target(
                    model=model,
                    field_name=field_name,
                    widget_meta=widget_meta,
                    item=item,
                )

                entry = DependencyTracker(
                    service_uuid=source_uuid,
                    service_name=source_name,
                    service_type=source_type,
                    dependency_uuid=dep_uuid,
                    dependency_name=dep_name,
                    dependency_type=dep_type,
                    relationship=field_name,
                )
                new_entries.append(entry)

        # Clear existing source dependencies for this service before adding new ones
        await self.clear_dependencies(source_uuid)
        for entry in new_entries:
            self.session.add(entry)
        await self.session.flush()
        return new_entries

    async def _resolve_target(
        self,
        model: Any,
        field_name: str,
        widget_meta: dict[str, Any],
        item: Any,
    ) -> tuple[str, str, str]:
        """Resolve dependency UUID, name, and service type for a given relationship value."""
        endpoint = widget_meta.get("endpoint", "")
        lookup_field = widget_meta.get("field", "id")

        # Try to find target service class
        target_svc_cls = self._find_target_service(model, field_name, endpoint)

        if target_svc_cls:
            target_type = target_svc_cls.service_type()
            target_model_cls = target_svc_cls.model_class()
            col = getattr(target_model_cls, lookup_field, None)
            if col is not None:
                stmt = select(target_model_cls).where(col == item)
                target_obj = (await self.session.exec(stmt)).first()
                if target_obj:
                    dep_uuid = str(getattr(target_obj, "uuid", item))
                    dep_name = str(getattr(target_obj, "name", item))
                    return dep_uuid, dep_name, target_type

        # Fallback if target object not found in database
        clean_ep = endpoint.replace("/api/v1", "").strip("/")
        fallback_type = clean_ep.split("/")[-1].replace("-", "_") if clean_ep else "unknown"
        return str(item), str(item), fallback_type

    def _find_target_service(
        self, model: Any, field_name: str, endpoint: str
    ) -> Optional[type[Service]]:
        """Find the target service class matching a relationship."""
        # 1. Try via foreign_key on model field
        model_fields = getattr(model.__class__, "model_fields", {})
        field_info = model_fields.get(field_name)
        if field_info and hasattr(field_info, "foreign_key") and field_info.foreign_key:
            table_name = str(field_info.foreign_key).split(".")[0]
            if table_name in SERVICE_REGISTRY:
                return SERVICE_REGISTRY[table_name]

        # 2. Try via endpoint matching service_path
        clean_ep = endpoint.replace("/api/v1", "").rstrip("/")
        for svc_cls in SERVICE_REGISTRY.values():
            if hasattr(svc_cls, "service_path"):
                sp = svc_cls.service_path().rstrip("/")
                if sp == clean_ep:
                    return svc_cls

        return None
