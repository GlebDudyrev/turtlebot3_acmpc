from collections.abc import Callable

from ..registries.registry import Registry
from .case import Case
from .configs import CaseConfig


class CaseRegistry(Registry[Case]):
    """Registry for training cases."""

    def get_config(self, name: str) -> CaseConfig:
        return self.get(name).config

    def list_cases(self) -> list[str]:
        return self.list_available()


CaseRegistryInstance = CaseRegistry("case")


def get_case(name: str) -> Case:
    """Get a case by name."""
    return CaseRegistryInstance.get(name)


def list_cases() -> list[str]:
    """List all available cases."""
    return CaseRegistryInstance.list_cases()
