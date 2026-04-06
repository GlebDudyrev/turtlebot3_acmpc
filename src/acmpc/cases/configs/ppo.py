"""PPO configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PPOConfig(BaseModel):
    """Configuration for PPO hyperparameters."""

    learning_rate: float = Field(default=3e-4, ge=1e-6, le=1e-1)
    n_steps: int = Field(default=2048, ge=1)
    batch_size: int = Field(default=64, ge=1)
    n_epochs: int = Field(default=10, ge=1)
    gamma: float = Field(default=0.99, ge=0.0, le=1.0)
    gae_lambda: float = Field(default=0.95, ge=0.0, le=1.0)
    clip_range: float = Field(default=0.2, ge=0.0, le=1.0)
    ent_coef: float = Field(default=0.01, ge=0.0)
    vf_coef: float = Field(default=0.5, ge=0.0)
    max_grad_norm: float = Field(default=0.5, ge=0.0)

    exploration_max_std: float = Field(default=0.1, ge=0.0)
    exploration_min_std: float = Field(default=0.0, ge=0.0)
    exploration_epochs: int = Field(default=100, ge=1)
