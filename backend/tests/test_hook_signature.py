import pytest
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


class SignatureMockModel(NamedBase, table=True):
    pass


def test_valid_signatures():
    try:

        class ValidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @before_create
            async def hook_before_create(self, data):
                pass

            @after_create
            async def hook_after_create(self, model):
                pass

            @before_update
            async def hook_before_update(self, model, data):
                pass

            @after_update
            async def hook_after_update(self, model):
                pass

            @before_delete
            async def hook_before_delete(self, model):
                pass

            @after_delete
            async def hook_after_delete(self, model):
                pass

    except TypeError as e:
        pytest.fail(f"Valid signatures raised TypeError: {e}")


def test_invalid_before_create():
    with pytest.raises(TypeError, match="before_create hook must accept 2 arguments"):

        class InvalidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @before_create
            async def hook(self):  # Missing data
                pass

    with pytest.raises(TypeError, match="before_create hook must accept 2 arguments"):

        class InvalidService2(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @before_create
            async def hook(self, data, extra):  # Extra arg
                pass


def test_invalid_after_create():
    with pytest.raises(TypeError, match="after_create hook must accept 2 arguments"):

        class InvalidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @after_create
            async def hook(self):  # Missing model
                pass


def test_invalid_before_update():
    with pytest.raises(TypeError, match="before_update hook must accept 3 arguments"):

        class InvalidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @before_update
            async def hook(self, model):  # Missing data
                pass


def test_invalid_after_update():
    with pytest.raises(TypeError, match="after_update hook must accept 2 arguments"):

        class InvalidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @after_update
            async def hook(self):  # Missing model
                pass


def test_invalid_before_delete():
    with pytest.raises(TypeError, match="before_delete hook must accept 2 arguments"):

        class InvalidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @before_delete
            async def hook(self):  # Missing model
                pass


def test_invalid_after_delete():
    with pytest.raises(TypeError, match="after_delete hook must accept 2 arguments"):

        class InvalidService(Service[SignatureMockModel]):
            @classmethod
            def model_class(cls):
                return SignatureMockModel

            @after_delete
            async def hook(self):  # Missing model
                pass
