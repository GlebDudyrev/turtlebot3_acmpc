"""Environment configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from acmpc.registries.rewards import RewardRegistry
from acmpc.registries.robots import RobotParamsRegistry


class EnvConfig(BaseModel):
    """Configuration for training environment."""

    world_name: str = Field(
        default="turtlebot3_empty", description="Name of world (from configs/worlds)"
    )

    robot_name: Literal["burger", "waffle", "waffle_pi"] = Field(
        default="burger",
        description="Robot model name",
    )

    reward_fn: str = Field(
        default="dense_goal",
        description="Reward function name from registry",
    )

    goal_threshold: float = Field(
        default=0.3,
        ge=0.1,
        description="Distance threshold for goal completion",
    )
    goal_min_distance: float = Field(
        default=1.0,
        ge=0.5,
        description="Minimum goal spawn distance from robot",
    )
    goal_max_distance: float = Field(
        default=3.0,
        ge=1.0,
        description="Maximum goal spawn distance from robot",
    )

    max_steps: int = Field(
        default=500,
        ge=1,
        description="Maximum steps per episode",
    )
    dt: float = Field(
        default=0.1,
        gt=0.0,
        le=1.0,
        description="Simulation timestep",
    )

    @field_validator("world_name")
    @classmethod
    def check_world_name(cls, value: str) -> str:
        path = Path("configs/worlds") / f"{value}.world"
        if path.exists():
            return value
        else:
            raise ValueError(f"World file with name {value} does not exist")

    @field_validator("reward_fn")
    @classmethod
    def check_reward_fn(cls, value: str) -> str:
        if value not in RewardRegistry:
            available = RewardRegistry.list_available()
            raise ValueError(
                f"Reward function '{value}' not found. " f"Available: {available}"
            )
        return value

    @field_validator("robot_name")
    @classmethod
    def check_robot_name(cls, value: str) -> str:
        if value not in RobotParamsRegistry:
            available = RobotParamsRegistry.list_available()
            raise ValueError(f"Robot '{value}' not found. Available: {available}")
        return value
