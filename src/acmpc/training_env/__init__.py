"""Environment layer for TurtleBot3 AC-MPC."""

import gymnasium as gym

from .turtlebot_env import TurtleBotEnv, make

gym.register(
    id="turtlebot3-acmpc-v0",
    entry_point="acmpc.training_env:make",
)

__all__ = ["TurtleBotEnv", "make"]
