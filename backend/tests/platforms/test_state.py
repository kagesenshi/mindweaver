import pytest
from datetime import datetime
from pydantic import ValidationError
from mindweaver.platform_service.base import PlatformStateBase


# Define a concrete model for testing
class MockPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_test_platform_state"


def test_platform_state_instantiation():
    """Test that PlatformStateBase can be instantiated with all fields"""
    now = datetime.now()
    state = MockPlatformState(
        status="online",
        active=True,
        message="Running smoothly",
        last_heartbeat=now,
        extra_data={"replica_count": 3},
    )
    assert state.status == "online"
    assert state.active is True
    assert state.message == "Running smoothly"
    assert state.last_heartbeat == now
    assert state.extra_data == {"replica_count": 3}


def test_platform_state_defaults():
    """Test default values of PlatformStateBase"""
    state = MockPlatformState()
    assert state.status == "pending"
    assert state.active is True
    assert state.message is None
    assert state.last_heartbeat is None
    assert state.extra_data == {}


def test_platform_state_status_validation():
    """Test validation of status field using Literal values"""
    # Valid statuses
    for status in ["online", "offline", "pending", "error"]:
        state = MockPlatformState.model_validate({"status": status})
        assert state.status == status

    # Invalid status
    with pytest.raises(ValidationError):
        MockPlatformState.model_validate({"status": "invalid"})


def test_platform_state_extra_data_json():
    """Test that extra_data accepts a dictionary (JSON)"""
    complex_data = {"nested": {"key": "value"}, "list": [1, 2, 3], "bool": True}
    state = MockPlatformState(extra_data=complex_data)
    assert state.extra_data == complex_data
