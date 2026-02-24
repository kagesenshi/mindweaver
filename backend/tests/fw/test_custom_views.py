# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi import APIRouter
from mindweaver.fw.model import NamedBase
from mindweaver.fw.service import Service


class CustomViewDummyModel(NamedBase, table=True):
    __tablename__ = "custom_view_dummy"


class BaseCustomViewService(Service[CustomViewDummyModel]):
    @classmethod
    def model_class(cls):
        return CustomViewDummyModel


@BaseCustomViewService.service_view("POST", "/base-service")
def base_service_func():
    return "base service"


@BaseCustomViewService.model_view(
    "GET", "/base-model", description="test description", response_model=str
)
async def base_model_func():
    return "base model"


class ChildCustomViewService(BaseCustomViewService):
    pass


@ChildCustomViewService.service_view("PUT", "/child-service")
def child_service_func():
    return "child service"


def test_custom_views_registration():
    """Test that custom views are registered properly."""
    base_views = BaseCustomViewService.get_custom_views()
    assert len(base_views) == 2
    types = [v["type"] for v in base_views]
    assert "service" in types
    assert "model" in types

    model_view = next(v for v in base_views if v["type"] == "model")
    assert model_view["method"] == "GET"
    assert model_view["path"] == "/base-model"
    assert model_view["kwargs"] == {
        "description": "test description",
        "response_model": str,
    }


def test_custom_views_inheritance():
    """Test that child services inherit views from parent services but don't mutate them."""
    child_views = ChildCustomViewService.get_custom_views()
    # Should contain 2 from parent and 1 from child
    assert len(child_views) == 3

    # Parent should still only have 2
    parent_views = BaseCustomViewService.get_custom_views()
    assert len(parent_views) == 2


def test_custom_views_mounts_on_router():
    """Test that custom views are correctly mounted on the APIRouter."""
    # Force new router creation just in case
    ChildCustomViewService._router = None
    router = ChildCustomViewService.router()
    routes = router.routes

    # Service path is /custom_view_dummy_models
    # Model path is /custom_view_dummy_models/{id}
    route_paths = [r.path for r in routes]

    assert "/custom_view_dummy_models/base-service" in route_paths
    assert "/custom_view_dummy_models/{id}/base-model" in route_paths
    assert "/custom_view_dummy_models/child-service" in route_paths

    # Verify attributes of the mounted routes
    base_service_route = next(
        r for r in routes if r.path == "/custom_view_dummy_models/base-service"
    )
    assert "POST" in base_service_route.methods

    base_model_route = next(
        r for r in routes if r.path == "/custom_view_dummy_models/{id}/base-model"
    )
    assert "GET" in base_model_route.methods
    assert base_model_route.description == "test description"


def test_custom_views_negative_missing_kwargs():
    """Test that using the decorators with missing required arguments raises TypeError."""
    # Method and path are positional required arguments, so omit them should raise error
    with pytest.raises(TypeError):

        @BaseCustomViewService.service_view(path="/only-path")
        def wrong_service_func():
            pass

    with pytest.raises(TypeError):

        @BaseCustomViewService.model_view(method="GET")
        def wrong_model_func():
            pass
