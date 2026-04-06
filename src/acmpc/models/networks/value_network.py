"""Value Network (Critic) for AC-MPC."""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


class ValueNetwork(nn.Module):
    """Value Network (Critic) for AC-MPC.

    Estimates V(s) - the value of a state for advantage estimation in PPO.
    """

    def __init__(
        self,
        obs_dim: int,
        hidden_layers: list[int] | None = None,
    ):
        """Initialize Value Network.

        Args:
            obs_dim: Observation dimension
            hidden_layers: List of hidden layer sizes
        """
        super().__init__()

        if hidden_layers is None:
            hidden_layers = [128, 128]

        layers = []
        in_dim = obs_dim
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU())
            in_dim = hidden_dim

        layers.append(nn.Linear(in_dim, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, obs: Tensor) -> Tensor:
        """Forward pass.

        Args:
            obs: Observation [batch, obs_dim] or [obs_dim]

        Returns:
            value: V(s) [batch, 1] or [1]
        """
        squeeze = False
        if obs.dim() == 1:
            obs = obs.unsqueeze(0)
            squeeze = True

        value = self.network(obs)

        if squeeze:
            value = value.squeeze(0)

        return value
