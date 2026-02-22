import pytest
import asyncio
from unittest.mock import MagicMock
from fastapi import Request
from sqlmodel import Session, SQLModel

from mindweaver.fw.model import NamedBase
from mindweaver.fw.service import Service
from mindweaver.fw.action import BaseAction


# Create dummy model
class DummyModel(NamedBase, table=True):
    pass


# Create dummy base service
class DummyService(Service[DummyModel]):
    @classmethod
    def model_class(cls):
        return DummyModel


@DummyService.register_action("base_action")
class BaseActionCls(BaseAction):
    async def available(self):
        return True

    def __call__(self, **kwargs):
        return {"message": "from base", "param": kwargs.get("param")}


@DummyService.register_action("overridden_action")
class OverriddenAction(BaseAction):
    def available(self):  # test synchronous available
        return False

    def __call__(self, **kwargs):
        return {"message": "from base restricted"}


# Create dummy child service
class ChildService(DummyService):
    pass


@ChildService.register_action("child_action")
class ChildAction(BaseAction):
    async def __call__(
        self, **kwargs
    ):  # Test without available, should default to True logic
        return {"message": "from child"}


@ChildService.register_action("overridden_action")
class OverriddenActionChild(BaseAction):
    def available(self):
        return True

    def __call__(self, **kwargs):
        assert self.model is not None
        assert self.svc is not None
        assert self.session is not None
        # request will be None because we didn't pass it in mock correctly but it shouldn't error
        return {"message": "from child overridden"}


def test_action_registration_class_methods():

    # Check base actions
    base_actions = DummyService.get_actions()
    assert "base_action" in base_actions
    assert "overridden_action" in base_actions
    assert "child_action" not in base_actions

    # Check child actions (should include base + child overridden)
    child_actions = ChildService.get_actions()
    assert "base_action" in child_actions
    assert "child_action" in child_actions
    assert "overridden_action" in child_actions

    # Check overriding
    assert child_actions["overridden_action"].__name__ == "OverriddenActionChild"
    assert base_actions["overridden_action"].__name__ == "OverriddenAction"


def test_action_registration_duplicate_error():
    with pytest.raises(
        ValueError,
        match="Action 'duplicate_action' is already registered on DummyService",
    ):

        @DummyService.register_action("duplicate_action")
        class Action1(BaseAction):
            def __call__(self, **kwargs):
                pass

        @DummyService.register_action("duplicate_action")
        class Action2(BaseAction):
            def __call__(self, **kwargs):
                pass


@pytest.mark.asyncio
async def test_action_execution_routing():
    model = DummyModel(id=1, name="test")
    svc = ChildService(MagicMock(spec=Request), MagicMock(spec=Session))

    actions = ChildService.get_actions()

    # Simulate execution of 'overridden_action'
    action_cls = actions["overridden_action"]
    action_instance1 = action_cls(model, svc)
    assert action_instance1.available() is True
    res1 = action_instance1()
    assert res1["message"] == "from child overridden"

    # Simulate execution of 'child_action' (async)
    action_cls2 = actions["child_action"]
    action_instance2 = action_cls2(model, svc)
    res2 = await action_instance2()
    assert res2["message"] == "from child"

    # Simulate execution of 'base_action'
    action_cls3 = actions["base_action"]
    action_instance3 = action_cls3(model, svc)
    res3 = action_instance3(param="test_param")
    assert res3["message"] == "from base"
    assert res3["param"] == "test_param"

    # Test unavailable base overridden action
    action_cls4 = DummyService.get_actions()["overridden_action"]
    action_instance4 = action_cls4(model, svc)
    assert action_instance4.available() is False
