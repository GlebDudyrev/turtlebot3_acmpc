"""AC-MPC configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CostMapConfig(BaseModel):
    """Configuration for Neural Cost Map (Actor)."""

    matrix_type: Literal["diagonal", "cholesky", "full"] = Field(
        default="diagonal",
        description="Type of cost matrix parameterization",
    )
    hidden_layers: list[int] = Field(
        default=[128, 128],
        description="Hidden layer sizes for Neural Cost Map",
    )
    activation: str = Field(
        default="relu",
        description="Activation function for Neural Cost Map",
    )


class MPCConfig(BaseModel):
    """Configuration for Differentiable MPC (Solver)."""

    horizon: int = Field(
        default=15,
        ge=1,
        le=100,
        description="MPC prediction horizon",
    )
    solver_type: Literal["osqp", "qp"] = Field(
        default="osqp",
        description="QP solver type",
    )


class ValueNetworkConfig(BaseModel):
    """Configuration for Value Network (Critic)."""

    hidden_layers: list[int] = Field(
        default=[128, 128],
        description="Hidden layer sizes for Value Network",
    )
    activation: str = Field(
        default="relu",
        description="Activation function for Value Network",
    )


class ACMPCConfig(BaseModel):
    """Configuration for AC-MPC components."""

    cost_map: CostMapConfig = Field(
        default_factory=CostMapConfig,
        description="Neural Cost Map (Actor) configuration",
    )
    mpc: MPCConfig = Field(
        default_factory=MPCConfig,
        description="Differentiable MPC configuration",
    )
    value_network: ValueNetworkConfig = Field(
        default_factory=ValueNetworkConfig,
        description="Value Network (Critic) configuration",
    )
