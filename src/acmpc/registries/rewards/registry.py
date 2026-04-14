from collections.abc import Callable

from ..registry import Registry

RewardFn = Callable[..., float]
RewardRegistry = Registry[RewardFn]("reward")


def list_rewards() -> list[str]:
    return RewardRegistry.list_available()
