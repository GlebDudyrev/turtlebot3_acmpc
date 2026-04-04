from collections.abc import Callable

from pydantic import BaseModel, Field, model_validator

from ..registries.rewards import RewardRegistry
from ..registries.robots import RobotParams, RobotParamsRegistry
from .configs import CaseConfig, EnvConfig


class Case(BaseModel):
    """Training case - wrapper around CaseConfig with convenience methods."""

    name: str = Field(description="Unique case identifier")
    description: str = Field(default="", description="Human-readable description")
    config: CaseConfig = Field(description="Case configuration")

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_references(self) -> "Case":
        if self.config.env.reward_fn not in RewardRegistry:
            raise ValueError(
                f"Reward '{self.config.env.reward_fn}' not found. "
                f"Available: {RewardRegistry.list_available()}"
            )
        if self.config.env.robot_name not in RobotParamsRegistry:
            raise ValueError(
                f"Robot '{self.config.env.robot_name}' not found. "
                f"Available: {RobotParamsRegistry.list_available()}"
            )
        return self

    @property
    def reward_fn(self) -> Callable[..., float]:
        return RewardRegistry.get(self.config.env.reward_fn)

    @property
    def robot_params(self) -> RobotParams:
        return RobotParamsRegistry.get(self.config.env.robot_name)

    @property
    def env_config(self) -> EnvConfig:
        return self.config.env
