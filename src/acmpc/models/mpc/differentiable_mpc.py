"""Differentiable MPC using torch.linalg.solve - fully differentiable."""

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor

from .dynamics import TurtleBot3Dynamics
from .qp_builder import build_prediction_matrices, build_qp_matrices


class DifferentiableMPC(nn.Module):
    """Fully differentiable MPC using PyTorch's linalg.solve.

    Uses torch.linalg.solve which supports autograd:
        H @ u = -f  →  u = -H^{-1} @ f

    This is fully differentiable through PyTorch's backward pass.
    """

    N_STATES = 3
    N_CONTROLS = 2

    def __init__(
        self,
        horizon: int = 15,
        dt: float = 0.1,
        control_bounds: tuple[float, float] = (-0.22, 0.22),
    ):
        super().__init__()

        self.horizon = horizon
        self.dt = dt
        self.control_bounds = control_bounds

        self.dynamics = TurtleBot3Dynamics(dt=dt)

        self.register_buffer(
            "R_diag_default",
            torch.ones(horizon, self.N_CONTROLS) * 1.0,
        )

    def forward(
        self,
        x0: Tensor,
        Q_diag: Tensor,
        p: Tensor,
        R_diag: Tensor | None = None,
    ) -> Tensor:
        """Forward pass - fully differentiable.

        Args:
            x0: Initial state [batch, n_states] or [n_states]
            Q_diag: State cost [batch, horizon+1, n_states]
            p: Linear cost [batch, horizon+1, n_states]
            R_diag: Control cost [batch, horizon, n_controls]

        Returns:
            action: [batch, n_controls]
        """
        squeeze = False
        if x0.dim() == 1:
            x0 = x0.unsqueeze(0)
            Q_diag = Q_diag.unsqueeze(0)
            p = p.unsqueeze(0)
            squeeze = True

        if R_diag is None:
            R_diag = self.R_diag_default.unsqueeze(0).expand(x0.shape[0], -1, -1)

        batch_size = x0.shape[0]
        n_vars = self.horizon * self.N_CONTROLS

        # Linearize dynamics
        u_zero = torch.zeros(batch_size, self.N_CONTROLS, device=x0.device)
        A, B = self.dynamics.linearize(x0, u_zero)

        # Build QP matrices
        F, M = build_prediction_matrices(A, B, self.horizon)
        H, f = build_qp_matrices(F, M, Q_diag, p, R_diag, x0)

        # Add regularization for positive definiteness
        H = H + torch.eye(H.shape[1], device=H.device) * 1e-3

        # Solve QP using torch.linalg.solve: H @ u = -f
        # This is fully differentiable!
        f_neg = -f

        # Add small identity for numerical stability in solve
        H_reg = H + torch.eye(H.shape[1], device=H.device) * 1e-6

        # Solve for each sample in batch
        actions = []
        for b in range(batch_size):
            try:
                # Solve H @ u = f_neg
                u = torch.linalg.solve(H_reg[b], f_neg[b])
            except RuntimeError:
                # Fallback: use pseudo-inverse
                u = torch.linalg.lstsq(H_reg[b], f_neg[b]).solution

            action = u[: self.N_CONTROLS]
            actions.append(action)

        actions = torch.stack(actions, dim=0)

        # Apply control bounds (soft, differentiable)
        u_min = self.control_bounds[0]
        u_max = self.control_bounds[1]

        # Use soft clamping for differentiability
        actions = torch.tanh(actions) * ((u_max - u_min) / 2) + (u_max + u_min) / 2

        if squeeze:
            actions = actions.squeeze(0)

        return actions

    def get_config(self) -> dict:
        return {
            "horizon": self.horizon,
            "dt": self.dt,
            "control_bounds": self.control_bounds,
            "n_states": self.N_STATES,
            "n_controls": self.N_CONTROLS,
        }
