from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):

    def __init__(self, name: str):
        self._name = name
        self._registry: dict[str, T] = {}

    def register(self, name: str, item: T | None = None) -> Callable[[T], T] | T:
        if item is None:

            def decorator(item: T) -> T:
                if name in self._registry:
                    raise ValueError(f"{self._name} '{name}' already registered")
                self._registry[name] = item
                return item

            return decorator
        else:
            if name in self._registry:
                raise ValueError(f"{self._name} '{name}' already registered")
            self._registry[name] = item
            return item

    def get(self, name: str) -> T:
        if name not in self._registry:
            available = ", ".join(self._registry.keys())
            raise KeyError(
                f"{self._name} '{name}' not found. " f"Available: {available}"
            )
        return self._registry[name]

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def list_available(self) -> list[str]:
        return list(self._registry.keys())
