"""Case configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .acmpc import ACMPCConfig
from .env import EnvConfig
from .ppo import PPOConfig


class CaseConfig(BaseModel):
    """Configuration for a training case."""

    name: str = Field(description="Unique case identifier")
    description: str = Field(default="", description="Human-readable description")

    env: EnvConfig = Field(
        default_factory=EnvConfig,
        description="Environment configuration",
    )

    acmpc: ACMPCConfig = Field(
        default_factory=ACMPCConfig,
        description="AC-MPC components configuration",
    )

    ppo: PPOConfig = Field(
        default_factory=PPOConfig,
        description="PPO hyperparameters",
    )

    device: str = Field(
        default="auto",
        description="Compute device (cpu, cuda, auto)",
    )
    seed: int = Field(
        default=42,
        description="Random seed for reproducibility",
    )

    max_epochs: int = Field(
        default=1000,
        ge=1,
        description="Maximum training epochs",
    )
    eval_freq: int = Field(
        default=10,
        ge=1,
        description="Evaluation frequency in epochs",
    )
    save_freq: int = Field(
        default=50,
        ge=1,
        description="Checkpoint save frequency in epochs",
    )
