import abc
from typing import Any
import pydantic


class ActionRequest(pydantic.BaseModel):
    action: str
    parameters: dict[str, Any] = pydantic.Field(default_factory=dict)


class BaseAction(abc.ABC):
    """Base Action class for Service plugin system."""

    def __init__(self, model, svc):
        self.model = model
        self.svc = svc
        self.session = getattr(svc, "session", None)
        self.request = getattr(svc, "request", None)

    async def available(self) -> bool:
        """Returns True if the action is currently available."""
        return True

    @abc.abstractmethod
    def __call__(self, **kwargs):
        """Execute the action."""
        pass
