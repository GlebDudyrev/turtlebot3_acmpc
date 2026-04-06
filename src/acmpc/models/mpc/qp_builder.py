"""QP Builder - builds H, f matrices for MPC."""

from __future__ import annotations

import torch
from torch import Tensor


def build_prediction_matrices(
    A: Tensor,
    B: Tensor,
    horizon: int,
) -> tuple[Tensor, Tensor]:
    """Build F and M matrices for trajectory prediction.

    Single-shooting: X = F @ x0 + M @ U
    where X is the trajectory and U is the control sequence.

    Args:
        A: State transition matrix [batch, n_states, n_states]
        B: Control matrix [batch, n_states, n_controls]
        horizon: MPC horizon

    Returns:
        F: [batch, (horizon+1)*n_states, n_states] - free response
        M: [batch, (horizon+1)*n_states, horizon*n_controls] - forced response
    """
    n_states = A.shape[1]
    n_controls = B.shape[2]
    batch_size = A.shape[0]

    # F matrix: state evolution without control input
    # Shape: [batch, (horizon+1)*n_states, n_states]
    F = torch.zeros(batch_size, (horizon + 1) * n_states, n_states)
    for i in range(horizon + 1):
        A_power = torch.linalg.matrix_power(A, i)
        start = i * n_states
        end = (i + 1) * n_states
        F[:, start:end, :] = A_power

    # M matrix: control effect on trajectory
    # x_k = A^k x0 + sum(A^{k-j-1} B u_j)
    M = torch.zeros(batch_size, (horizon + 1) * n_states, horizon * n_controls)

    for k in range(1, horizon + 1):  # for each timestep
        for j in range(k):  # for each control up to k
            # A^{k-j-1} B effect from control u_j
            if k - j - 1 >= 0:
                A_power = torch.linalg.matrix_power(A, k - j - 1)
                AB = A_power @ B  # [batch, n_states, n_controls]

                M_start = k * n_states
                M_end = (k + 1) * n_states
                U_start = j * n_controls
                U_end = (j + 1) * n_controls

                M[:, M_start:M_end, U_start:U_end] = AB

    return F, M


def build_qp_matrices(
    F: Tensor,
    M: Tensor,
    Q_diag: Tensor,
    p: Tensor,
    R_diag: Tensor,
    x0: Tensor,
) -> tuple[Tensor, Tensor]:
    """Build QP matrices H and f from cost parameters.

    MPC cost: J = X^T Q X + U^T R U + p^T X
    where X = F @ x0 + M @ U

    Expanding:
    J = (F @ x0 + M @ U)^T Q (F @ x0 + M @ U) + U^T R U + p^T (F @ x0 + M @ U)
      = U^T (M^T Q M + R) U + 2 * (x0^T F^T Q M + p^T M) U + const

    So:
    H = M^T Q M + R
    f = 2 * M^T Q F x0 + 2 * M^T p

    Args:
        F: [batch, (horizon+1)*n_states, n_states]
        M: [batch, (horizon+1)*n_states, horizon*n_controls]
        Q_diag: [batch, horizon+1, n_states]
        p: [batch, horizon+1, n_states]
        R_diag: [batch, horizon, n_controls]
        x0: [batch, n_states]

    Returns:
        H: [batch, horizon*n_controls, horizon*n_controls]
        f: [batch, horizon*n_controls]
    """
    batch_size = F.shape[0]
    horizon = R_diag.shape[1]
    n_states = Q_diag.shape[2]
    n_controls = R_diag.shape[2]
    n_vars = horizon * n_controls
    traj_len = (horizon + 1) * n_states

    Q_diag_flat = Q_diag.view(batch_size, -1)
    Q = torch.diag_embed(Q_diag_flat)

    R_diag_flat = R_diag.view(batch_size, -1)
    R = torch.diag_embed(R_diag_flat)

    M_view = M.view(batch_size, traj_len, n_vars)
    H = torch.bmm(M_view.transpose(1, 2), torch.bmm(Q, M_view)) + R

    p_flat = p.view(batch_size, -1)
    Fx0 = torch.bmm(F, x0.unsqueeze(2)).squeeze(2)
    Q_Fx0 = torch.bmm(Fx0.unsqueeze(1), Q).squeeze(1)
    term1 = 2 * torch.bmm(M_view.transpose(1, 2), Q_Fx0.unsqueeze(2)).squeeze(2)
    term2 = 2 * torch.bmm(M_view.transpose(1, 2), p_flat.unsqueeze(2)).squeeze(2)
    f = term1 + term2

    return H, f


def build_qp_matrices_single(
    F: Tensor,
    M: Tensor,
    Q_diag: Tensor,
    p: Tensor,
    R_diag: Tensor,
    x0: Tensor,
) -> tuple[Tensor, Tensor]:
    """Build QP matrices for single sample (no batch).

    Args:
        F: [(horizon+1)*n_states, n_states]
        M: [(horizon+1)*n_states, horizon*n_controls]
        Q_diag: [horizon+1, n_states]
        p: [horizon+1, n_states]
        R_diag: [horizon, n_controls]
        x0: [n_states]

    Returns:
        H: [horizon*n_controls, horizon*n_controls]
        f: [horizon*n_controls]
    """
    horizon = R_diag.shape[0]
    n_states = Q_diag.shape[1]
    n_controls = R_diag.shape[1]
    n_vars = horizon * n_controls

    # Build Q matrix
    Q_diag_flat = Q_diag.view(-1)  # [(horizon+1)*n_states]
    Q = torch.diag(Q_diag_flat)

    # Build R matrix
    R_diag_flat = R_diag.view(-1)  # [horizon*n_controls]
    R = torch.diag(R_diag_flat)

    # H = M^T Q M + R
    H = M.T @ Q @ M + R

    # f = 2 * M^T Q F x0 + 2 * M^T p
    p_flat = p.view(-1)  # [(horizon+1)*n_states]
    f = 2 * M.T @ Q @ F @ x0 + 2 * M.T @ p_flat

    return H, f
