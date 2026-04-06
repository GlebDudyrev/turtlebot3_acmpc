"""Neural Cost Map - outputs Q_diag and p for MPC."""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


class NeuralCostMap(nn.Module):
    """Neural Cost Map (Actor) for AC-MPC.

    Forward pass:
        observation → MLP → (Q_diag, p)

    Output shapes:
        Q_diag: [batch, horizon+1, n_states] - diagonal of Q matrix
        p:      [batch, horizon+1, n_states] - linear bias term

    The Q matrix defines state costs:
        x^T Q x penalizes states (e.g., distance to goal)

    The p vector provides goal direction:
        p^T x biases the trajectory toward the goal
    """

    def __init__(
        self,
        obs_dim: int,
        n_states: int,
        horizon: int,
        hidden_layers: list[int] | None = None,
    ):
        """Initialize Neural Cost Map.

        Args:
            obs_dim: Observation dimension (lidar + state + goal)
            n_states: Number of state dimensions (3 for TurtleBot: x, y, theta)
            horizon: MPC prediction horizon
            hidden_layers: List of hidden layer sizes
        """
        super().__init__()

        self.obs_dim = obs_dim
        self.n_states = n_states
        self.horizon = horizon

        if hidden_layers is None:
            hidden_layers = [128, 128]

        # Build MLP layers
        layers = []
        in_dim = obs_dim
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU())
            in_dim = hidden_dim

        self.mlp = nn.Sequential(*layers)

        # Output layers
        # Q_diag: (horizon + 1) * n_states values - initialize positive
        # p: (horizon + 1) * n_states values
        self.q_head = nn.Linear(in_dim, (horizon + 1) * n_states)
        self.p_head = nn.Linear(in_dim, (horizon + 1) * n_states)

        # Initialize Q head to produce reasonable positive values
        nn.init.constant_(self.q_head.bias, 1.0)
        nn.init.xavier_uniform_(self.q_head.weight)
        with torch.no_grad():
            self.q_head.weight.fill_(0.1)

    def forward(self, obs: Tensor) -> tuple[Tensor, Tensor]:
        """Forward pass.

        Args:
            obs: Observation [batch, obs_dim] or [obs_dim]

        Returns:
            Q_diag: [batch, horizon+1, n_states]
            p:      [batch, horizon+1, n_states]
        """
        squeeze = False
        if obs.dim() == 1:
            obs = obs.unsqueeze(0)
            squeeze = True

        # MLP forward
        features = self.mlp(obs)

        # Output heads
        Q_diag_flat = self.q_head(features)
        p_flat = self.p_head(features)

        # Reshape to [batch, horizon+1, n_states]
        Q_diag = Q_diag_flat.view(-1, self.horizon + 1, self.n_states)
        p = p_flat.view(-1, self.horizon + 1, self.n_states)

        # Apply softplus to Q_diag to ensure positive definite
        Q_diag = torch.nn.functional.softplus(Q_diag) + 1e-4

        # Scale p to have stronger effect on MPC
        # This helps MPC produce non-zero actions during training
        p = p * 10.0

        if squeeze:
            Q_diag = Q_diag.squeeze(0)
            p = p.squeeze(0)

        return Q_diag, p
