import pytest
import asyncio
from unittest.mock import MagicMock
from fastapi import Request
from sqlmodel import Session

from mindweaver.fw.model import NamedBase
from mindweaver.fw.service import Service
from mindweaver.fw.state import BaseState


# Create dummy model
class StateDummyModel(NamedBase, table=True):
    pass


# Create dummy base service
class StateDummyService(Service[StateDummyModel]):
    @classmethod
    def model_class(cls):
        return StateDummyModel


@StateDummyService.with_state()
class BaseStateCls(BaseState):
    async def get(self):
        return {"state": "base"}


# Create dummy child service 1
class ChildService(StateDummyService):
    pass


# Create dummy child service 2
class OverriddenChildService(StateDummyService):
    pass


@OverriddenChildService.with_state()
class OverriddenStateCls(BaseState):
    async def get(self):
        return {"state": "overridden"}


def test_state_registration_class_methods():
    # Check base service state class
    base_state_cls = StateDummyService.get_state_class()
    assert base_state_cls is not None
    assert base_state_cls.__name__ == "BaseStateCls"

    # Check child service 1 inherits base state class
    child_state_cls = ChildService.get_state_class()
    assert child_state_cls is not None
    assert child_state_cls.__name__ == "BaseStateCls"
    assert child_state_cls == base_state_cls

    # Check child service 2 has overridden state class
    overridden_state_cls = OverriddenChildService.get_state_class()
    assert overridden_state_cls is not None
    assert overridden_state_cls.__name__ == "OverriddenStateCls"
    assert overridden_state_cls != base_state_cls


@pytest.mark.asyncio
async def test_state_execution_routing():
    model = StateDummyModel(id=1, name="test")
    svc = StateDummyService(MagicMock(spec=Request), MagicMock(spec=Session))
    child_svc = ChildService(MagicMock(spec=Request), MagicMock(spec=Session))
    override_svc = OverriddenChildService(
        MagicMock(spec=Request), MagicMock(spec=Session)
    )

    # Base service state execution
    base_state_cls = StateDummyService.get_state_class()
    base_inst = base_state_cls(model, svc)
    assert await base_inst.get() == {"state": "base"}

    # Child service state execution
    child_state_cls = ChildService.get_state_class()
    child_inst = child_state_cls(model, child_svc)
    assert await child_inst.get() == {"state": "base"}

    # Overridden Child service state execution
    override_state_cls = OverriddenChildService.get_state_class()
    override_inst = override_state_cls(model, override_svc)
    assert await override_inst.get() == {"state": "overridden"}
