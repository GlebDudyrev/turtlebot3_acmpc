"""TurtleBot3 Dynamics - Unicycle model."""

from __future__ import annotations

import torch
from torch import Tensor


class TurtleBot3Dynamics:
    """Unicycle dynamics for TurtleBot3.

    State: x = [x, y, theta] (position + orientation)
    Control: u = [v, omega] (linear velocity, angular velocity)

    Discrete dynamics (Euler integration):
        x_{k+1} = x_k + v_k * cos(theta_k) * dt
        y_{k+1} = y_k + v_k * sin(theta_k) * dt
        theta_{k+1} = theta_k + omega_k * dt
    """

    N_STATES = 3  # x, y, theta
    N_CONTROLS = 2  # v, omega

    def __init__(self, dt: float = 0.1):
        """Initialize dynamics.

        Args:
            dt: Time step in seconds
        """
        self.dt = dt

    def forward(self, states: Tensor, controls: Tensor) -> Tensor:
        """Compute next state given current state and control.

        Args:
            states: Current state [batch, n_states] or [n_states]
            controls: Control input [batch, n_controls] or [n_controls]

        Returns:
            next_states: Next state [batch, n_states] or [n_states]
        """
        if states.dim() == 1:
            states = states.unsqueeze(0)
            controls = controls.unsqueeze(0)
            squeeze_output = True
        else:
            squeeze_output = False

        x = states[:, 0]
        y = states[:, 1]
        theta = states[:, 2]

        v = controls[:, 0]
        omega = controls[:, 1]

        dt = self.dt

        x_next = x + v * torch.cos(theta) * dt
        y_next = y + v * torch.sin(theta) * dt
        theta_next = theta + omega * dt

        # Wrap theta to [-pi, pi]
        theta_next = torch.atan2(torch.sin(theta_next), torch.cos(theta_next))

        next_states = torch.stack([x_next, y_next, theta_next], dim=1)

        if squeeze_output:
            next_states = next_states.squeeze(0)

        return next_states

    def linearize(
        self, states: Tensor, controls: Tensor | None = None
    ) -> tuple[Tensor, Tensor]:
        """Linearize dynamics around operating point.

        Returns A and B matrices for discrete-time linear system:
            x_{k+1} = A * x_k + B * u_k

        Linearization at point (x, u):
            f(x, u) ≈ f(x0, u0) + A*(x-x0) + B*(u-u0)

        Here we linearize at the operating point itself.

        Args:
            states: Operating point state [batch, n_states] or [n_states]
            controls: Operating point control [batch, n_controls] or [n_controls]
                      If None, uses zero control

        Returns:
            A: State transition matrix [batch, n_states, n_states]
            B: Control input matrix [batch, n_states, n_controls]
        """
        if states.dim() == 1:
            states = states.unsqueeze(0)
            squeeze = True
        else:
            squeeze = False

        if controls is None:
            controls = torch.zeros_like(states[:, : self.N_CONTROLS])

        batch_size = states.shape[0]
        dt = self.dt

        theta = states[:, 2]
        v = controls[:, 0]

        cos_theta = torch.cos(theta)
        sin_theta = torch.sin(theta)

        # A matrix: partial derivatives of f(x, u) with respect to x
        # [[1, 0, -v*sin(theta)*dt],
        #  [0, 1,  v*cos(theta)*dt],
        #  [0, 0,              1]]
        A = torch.zeros(batch_size, self.N_STATES, self.N_STATES)
        A[:, 0, 0] = 1.0
        A[:, 0, 2] = -v * sin_theta * dt
        A[:, 1, 1] = 1.0
        A[:, 1, 2] = v * cos_theta * dt
        A[:, 2, 2] = 1.0

        # B matrix: partial derivatives of f(x, u) with respect to u
        # [[cos(theta)*dt, 0],
        #  [sin(theta)*dt, 0],
        #  [0,             dt]]
        B = torch.zeros(batch_size, self.N_STATES, self.N_CONTROLS)
        B[:, 0, 0] = cos_theta * dt
        B[:, 1, 0] = sin_theta * dt
        B[:, 2, 1] = dt

        if squeeze:
            A = A.squeeze(0)
            B = B.squeeze(0)

        return A, B

    def predict_trajectory(self, x0: Tensor, u_seq: Tensor) -> Tensor:
        """Predict trajectory over horizon.

        Args:
            x0: Initial state [batch, n_states] or [n_states]
            u_seq: Control sequence [batch, horizon, n_controls]

        Returns:
            trajectory: [batch, horizon+1, n_states]
        """
        if x0.dim() == 1:
            x0 = x0.unsqueeze(0)
            squeeze = True
        else:
            squeeze = False

        if u_seq.dim() == 2:
            u_seq = u_seq.unsqueeze(0)

        batch_size = x0.shape[0]
        horizon = u_seq.shape[1]

        trajectory = torch.zeros(batch_size, horizon + 1, self.N_STATES)
        trajectory[:, 0] = x0

        current_state = x0
        for t in range(horizon):
            current_state = self.forward(current_state, u_seq[:, t])
            trajectory[:, t + 1] = current_state

        if squeeze:
            trajectory = trajectory.squeeze(0)

        return trajectory
