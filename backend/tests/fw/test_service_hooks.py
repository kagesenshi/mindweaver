# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock
from mindweaver.fw.service import (
    Service,
    before_create,
    after_create,
    before_update,
    after_update,
    before_delete,
    after_delete,
)
from mindweaver.fw.model import NamedBase


class MockModel(NamedBase, table=True):
    description: str | None = None


class MockService(Service[MockModel]):
    @classmethod
    def model_class(cls):
        return MockModel

    @before_create
    async def hook_before(self, data):
        data.name = "modified_before"

    @after_create
    async def hook_after(self, model):
        model.title = "modified_after"


class MockServiceSub(MockService):
    @before_create
    async def hook_before_sub(self, data):
        data.description = "sub_before"


@pytest.mark.asyncio
async def test_basic_hooks():
    mock_session = AsyncMock()
    mock_request = MagicMock()

    service = MockServiceSub(mock_request, mock_session)
    data = MockModel(name="original", title="original")

    # Mock session behavior
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    created_model = await service.create(data)

    # Verify before hooks
    assert created_model.name == "modified_before"
    assert created_model.description == "sub_before"

    # Verify after hooks
    assert created_model.title == "modified_after"


class OrderService(Service[MockModel]):
    @classmethod
    def model_class(cls):
        return MockModel

    @before_create
    async def hook_1(self, data):
        pass

    @before_create(after="hook_1")
    async def hook_2(self, data):
        pass

    @before_create(before="hook_1")
    async def hook_0(self, data):
        pass

    @after_create
    async def hook_a(self, model):
        pass

    @after_create(before="hook_a")
    async def hook_b(self, model):
        pass

    @before_update
    async def up_1(self, model, data):
        pass

    @before_update(after="up_1")
    async def up_2(self, model, data):
        pass

    @after_update
    async def up_a(self, model):
        pass

    @after_update(before="up_a")
    async def up_b(self, model):
        pass

    @before_delete
    async def del_1(self, model):
        pass

    @before_delete(after="del_1")
    async def del_2(self, model):
        pass

    @after_delete
    async def del_a(self, model):
        pass

    @after_delete(before="del_a")
    async def del_b(self, model):
        pass


@pytest.mark.asyncio
async def test_hook_dependencies():
    # Inspect the sorted hooks directly on the class

    before_create_hooks = [h.__name__ for h in OrderService._before_create_hooks]
    after_create_hooks = [h.__name__ for h in OrderService._after_create_hooks]
    before_update_hooks = [h.__name__ for h in OrderService._before_update_hooks]
    after_update_hooks = [h.__name__ for h in OrderService._after_update_hooks]
    before_delete_hooks = [h.__name__ for h in OrderService._before_delete_hooks]
    after_delete_hooks = [h.__name__ for h in OrderService._after_delete_hooks]

    # Expected order includes base mixin hooks first for create/update:
    # hook_0 -> hook_1 -> hook_2
    assert "hook_0" in before_create_hooks
    assert "hook_1" in before_create_hooks
    assert "hook_2" in before_create_hooks
    idx0 = before_create_hooks.index("hook_0")
    idx1 = before_create_hooks.index("hook_1")
    idx2 = before_create_hooks.index("hook_2")
    assert idx0 < idx1 < idx2

    assert after_create_hooks == ["hook_b", "hook_a"]

    # Update hooks: _handle_hashed_update -> _handle_redacted_update -> up_1 -> up_2
    assert "up_1" in before_update_hooks
    assert "up_2" in before_update_hooks
    u_idx1 = before_update_hooks.index("up_1")
    u_idx2 = before_update_hooks.index("up_2")
    assert u_idx1 < u_idx2

    assert after_update_hooks == ["up_b", "up_a"]

    # Delete hooks (no base mixin hooks currently)
    assert before_delete_hooks == ["del_1", "del_2"]
    assert after_delete_hooks == ["del_b", "del_a"]


def test_circular_dependency():
    try:

        class CircularService(Service[MockModel]):
            @classmethod
            def model_class(cls):
                return MockModel

            @before_create(after="hook_y")
            async def hook_x(self, data):
                pass

            @before_create(after="hook_x")
            async def hook_y(self, data):
                pass

    except ValueError as e:
        assert "Circular dependency detected" in str(e)
        return

    pytest.fail("Circular dependency did not raise ValueError")


class BaseOrderService(Service[MockModel]):
    @classmethod
    def model_class(cls):
        return MockModel

    @before_create
    async def hook_base(self, data):
        pass


class SubOrderService(BaseOrderService):
    @before_create
    async def hook_sub(self, data):
        pass


@pytest.mark.asyncio
async def test_inheritance_order():
    # Base hooks should come before Sub hooks by default (if no deps)
    # because we iterate MRO reversed (Base -> Sub)

    hooks = [h.__name__ for h in SubOrderService._before_create_hooks]
    # Filter out base mixin hooks to focus on inheritance test
    hooks = [h for h in hooks if not h.startswith("_handle_")]
    assert hooks == ["hook_base", "hook_sub"]


class UpdateDeleteService(Service[MockModel]):
    @classmethod
    def model_class(cls):
        return MockModel

    @before_update
    async def hook_before_update(self, model, data):
        data.description = "modified_before_update"

    @after_update
    async def hook_after_update(self, model):
        model.title = "modified_after_update"

    @before_delete
    async def hook_before_delete(self, model):
        # We can test side effects here, e.g. setting a flag on the model object in memory
        model.description = "deleted"

    @after_delete
    async def hook_after_delete(self, model):
        # Verify that we can still access the model
        assert model.description == "deleted"


@pytest.mark.asyncio
async def test_update_delete_hooks():
    mock_session = AsyncMock()
    mock_request = MagicMock()

    service = UpdateDeleteService(mock_request, mock_session)

    # Mock existing model
    existing_model = MockModel(id=1, name="existing", title="existing")

    # Mock session behavior
    mock_result = MagicMock()
    mock_result.first.return_value = existing_model
    mock_session.exec = AsyncMock(return_value=mock_result)

    mock_session.get = AsyncMock(return_value=existing_model)
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.delete = AsyncMock()

    # Test Update
    update_data = MockModel(name="existing", title="updated")
    updated_model = await service.update(1, update_data)

    # Verify before_update hook
    # The data object passed to update should have been modified
    assert update_data.description == "modified_before_update"

    # Verify after_update hook
    assert updated_model.title == "modified_after_update"

    # Test Delete
    await service.delete(1)

    # Verify before_delete hook (via side effect on model)
    assert existing_model.description == "deleted"

    # Verify delete was called
    mock_session.delete.assert_called_with(existing_model)
