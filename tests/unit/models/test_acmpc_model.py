"""Unit tests for AC-MPC models."""

from __future__ import annotations

import torch
import pytest
from torch import Tensor

from acmpc.models import ACMPCModel
from acmpc.models.cost import NeuralCostMap
from acmpc.models.mpc import DifferentiableMPC
from acmpc.models.networks import ValueNetwork


class TestDifferentiableMPC:
    """Tests for DifferentiableMPC."""

    @pytest.fixture
    def mpc(self):
        """Create DifferentiableMPC instance."""
        return DifferentiableMPC(horizon=10, dt=0.1)

    def test_mpc_forward_single_sample(self, mpc):
        """Test forward pass with single sample."""
        batch_size = 1
        x0 = torch.zeros(3)
        Q_diag = torch.ones(11, 3)
        p = torch.zeros(11, 3)

        action = mpc(x0, Q_diag, p)

        assert action.shape == (2,)
        assert torch.allclose(action.abs(), action.abs(), atol=1.0)

    def test_mpc_forward_batch(self, mpc):
        """Test forward pass with batch."""
        batch_size = 4
        x0 = torch.zeros(batch_size, 3)
        Q_diag = torch.ones(batch_size, 11, 3)
        p = torch.zeros(batch_size, 11, 3)

        action = mpc(x0, Q_diag, p)

        assert action.shape == (batch_size, 2)

    def test_mpc_output_bounds(self, mpc):
        """Test that output is within control bounds."""
        x0 = torch.zeros(3)
        Q_diag = torch.ones(11, 3) * 10.0
        p = torch.zeros(11, 3)

        action = mpc(x0, Q_diag, p)

        assert action[0] >= -0.22
        assert action[0] <= 0.22
        assert action[1] >= -0.22
        assert action[1] <= 0.22


class TestNeuralCostMap:
    """Tests for NeuralCostMap."""

    @pytest.fixture
    def cost_map(self):
        """Create NeuralCostMap instance."""
        return NeuralCostMap(obs_dim=15, n_states=3, horizon=10)

    def test_cost_map_forward(self, cost_map):
        """Test forward pass."""
        obs = torch.randn(1, 15)
        Q_diag, p = cost_map(obs)

        assert Q_diag.shape == (1, 11, 3)
        assert p.shape == (1, 11, 3)

    def test_cost_map_positive_costs(self, cost_map):
        """Test that cost outputs are positive."""
        obs = torch.randn(4, 15)
        Q_diag, p = cost_map(obs)

        assert torch.all(Q_diag > 0)


class TestValueNetwork:
    """Tests for ValueNetwork."""

    @pytest.fixture
    def value_net(self):
        """Create ValueNetwork instance."""
        return ValueNetwork(obs_dim=15)

    def test_value_network_forward(self, value_net):
        """Test forward pass."""
        obs = torch.randn(1, 15)
        value = value_net(obs)

        assert value.shape == (1, 1)

    def test_value_network_batch(self, value_net):
        """Test forward pass with batch."""
        obs = torch.randn(4, 15)
        value = value_net(obs)

        assert value.shape == (4, 1)


class TestACMPCModel:
    """Tests for ACMPCModel."""

    @pytest.fixture
    def model(self):
        """Create ACMPCModel instance."""
        return ACMPCModel(
            obs_dim=15,
            n_states=3,
            horizon=10,
            cost_map_hidden_layers=[64, 64],
            value_hidden_layers=[64, 64],
        )

    def test_acmpc_forward(self, model):
        """Test forward pass returns action and value."""
        obs = torch.randn(1, 15)
        action, value = model(obs)

        assert action.shape == (1, 2)
        assert value.shape == (1, 1)

    def test_acmpc_forward_batch(self, model):
        """Test forward pass with batch."""
        batch_size = 4
        obs = torch.randn(batch_size, 15)
        action, value = model(obs)

        assert action.shape == (batch_size, 2)
        assert value.shape == (batch_size, 1)

    def test_acmpc_action_bounds(self, model):
        """Test that action is within bounds."""
        obs = torch.randn(1, 15)
        action, _ = model(obs)

        assert action[0, 0].item() >= -0.22
        assert action[0, 0].item() <= 0.22
        assert action[0, 1].item() >= -0.22
        assert action[0, 1].item() <= 0.22


class TestACMPCModelGradients:
    """Tests for gradient flow through ACMPCModel."""

    @pytest.fixture
    def model(self):
        """Create ACMPCModel instance."""
        model = ACMPCModel(
            obs_dim=15,
            n_states=3,
            horizon=10,
            cost_map_hidden_layers=[32, 32],
            value_hidden_layers=[32, 32],
        )
        model.train()
        return model

    def test_backward_pass(self, model):
        """Test that backward pass works without errors."""
        obs = torch.randn(1, 15, requires_grad=True)
        action, value = model(obs)

        value_sum = value.sum()
        value_sum.backward()

        assert obs.grad is not None

    def test_gradients_flow_to_cost_map(self, model):
        """Test that gradients flow to NeuralCostMap parameters."""
        obs = torch.randn(1, 15, requires_grad=True)
        action, value = model(obs)

        action_sum = action.sum()
        action_sum.backward()

        cost_map_grads = []
        for param in model.cost_map.parameters():
            if param.grad is not None:
                cost_map_grads.append(param.grad)

        assert len(cost_map_grads) > 0, "No gradients flowed to cost_map"

    def test_gradients_flow_to_value_network(self, model):
        """Test that gradients flow to ValueNetwork parameters."""
        obs = torch.randn(1, 15, requires_grad=True)
        action, value = model(obs)

        value_sum = value.sum()
        value_sum.backward()

        value_net_grads = []
        for param in model.value_network.parameters():
            if param.grad is not None:
                value_net_grads.append(param.grad)

        assert len(value_net_grads) > 0, "No gradients flowed to value_network"

    def test_full_training_step(self, model):
        """Test full training step with optimizer."""
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        obs = torch.randn(4, 15, requires_grad=True)
        action, value = model(obs)

        loss = -value.mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        assert True
