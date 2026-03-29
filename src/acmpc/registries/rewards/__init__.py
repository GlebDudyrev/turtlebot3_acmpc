"""Reward functions."""

from .dense_goal import dense_goal_reward
from .registry import RewardRegistry

__all__ = [
    "RewardRegistry",
]
