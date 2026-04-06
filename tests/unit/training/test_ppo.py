"""Unit tests for PPO training."""

from __future__ import annotations

import numpy as np
import torch
import pytest
import gymnasium as gym

from acmpc.models import ACMPCModel
from acmpc.training.ppo import PPOTrainer
from acmpc.training.buffer import RolloutBuffer
from acmpc.cases.configs import PPOConfig, ACMPCConfig, EnvConfig


class MockEnv(gym.Env):
    """Mock environment for testing without ROS/Gazebo."""

    def __init__(self):
        super().__init__()
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(15,))
        self.action_space = gym.spaces.Box(low=-1, high=1, shape=(2,))
        self._state = None
        self._steps = 0
        self._max_steps = 100

    def reset(self, seed=None, options=None):
        self._state = np.random.randn(15).astype(np.float32)
        self._steps = 0
        return self._state, {}

    def step(self, action):
        self._steps += 1

        self._state = np.random.randn(15).astype(np.float32)

        reward = np.random.randn()
        terminated = self._steps >= self._max_steps
        truncated = False
        info = {}

        return self._state, reward, terminated, truncated, info


class TestRolloutBuffer:
    """Tests for RolloutBuffer."""

    @pytest.fixture
    def buffer(self):
        """Create RolloutBuffer instance."""
        return RolloutBuffer(
            obs_dim=15,
            action_dim=2,
            n_steps=100,
            gamma=0.99,
            gae_lambda=0.95,
            device="cpu",
        )

    def test_buffer_add(self, buffer):
        """Test adding data to buffer."""
        obs = np.random.randn(15)
        action = np.random.randn(2)
        reward = 1.0
        value = 0.5
        log_prob = -0.1
        done = False

        buffer.add(obs, action, reward, value, log_prob, done)

        assert buffer.ptr == 1

    def test_buffer_compute_advantages(self, buffer):
        """Test GAE computation."""
        for i in range(100):
            obs = np.random.randn(15)
            action = np.random.randn(2)
            reward = float(i)
            value = float(i) * 0.1
            log_prob = -0.1
            done = False
            buffer.add(obs, action, reward, value, log_prob, done)

        buffer.compute_advantages(final_value=10.0)

        assert buffer.advantages is not None
        assert buffer.returns is not None

    def test_buffer_get(self, buffer):
        """Test retrieving data from buffer."""
        for i in range(100):
            obs = np.random.randn(15)
            action = np.random.randn(2)
            reward = float(i)
            value = float(i) * 0.1
            log_prob = -0.1
            done = False
            buffer.add(obs, action, reward, value, log_prob, done)

        buffer.compute_advantages(final_value=10.0)

        (
            observations,
            actions,
            advantages,
            returns,
            old_log_probs,
            _,
        ) = buffer.get()

        assert observations.shape == (100, 15)
        assert actions.shape == (100, 2)
        assert advantages.shape == (100,)
        assert returns.shape == (100,)


class TestPPOTrainer:
    """Tests for PPOTrainer."""

    @pytest.fixture
    def trainer(self):
        """Create PPOTrainer instance."""
        model = ACMPCModel(
            obs_dim=15,
            n_states=3,
            horizon=10,
            cost_map_hidden_layers=[32, 32],
            value_hidden_layers=[32, 32],
        )

        ppo_config = PPOConfig(
            n_steps=50,
            n_epochs=2,
            learning_rate=1e-3,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            exploration_max_std=0.1,
            exploration_epochs=10,
        )

        env_config = EnvConfig(
            world_name="turtlebot3_empty",
            robot_name="burger",
            reward_fn="dense_goal",
        )

        trainer = PPOTrainer(
            model=model,
            ppo_config=ppo_config,
            acmpc_config=ACMPCConfig(),
            env_config=env_config,
            case=None,
            device="cpu",
        )

        return trainer

    def test_sample_action_deterministic(self, trainer):
        """Test deterministic action sampling."""
        obs = torch.randn(1, 15)

        action, log_prob, value = trainer.sample_action(obs, deterministic=True)

        assert action.shape == (1, 2)
        assert log_prob.shape == (1,)
        assert value.shape == (1,)

    def test_sample_action_with_exploration(self, trainer):
        """Test action sampling with exploration."""
        obs = torch.randn(1, 15)

        action, log_prob, value = trainer.sample_action(obs, deterministic=False)

        assert action.shape == (1, 2)
        assert log_prob.shape == (1,)
        assert value.shape == (1,)

    def test_collect_rollouts(self, trainer):
        """Test collecting rollouts with mock environment."""
        env = MockEnv()
        metrics = trainer.collect_rollouts(env)

        assert "rollout_reward" in metrics
        assert "rollout_steps" in metrics
        assert metrics["rollout_steps"] == 50

    def test_train_step(self, trainer):
        """Test PPO training step."""
        env = MockEnv()

        trainer.collect_rollouts(env)

        metrics = trainer.train_step()

        assert "policy_loss" in metrics
        assert "value_loss" in metrics

    def test_full_training_loop(self, trainer):
        """Test full training loop with multiple steps."""
        env = MockEnv()

        for _ in range(3):
            trainer.collect_rollouts(env)
            metrics = trainer.train_step()

        assert trainer.global_step > 0
        assert trainer.epoch > 0

    def test_gradient_accumulation(self, trainer):
        """Test that gradients accumulate correctly."""
        model = trainer.model
        model.train()

        obs = torch.randn(1, 15, requires_grad=True)
        action, value = model(obs)

        loss = value.mean()
        trainer.actor_optimizer.zero_grad()
        trainer.critic_optimizer.zero_grad()
        loss.backward()

        grad_norms = []
        for param in model.parameters():
            if param.grad is not None:
                grad_norms.append(param.grad.norm().item())

        assert len(grad_norms) > 0


class TestPPOIntegration:
    """Integration tests for PPO with AC-MPC."""

    def test_ppo_with_mock_env(self):
        """Test PPO training loop with mock environment."""
        model = ACMPCModel(
            obs_dim=15,
            n_states=3,
            horizon=10,
            cost_map_hidden_layers=[32, 32],
            value_hidden_layers=[32, 32],
        )

        ppo_config = PPOConfig(
            n_steps=100,
            n_epochs=2,
            learning_rate=1e-3,
        )

        env_config = EnvConfig(
            world_name="turtlebot3_empty",
            robot_name="burger",
            reward_fn="dense_goal",
        )

        trainer = PPOTrainer(
            model=model,
            ppo_config=ppo_config,
            acmpc_config=ACMPCConfig(),
            env_config=env_config,
            case=None,
            device="cpu",
        )

        env = MockEnv()

        for _ in range(2):
            trainer.collect_rollouts(env)
            metrics = trainer.train_step()

        assert trainer.global_step == 200
