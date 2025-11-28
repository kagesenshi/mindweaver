import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import reflex as rx
from mindweaver_fe.states.project_state import ProjectState


@pytest.fixture
def project_state():
    return ProjectState()


@pytest.mark.asyncio
async def test_load_projects(project_state):
    mock_projects = [
        {"id": 1, "name": "p1", "title": "Project 1"},
        {"id": 2, "name": "p2", "title": "Project 2"},
    ]

    with patch(
        "mindweaver_fe.states.project_state.project_client.list_all",
        new_callable=AsyncMock,
    ) as mock_list_all:
        mock_list_all.return_value = mock_projects

        await project_state.load_projects()

        assert len(project_state.projects) == 2
        assert project_state.projects[0]["name"] == "p1"
        assert (
            project_state.current_project == mock_projects[0]
        )  # Should select first by default


@pytest.mark.asyncio
async def test_select_project(project_state):
    mock_projects = [
        {"id": 1, "name": "p1", "title": "Project 1"},
        {"id": 2, "name": "p2", "title": "Project 2"},
    ]
    project_state.projects = mock_projects

    await project_state.select_project(mock_projects[1])

    assert project_state.current_project == mock_projects[1]


@pytest.mark.asyncio
async def test_create_project(project_state):
    project_state.new_project_name = "new-p"
    project_state.new_project_description = "Desc"
    new_project = {
        "id": 3,
        "name": "new-p",
        "title": "new-p",
        "description": "Desc",
    }

    with patch(
        "mindweaver_fe.states.project_state.project_client.create",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = new_project

        await project_state.create_project()

        assert len(project_state.projects) == 1
        assert project_state.projects[0]["name"] == "new-p"
        assert (
            project_state.current_project == new_project
        )  # Should auto-select new project
