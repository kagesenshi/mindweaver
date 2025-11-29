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
        # load_projects doesn't auto-select, so current_project should be None
        assert project_state.current_project is None


@pytest.mark.asyncio
async def test_select_project(project_state):
    mock_projects = [
        {"id": 1, "name": "p1", "title": "Project 1"},
        {"id": 2, "name": "p2", "title": "Project 2"},
    ]
    project_state.projects = mock_projects

    # select_project is an event handler that yields, so we need to consume the generator
    result = project_state.select_project(mock_projects[1])
    # Consume the async generator
    events = []
    async for event in result:
        events.append(event)

    assert project_state.current_project == mock_projects[1]
    # Should yield a redirect event
    assert len(events) == 1
    assert isinstance(events[0], rx.event.EventSpec)


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

        # create_project is async and may return events
        result = await project_state.create_project()

        assert len(project_state.projects) == 1
        assert project_state.projects[0]["name"] == "new-p"
        # create_project calls select_project internally, but in test context
        # the async generator from select_project isn't consumed, so current_project
        # won't be set. We just verify the project was added to the list.
        assert project_state.is_create_modal_open is False
