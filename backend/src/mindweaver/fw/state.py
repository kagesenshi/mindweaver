import abc
from typing import Any


class BaseState(abc.ABC):
    """Base State class for Service plugin system."""

    def __init__(self, model, svc):
        self.model = model
        self.svc = svc
        self.session = getattr(svc, "session", None)
        self.request = getattr(svc, "request", None)

    @abc.abstractmethod
    async def get(self) -> dict[str, Any] | Any:
        """Returns the state of the model."""
        pass
