import pytest
from unittest.mock import MagicMock
from fastapi import Request
from sqlmodel import Session
from mindweaver.platform_service.pgsql import PgSqlPlatform, PgSqlPlatformService
from pydantic import ValidationError


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=Session)
    return request, session


def test_pgsql_resource_defaults():
    """Test default values for resource limits"""
    model = PgSqlPlatform(name="test-pgsql", project_id=1, k8s_cluster_id=1)
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 1.0
    assert model.mem_request == 1.0
    assert model.mem_limit == 2.0


def test_pgsql_resource_validation():
    """Test validation logic for resource limits"""
    # Valid case
    model = PgSqlPlatform.model_validate(
        {
            "name": "test-pgsql",
            "title": "Test PGSQL",
            "project_id": 1,
            "k8s_cluster_id": 1,
            "cpu_request": 1.0,
            "cpu_limit": 2.0,
            "mem_request": 2.0,
            "mem_limit": 4.0,
        }
    )
    assert model.cpu_request == 1.0

    # Invalid CPU: request > limit
    with pytest.raises(ValidationError) as excinfo:
        PgSqlPlatform.model_validate(
            {
                "name": "test-pgsql",
                "title": "Test PGSQL",
                "project_id": 1,
                "k8s_cluster_id": 1,
                "cpu_request": 2.0,
                "cpu_limit": 1.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

    # Invalid Memory: request > limit
    with pytest.raises(ValidationError) as excinfo:
        PgSqlPlatform.model_validate(
            {
                "name": "test-pgsql",
                "title": "Test PGSQL",
                "project_id": 1,
                "k8s_cluster_id": 1,
                "mem_request": 5.0,
                "mem_limit": 4.0,
            }
        )
    assert "Memory request cannot be greater than Memory limit" in str(excinfo.value)


@pytest.mark.asyncio
async def test_pgsql_template_rendering(mock_service_dependencies):
    """Test that the template renders with the correct resource values"""
    request, session = mock_service_dependencies
    svc = PgSqlPlatformService(request, session)

    model = PgSqlPlatform(
        name="test-db",
        project_id=1,
        k8s_cluster_id=1,
        cpu_request=0.5,
        cpu_limit=1.0,
        mem_request=2.0,
        mem_limit=4.0,
        storage_size="10Gi",
    )

    # Get template variables
    vars = await svc.template_vars(model)

    # Render template (we only test 10-cluster.yml.j2)
    # Since we can't easily access the internal render method without setting up more mocks,
    # we will manually verify the variables are present and check logic if needed.
    # But better yet, we can try to render it if we have the environment set up.
    # For unit test, checking variables might be enough if we trust the jinja template.

    # However, to be thorough, let's try to verify the template content if possible.
    # PgSqlPlatformService.render_manifests is complex to mock fully.
    # Let's verify that the variables are correctly populated first.

    assert vars["cpu_request"] == 0.5
    assert vars["cpu_limit"] == 1.0
    assert vars["mem_request"] == 2.0
    assert vars["mem_limit"] == 4.0

    # Basic check against the template file content to ensure placeholders exist
    import os

    template_path = os.path.join(svc.template_directory, "10-cluster.yml.j2")
    with open(template_path, "r") as f:
        content = f.read()

    assert 'cpu: "{{ cpu_request }}"' in content
    assert 'memory: "{{ mem_request }}Gi"' in content
    assert 'cpu: "{{ cpu_limit }}"' in content
    assert 'memory: "{{ mem_limit }}Gi"' in content
