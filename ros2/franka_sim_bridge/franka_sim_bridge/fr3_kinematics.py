"""FR3 名义运动学 + 差分 IK（DLS）。

参数对齐 Franka Research 3 / franka_description 常用 MDH 数值；
求解方法对齐 Isaac Lab ``DifferentialIKController`` 的 ``ik_method=dls``，
以及 franka_ros2 ``joint_impedance_with_ik_example_controller`` 所用的数值 IK 族
（官方真机路径用 MoveIt LMA；CTRL-SIM 侧用同族 DLS，避免在桥进程内拉起 MoveIt）。

TCP 偏移默认 ``t_flange_tcp=(0,0,0.103)``，见 ``FR3_Scene_v0_场景规格.md``。
实测后应以 pin / Scene 补丁覆盖。
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

# Modified DH: (a, alpha, d) per joint i (theta = q_i)
# Values commonly used for Franka Panda/FR3-class 7-DoF (franka_description lineage).
_MDH = np.array(
    [
        [0.0, 0.0, 0.333],
        [0.0, -np.pi / 2, 0.0],
        [0.0, np.pi / 2, 0.316],
        [0.0825, np.pi / 2, 0.0],
        [-0.0825, -np.pi / 2, 0.384],
        [0.0, np.pi / 2, 0.0],
        [0.088, np.pi / 2, 0.0],
    ],
    dtype=np.float64,
)
_FLANGE_Z = 0.107
_DEFAULT_TCP = np.array([0.0, 0.0, 0.103], dtype=np.float64)

# Scene v0 名义 Home（rad）
Q_HOME = np.array(
    [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785], dtype=np.float64
)


def _mdh_T(a: float, alpha: float, d: float, theta: float) -> np.ndarray:
    ca, sa = np.cos(alpha), np.sin(alpha)
    ct, st = np.cos(theta), np.sin(theta)
    return np.array(
        [
            [ct, -st, 0.0, a],
            [st * ca, ct * ca, -sa, -sa * d],
            [st * sa, ct * sa, ca, ca * d],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def fk_flange(q: np.ndarray) -> np.ndarray:
    """基座 → 法兰 4x4。"""
    T = np.eye(4, dtype=np.float64)
    for i in range(7):
        a, alpha, d = _MDH[i]
        T = T @ _mdh_T(float(a), float(alpha), float(d), float(q[i]))
    T_flange = np.eye(4, dtype=np.float64)
    T_flange[2, 3] = _FLANGE_Z
    return T @ T_flange


def fk_tcp(q: np.ndarray, t_flange_tcp: np.ndarray | None = None) -> np.ndarray:
    """基座 → TCP 4x4。"""
    tcp = _DEFAULT_TCP if t_flange_tcp is None else np.asarray(t_flange_tcp, dtype=np.float64)
    T = fk_flange(q)
    T_tcp = np.eye(4, dtype=np.float64)
    T_tcp[:3, 3] = tcp
    return T @ T_tcp


def rot_to_quat_xyzw(R: np.ndarray) -> np.ndarray:
    """旋转矩阵 → quat (x,y,z,w)。"""
    m00, m01, m02 = R[0, 0], R[0, 1], R[0, 2]
    m10, m11, m12 = R[1, 0], R[1, 1], R[1, 2]
    m20, m21, m22 = R[2, 0], R[2, 1], R[2, 2]
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = 0.5 / np.sqrt(tr + 1.0)
        w = 0.25 / s
        x = (m21 - m12) * s
        y = (m02 - m20) * s
        z = (m10 - m01) * s
    elif m00 > m11 and m00 > m22:
        s = 2.0 * np.sqrt(1.0 + m00 - m11 - m22)
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = 2.0 * np.sqrt(1.0 + m11 - m00 - m22)
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = 2.0 * np.sqrt(1.0 + m22 - m00 - m11)
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    q = np.array([x, y, z, w], dtype=np.float64)
    n = np.linalg.norm(q)
    return q / n if n > 0 else np.array([0.0, 0.0, 0.0, 1.0])


def pose7_from_T(T: np.ndarray) -> np.ndarray:
    """xyz + quat(xyzw)。"""
    return np.concatenate([T[:3, 3], rot_to_quat_xyzw(T[:3, :3])])


def _skew(w: np.ndarray) -> np.ndarray:
    return np.array(
        [[0.0, -w[2], w[1]], [w[2], 0.0, -w[0]], [-w[1], w[0], 0.0]],
        dtype=np.float64,
    )


def numerical_jacobian(q: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """6x7 几何雅可比（位置+姿态，有限差分）。"""
    T0 = fk_tcp(q)
    p0 = T0[:3, 3]
    R0 = T0[:3, :3]
    J = np.zeros((6, 7), dtype=np.float64)
    for i in range(7):
        dq = np.zeros(7, dtype=np.float64)
        dq[i] = eps
        T1 = fk_tcp(q + dq)
        p1 = T1[:3, 3]
        R1 = T1[:3, :3]
        J[:3, i] = (p1 - p0) / eps
        dR = R1 @ R0.T
        # vee( (dR - I)/eps ) approx for small rotation
        w_hat = (dR - np.eye(3)) / eps
        J[3, i] = w_hat[2, 1]
        J[4, i] = w_hat[0, 2]
        J[5, i] = w_hat[1, 0]
    return J


def apply_ee_delta(
    q: np.ndarray,
    ee_delta6: np.ndarray,
    *,
    damping: float = 0.05,
    max_dq: float = 0.2,
) -> Tuple[np.ndarray, str, np.ndarray]:
    """相对 Δpose → 新关节角（单步 DLS）。

    Returns:
        q_des, ik_status ('ok'|'limited'|'failed'), ee_pose_desired(7)
    """
    q = np.asarray(q, dtype=np.float64).reshape(7)
    delta = np.asarray(ee_delta6, dtype=np.float64).reshape(6)
    T = fk_tcp(q)
    p = T[:3, 3].copy()
    R = T[:3, :3].copy()
    p_des = p + delta[:3]
    # 小角度旋转：R_des ≈ R @ Exp([droll,dpitch,dyaw])
    wr = delta[3:6]
    R_des = R @ (np.eye(3) + _skew(wr))
    # 正交化
    u, _, vt = np.linalg.svd(R_des)
    R_des = u @ vt
    if np.linalg.det(R_des) < 0:
        u[:, -1] *= -1
        R_des = u @ vt

    T_des = np.eye(4, dtype=np.float64)
    T_des[:3, :3] = R_des
    T_des[:3, 3] = p_des
    pose_des = pose7_from_T(T_des)

    J = numerical_jacobian(q)
    # task error: position + rotation (vee of R_err)
    R_err = R_des @ R.T
    rot_err = np.array(
        [R_err[2, 1] - R_err[1, 2], R_err[0, 2] - R_err[2, 0], R_err[1, 0] - R_err[0, 1]],
        dtype=np.float64,
    ) * 0.5
    err = np.concatenate([p_des - p, rot_err])

    JJT = J @ J.T
    try:
        dq = J.T @ np.linalg.solve(JJT + (damping**2) * np.eye(6), err)
    except np.linalg.LinAlgError:
        return q.copy(), "failed", pose_des

    status = "ok"
    n = np.linalg.norm(dq)
    if n > max_dq:
        dq = dq * (max_dq / n)
        status = "limited"
    return q + dq, status, pose_des
