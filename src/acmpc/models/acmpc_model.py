"""AC-MPC Model - combines Cost Map, MPC, and Value Network."""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor

from .cost import NeuralCostMap
from .mpc import DifferentiableMPC
from .networks import ValueNetwork


class ACMPCModel(nn.Module):
    """AC-MPC Model: Neural Cost Map + MPC + Value Network.

    Forward:
        observation → NeuralCostMap → (Q_diag, p) → MPC → action
        observation → ValueNetwork → V(s)
    """

    def __init__(
        self,
        obs_dim: int,
        n_states: int = 3,
        horizon: int = 15,
        cost_map_hidden_layers: list[int] | None = None,
        value_hidden_layers: list[int] | None = None,
        mpc_horizon: int | None = None,
        mpc_dt: float = 0.1,
        mpc_control_bounds: tuple[float, float] = (-0.22, 0.22),
    ):
        """Initialize ACMPCModel.

        Args:
            obs_dim: Observation dimension
            n_states: Number of state dimensions
            horizon: MPC horizon
            cost_map_hidden_layers: Hidden layers for Neural Cost Map
            value_hidden_layers: Hidden layers for Value Network
            mpc_horizon: MPC horizon (overrides horizon if set)
            mpc_dt: MPC time step
            mpc_control_bounds: Control bounds
        """
        super().__init__()

        self.obs_dim = obs_dim
        self.n_states = n_states
        self.horizon = horizon

        # Neural Cost Map (Actor)
        self.cost_map = NeuralCostMap(
            obs_dim=obs_dim,
            n_states=n_states,
            horizon=horizon,
            hidden_layers=cost_map_hidden_layers,
        )

        # Differentiable MPC
        self.mpc = DifferentiableMPC(
            horizon=mpc_horizon or horizon,
            dt=mpc_dt,
            control_bounds=mpc_control_bounds,
        )

        # Value Network (Critic)
        self.value_network = ValueNetwork(
            obs_dim=obs_dim,
            hidden_layers=value_hidden_layers,
        )

    def forward(
        self,
        obs: Tensor,
        state: Tensor | None = None,
    ) -> tuple[Tensor, Tensor]:
        """Forward pass.

        Args:
            obs: Observation [batch, obs_dim]
            state: State for MPC [batch, n_states]. If None, uses zeros.

        Returns:
            action: Control [batch, n_controls]
            value: V(s) [batch, 1]
        """
        batch_size = obs.shape[0]

        # Get state for MPC
        if state is None:
            state = torch.zeros(batch_size, self.n_states, device=obs.device)

        # Get cost parameters from Neural Cost Map
        Q_diag, p = self.cost_map(obs)

        # Solve MPC
        action = self.mpc(state, Q_diag, p)

        # Get value estimate
        value = self.value_network(obs)

        return action, value
