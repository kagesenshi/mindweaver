import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mindweaver_fe.states.project_state import ProjectState


@pytest.mark.asyncio
async def test_load_projects_restores_from_cookie():
    """Test that load_projects restores the current project from the cookie."""
    # Mock data
    mock_projects = [
        {"id": "p1", "name": "Project 1"},
        {"id": "p2", "name": "Project 2"},
    ]

    # Create a mock state instance
    state = ProjectState()

    # Mock the cookie value
    # In Reflex, cookies are accessed as attributes on the state
    state.current_project_id_cookie = "p2"

    # Mock the project client
    with patch("mindweaver_fe.states.project_state.project_client") as mock_client:
        mock_client.list_all = AsyncMock(return_value=mock_projects)

        # Run load_projects
        await state.load_projects()

        # Verify
        assert state.projects == mock_projects
        assert state.current_project == mock_projects[1]
        assert state.current_project["id"] == "p2"


@pytest.mark.asyncio
async def test_select_project_sets_cookie():
    """Test that select_project sets the cookie."""
    # Mock data
    project = {"id": "p1", "name": "Project 1"}

    # Create a mock state instance
    state = ProjectState()

    # Run select_project
    # select_project is an async generator (event handler)
    async for _ in state.select_project(project):
        pass

    # Verify
    assert state.current_project == project
    assert state.current_project_id_cookie == "p1"
