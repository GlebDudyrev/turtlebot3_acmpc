"""PPO Trainer for AC-MPC."""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions.normal import Normal

from ..cases import Case
from ..cases.configs import ACMPCConfig, CaseConfig, PPOConfig
from ..cases.registry import CaseRegistryInstance
from ..models import ACMPCModel
from .base import BaseTrainer
from .buffer import RolloutBuffer


class PPOTrainer(BaseTrainer):
    """PPO Trainer for AC-MPC.

    Uses differentiable MPC as the policy (actor) and Value Network as critic.
    Exploration is done by sampling from N(mean, std) where mean is MPC output.

    Architecture:
        observation → NeuralCostMap → (Q_diag, p) → DifferentiableMPC → action
        observation → ValueNetwork → V(s)

    Training:
        - Processes one sample at a time (batch=1) to ensure gradient flow through MPC
        - Uses gradient accumulation across all samples in a batch
        - Proper PPO clipped surrogate objective
    """

    def __init__(
        self,
        model: ACMPCModel,
        ppo_config: PPOConfig,
        acmpc_config: ACMPCConfig,
        env_config,
        case: Case,
        device: str = "cpu",
    ):
        self.model = model.to(device)
        self.ppo_config = ppo_config
        self.acmpc_config = acmpc_config
        self.env_config = env_config
        self.case = case
        self._device = torch.device(device)

        self._global_step = 0
        self._epoch = 0

        obs_dim = env_config.observation_dim
        action_dim = 2  # linear velocity, angular velocity

        self.buffer = RolloutBuffer(
            obs_dim=obs_dim,
            action_dim=action_dim,
            n_steps=ppo_config.n_steps,
            gamma=ppo_config.gamma,
            gae_lambda=ppo_config.gae_lambda,
            device=self._device,
        )

        self.exploration_std = ppo_config.exploration_max_std
        self.exploration_max_std = ppo_config.exploration_max_std
        self.exploration_min_std = ppo_config.exploration_min_std
        self.exploration_epochs = ppo_config.exploration_epochs

        self.action_low = torch.tensor(
            env_config.action_low, dtype=torch.float32, device=self._device
        )
        self.action_high = torch.tensor(
            env_config.action_high, dtype=torch.float32, device=self._device
        )

        self.actor_optimizer = optim.Adam(
            self.model.cost_map.parameters(),
            lr=ppo_config.learning_rate,
        )
        self.critic_optimizer = optim.Adam(
            self.model.value_network.parameters(),
            lr=ppo_config.learning_rate,
        )

        self.mse_loss = nn.MSELoss()

    def sample_action(
        self,
        obs: torch.Tensor,
        state: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample action from policy with exploration noise.

        Args:
            obs: Observation tensor [batch, obs_dim]
            state: State for MPC [batch, n_states]
            deterministic: If True, return MPC output without noise

        Returns:
            action: Sampled action [batch, action_dim]
            log_prob: Log probability of action [batch]
            value: Value estimate V(s) [batch]
        """
        mpc_action, value = self.model(obs, state)

        if deterministic or self.exploration_std <= 0:
            action = mpc_action
            log_prob = torch.zeros(action.shape[0], device=self._device)
            return action, log_prob, value.squeeze(-1)

        dist = Normal(mpc_action, self.exploration_std)
        raw_action = dist.rsample()

        action = torch.clamp(raw_action, self.action_low, self.action_high)
        log_prob = dist.log_prob(raw_action).sum(dim=-1)

        return action, log_prob, value.squeeze(-1)

    def collect_rollouts(self, env) -> dict[str, float]:
        """Collect rollout data by interacting with environment.

        Args:
            env: Gymnasium environment

        Returns:
            Dictionary of rollout metrics.
        """
        self.model.eval()

        obs, _ = env.reset()
        total_reward = 0.0
        ep_count = 0
        ep_rewards = []

        self.buffer.reset()

        for step in range(self.ppo_config.n_steps):
            obs_tensor = torch.tensor(
                obs, dtype=torch.float32, device=self._device
            ).unsqueeze(0)

            with torch.no_grad():
                action, log_prob, value = self.sample_action(obs_tensor)
                action_np = action.cpu().numpy()[0]
                value_np = value.cpu().numpy()[0]

            next_obs, reward, terminated, truncated, _ = env.step(action_np)

            self.buffer.add(
                obs=obs,
                action=action_np,
                reward=reward,
                value=value_np,
                log_prob=log_prob.item(),
                done=terminated or truncated,
            )

            total_reward += reward

            if terminated or truncated:
                ep_rewards.append(total_reward)
                total_reward = 0.0
                ep_count += 1
                obs, _ = env.reset()
            else:
                obs = next_obs

        with torch.no_grad():
            final_obs = torch.tensor(
                obs, dtype=torch.float32, device=self._device
            ).unsqueeze(0)
            final_value = self.model.value_network(final_obs).item()

        self.buffer.compute_advantages(final_value)

        self._global_step += self.ppo_config.n_steps

        avg_ep_reward = sum(ep_rewards) / max(ep_count, 1) if ep_rewards else 0.0

        return {
            "rollout_reward": avg_ep_reward,
            "rollout_steps": self.ppo_config.n_steps,
            "episodes": ep_count,
            "exploration_std": self.exploration_std,
        }

    def train_step(self) -> dict[str, float]:
        """Execute one PPO training step.

        Processes each sample individually to ensure proper gradient flow through MPC.
        Uses gradient accumulation across all samples.

        Returns:
            Dictionary of training metrics.
        """
        self.model.train()

        (
            observations,
            actions,
            advantages,
            returns,
            old_log_probs,
            _,
        ) = self.buffer.get()

        advantages = advantages.detach()

        clip_fraction = 0.0
        policy_losses = []
        value_losses = []

        for epoch in range(self.ppo_config.n_epochs):
            indices = torch.randperm(self.ppo_config.n_steps, device=self._device)

            epoch_policy_loss = 0.0
            epoch_value_loss = 0.0
            epoch_clip_count = 0

            self.actor_optimizer.zero_grad()
            self.critic_optimizer.zero_grad()

            for idx in indices:
                obs = observations[idx : idx + 1].requires_grad_(True)
                action = actions[idx : idx + 1]
                advantage = advantages[idx : idx + 1]
                return_ = returns[idx : idx + 1]
                old_lp = old_log_probs[idx : idx + 1]

                # Full forward pass - fully differentiable!
                mpc_action, value = self.model(obs)

                dist = Normal(mpc_action, self.exploration_std + 1e-8)
                log_prob = dist.log_prob(action).sum(dim=-1)

                ratio = torch.exp(log_prob - old_lp)

                surr1 = ratio * advantage
                surr2 = (
                    torch.clamp(
                        ratio,
                        1.0 - self.ppo_config.clip_range,
                        1.0 + self.ppo_config.clip_range,
                    )
                    * advantage
                )

                policy_loss = -torch.min(surr1, surr2)
                value_loss = self.mse_loss(value.squeeze(-1), return_)

                epoch_policy_loss += policy_loss.item()
                epoch_value_loss += value_loss.item()

                total_loss = policy_loss + self.ppo_config.vf_coef * value_loss
                total_loss.backward()

                with torch.no_grad():
                    if torch.abs(ratio - 1.0) > self.ppo_config.clip_range:
                        epoch_clip_count += 1

            nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.ppo_config.max_grad_norm,
            )

            self.actor_optimizer.step()
            self.critic_optimizer.step()

            n_samples = self.ppo_config.n_steps
            policy_losses.append(epoch_policy_loss / n_samples)
            value_losses.append(epoch_value_loss / n_samples)
            clip_fraction += epoch_clip_count / n_samples

        self._epoch += 1

        self.exploration_std = max(
            self.exploration_min_std,
            self.exploration_max_std * (1.0 - self._epoch / self.exploration_epochs),
        )

        return {
            "policy_loss": sum(policy_losses) / len(policy_losses),
            "value_loss": sum(value_losses) / len(value_losses),
            "exploration_std": self.exploration_std,
            "clip_fraction": clip_fraction / self.ppo_config.n_epochs,
        }

    def evaluate(self) -> dict[str, float]:
        """Run evaluation episode(s).

        Returns:
            Dictionary of evaluation metrics.
        """
        return {"eval_reward": 0.0}

    def save_checkpoint(self, path: Path) -> None:
        """Save trainer state to checkpoint file."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "actor_optimizer_state_dict": self.actor_optimizer.state_dict(),
            "critic_optimizer_state_dict": self.critic_optimizer.state_dict(),
            "epoch": self._epoch,
            "global_step": self._global_step,
            "exploration_std": self.exploration_std,
        }
        torch.save(checkpoint, path)

    def load_checkpoint(self, path: Path) -> None:
        """Load trainer state from checkpoint file."""
        checkpoint = torch.load(path, map_location=self._device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.actor_optimizer.load_state_dict(checkpoint["actor_optimizer_state_dict"])
        self.critic_optimizer.load_state_dict(checkpoint["critic_optimizer_state_dict"])
        self._epoch = checkpoint["epoch"]
        self._global_step = checkpoint["global_step"]
        self.exploration_std = checkpoint["exploration_std"]

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def global_step(self) -> int:
        return self._global_step

    @property
    def epoch(self) -> int:
        return self._epoch

    @classmethod
    def from_case(
        cls,
        case_config: CaseConfig | str,
        device: str = "auto",
        **kwargs,
    ) -> "PPOTrainer":
        """Create trainer from case configuration.

        Args:
            case_config: Case name or CaseConfig object
            device: Compute device (cpu, cuda, auto)
            **kwargs: Additional arguments

        Returns:
            Initialized PPOTrainer instance.
        """
        if isinstance(case_config, str):
            case = CaseRegistryInstance.get(case_config)
            case_config = case.config
        else:
            case = Case(
                name=case_config.name,
                description=case_config.description,
                config=case_config,
            )

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        model = ACMPCModel(
            obs_dim=case_config.env.observation_dim,
            n_states=3,
            horizon=case_config.acmpc.mpc.horizon,
            cost_map_hidden_layers=case_config.acmpc.cost_map.hidden_layers,
            value_hidden_layers=case_config.acmpc.value_network.hidden_layers,
            mpc_horizon=case_config.acmpc.mpc.horizon,
        )

        return cls(
            model=model,
            ppo_config=case_config.ppo,
            acmpc_config=case_config.acmpc,
            env_config=case_config.env,
            case=case,
            device=device,
        )
