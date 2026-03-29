from collections.abc import Callable

from ..registry import Registry

RewardFn = Callable[..., float]
RewardRegistry = Registry[RewardFn]("reward")
