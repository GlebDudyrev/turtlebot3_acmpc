"""Rollout buffer for storing trajectory data and computing GAE."""

from __future__ import annotations

import torch
from numpy.typing import ArrayLike


class RolloutBuffer:
    """Stores rollout data for PPO training with Generalized Advantage Estimation."""

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        n_steps: int,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        device: str = "cpu",
    ):
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.n_steps = n_steps
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.device = device

        self.observations = torch.zeros(
            (n_steps, obs_dim), dtype=torch.float32, device=device
        )
        self.actions = torch.zeros(
            (n_steps, action_dim), dtype=torch.float32, device=device
        )
        self.rewards = torch.zeros(n_steps, dtype=torch.float32, device=device)
        self.values = torch.zeros(n_steps + 1, dtype=torch.float32, device=device)
        self.log_probs = torch.zeros(n_steps, dtype=torch.float32, device=device)
        self.dones = torch.zeros(n_steps, dtype=torch.float32, device=device)

        self.advantages = None
        self.returns = None

        self.ptr = 0

    def add(
        self,
        obs: ArrayLike,
        action: ArrayLike,
        reward: float,
        value: float,
        log_prob: float,
        done: bool,
    ):
        """Add a transition to the buffer."""
        self.observations[self.ptr] = torch.as_tensor(
            obs, dtype=torch.float32, device=self.device
        )
        self.actions[self.ptr] = torch.as_tensor(
            action, dtype=torch.float32, device=self.device
        )
        self.rewards[self.ptr] = float(reward)
        self.values[self.ptr] = float(value)
        self.log_probs[self.ptr] = float(log_prob)
        self.dones[self.ptr] = float(done)
        self.ptr += 1

    def compute_advantages(self, final_value: float):
        """Compute Generalized Advantage Estimation."""
        self.values[self.ptr] = float(final_value)

        advantages = torch.zeros(self.n_steps, dtype=torch.float32, device=self.device)
        gae = 0.0

        for t in reversed(range(self.n_steps)):
            if t == self.n_steps - 1:
                next_value = float(final_value)
            else:
                next_value = self.values[t + 1].item()

            delta = (
                self.rewards[t].item()
                + self.gamma * next_value * (1.0 - self.dones[t].item())
                - self.values[t].item()
            )
            gae = (
                delta
                + self.gamma * self.gae_lambda * (1.0 - self.dones[t].item()) * gae
            )
            advantages[t] = gae

        self.advantages = advantages
        self.returns = advantages + self.values[:-1]

    def get(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return normalized advantages and data for training."""
        if self.advantages is None or self.returns is None:
            raise RuntimeError("Must call compute_advantages() before get()")

        advantages = (self.advantages - self.advantages.mean()) / (
            self.advantages.std() + 1e-8
        )

        return (
            self.observations.detach(),
            self.actions.detach(),
            advantages.detach(),
            self.returns.detach(),
            self.log_probs.detach(),
            self.values[:-1].detach(),
        )

    def reset(self):
        """Reset the buffer."""
        self.ptr = 0
        self.advantages = None
        self.returns = None
