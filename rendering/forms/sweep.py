"""Shared tube-sweep engine.

Powers BOTH:
  - DTI tracts  (sweep a thin tube along each streamline, color by direction)
  - tentacles   (sweep a tapered tube along a curled centerline)  [later]

A pin is the degenerate case (straight, 1 segment) handled in quills.py.

Uses a rotation-minimizing (parallel-transport) frame so tubes don't twist on
bends — essential for tracts, which curve constantly.
"""
from __future__ import annotations

import numpy as np


def _tangents(P: np.ndarray) -> np.ndarray:
    T = np.empty_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    n = np.linalg.norm(T, axis=1, keepdims=True)
    return T / (n + 1e-12)


def _pt_frames(P: np.ndarray):
    """Parallel-transport normal/binormal frames along centerline P."""
    T = _tangents(P)
    n = len(P)
    N = np.empty((n, 3))
    B = np.empty((n, 3))
    up = np.array([0.0, 0.0, 1.0])
    if abs(T[0] @ up) > 0.99:
        up = np.array([1.0, 0.0, 0.0])
    N[0] = np.cross(T[0], up)
    N[0] /= np.linalg.norm(N[0]) + 1e-12
    B[0] = np.cross(T[0], N[0])
    for i in range(1, n):
        v = N[i - 1] - T[i] * (N[i - 1] @ T[i])   # project previous normal
        ln = np.linalg.norm(v)
        if ln < 1e-9:
            v = B[i - 1] - T[i] * (B[i - 1] @ T[i])
            ln = np.linalg.norm(v) + 1e-12
        N[i] = v / ln
        B[i] = np.cross(T[i], N[i])
    return T, N, B


def sweep_tube(P: np.ndarray, radius, sides: int = 5):
    """Sweep a tube of given radius(es) along polyline P (M,3).

    radius: scalar or per-point array (M,). Returns (verts, faces, dir_rgb)
    where dir_rgb is the per-vertex direction color (|tangent|), ready to use
    as a vertex-color attribute.
    """
    P = np.asarray(P, dtype=float)
    M = len(P)
    if M < 2:
        return None
    radii = np.full(M, radius) if np.isscalar(radius) else np.asarray(radius)
    T, N, B = _pt_frames(P)

    theta = 2 * np.pi * np.arange(sides) / sides
    cs, sn = np.cos(theta), np.sin(theta)
    # ring i: P[i] + r[i]*(cos*N[i] + sin*B[i])
    ring = (P[:, None, :]
            + radii[:, None, None] * (cs[None, :, None] * N[:, None, :]
                                      + sn[None, :, None] * B[:, None, :]))
    verts = ring.reshape(-1, 3)

    # direction color per point, broadcast to its ring
    dir_rgb = np.abs(T)                      # |tangent| -> RGB (DTI convention)
    dir_rgb = np.repeat(dir_rgb, sides, axis=0)

    faces = []
    for i in range(M - 1):
        a, b = i * sides, (i + 1) * sides
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append([a + j, a + j2, b + j2])
            faces.append([a + j, b + j2, b + j])
    return verts, np.array(faces, dtype=np.int64), dir_rgb
