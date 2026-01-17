import pytest
from sqlmodel import SQLModel, Field
from typing import Optional
from mindweaver.fw.service import Service
from mindweaver.fw.model import NamedBase
from sqlalchemy_utils import JSONType


class MockTarget(NamedBase):
    pass


class MockTargetService(Service[MockTarget]):
    @classmethod
    def model_class(cls) -> type[MockTarget]:
        return MockTarget


class MockModel(NamedBase):
    project_id: int = Field(foreign_key="mw_project.id")
    k8s_cluster_id: int = Field(foreign_key="mw_k8s_cluster.id")
    knowledge_db_ids: list[int] = Field(
        default=[], sa_type=JSONType(), foreign_key="mw_knowledge_db.id"
    )
    datasource_ids: list[int] = Field(
        default=[], sa_type=JSONType(), foreign_key="mw_datasource.id"
    )
    s3_storage_id: int = Field(default=None, foreign_key="mw_s3_storage.id")
    custom_field: str = Field(default="test")


class MockService(Service[MockModel]):
    @classmethod
    def model_class(cls) -> type[MockModel]:
        return MockModel


def test_relationship_label_generation():
    # Backup registry
    original_registry = Service._registry.copy()

    try:
        # Register mock services to registry
        Service._registry["mw_project"] = MockTargetService
        Service._registry["mw_k8s_cluster"] = MockTargetService
        Service._registry["mw_datasource"] = MockTargetService
        Service._registry["mw_knowledge_db"] = MockTargetService
        Service._registry["mw_s3_storage"] = MockTargetService

        widgets = MockService.get_widgets()

        # Check relationship detection and label generation
        assert widgets["project_id"]["type"] == "relationship"
        assert widgets["project_id"]["label"] == "Project"

        assert widgets["k8s_cluster_id"]["type"] == "relationship"
        assert widgets["k8s_cluster_id"]["label"] == "K8S Cluster"

        assert widgets["s3_storage_id"]["type"] == "relationship"
        assert widgets["s3_storage_id"]["label"] == "S3 Storage"

        assert widgets["knowledge_db_ids"]["type"] == "relationship"
        assert widgets["knowledge_db_ids"]["label"] == "Knowledge DB"

        assert widgets["datasource_ids"]["type"] == "relationship"
        assert widgets["datasource_ids"]["label"] == "Datasource"
    finally:
        # Restore registry
        Service._registry = original_registry
