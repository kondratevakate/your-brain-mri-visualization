"""DTI tract layer: load streamlines, subsample, decimate, sweep to tubes.

Real tractography files (.trk/.tck) hold 10k-1M streamlines — far too many to
sweep directly. We random-subsample to a renderable count and Ramer-Douglas-
Peucker-decimate each line before sweeping. Output is one trimesh.Trimesh with
a per-vertex direction color carried in `visual.vertex_colors`, so it drops into
scene.py as an emission Layer that reads color from geometry.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from rendering.forms.sweep import sweep_tube


def load_streamlines(path: str | Path):
    """Load .trk/.tck via nibabel. Returns list of (Ni,3) arrays in mm (RASMM)."""
    import nibabel as nib
    tractogram = nib.streamlines.load(str(path))
    return [np.asarray(s) for s in tractogram.streamlines]


def _rdp_decimate(P: np.ndarray, eps: float) -> np.ndarray:
    """Iterative Ramer-Douglas-Peucker: drop points within eps of the chord."""
    if len(P) < 3:
        return P
    keep = np.zeros(len(P), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(P) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        seg = P[j] - P[i]
        L = np.linalg.norm(seg) + 1e-12
        d = np.linalg.norm(np.cross(P[i + 1:j] - P[i], seg), axis=1) / L
        k = int(np.argmax(d))
        if d[k] > eps:
            keep[i + 1 + k] = True
            stack.append((i, i + 1 + k))
            stack.append((i + 1 + k, j))
    return P[keep]


def tract_tubes(
    streamlines,
    *,
    max_lines: int = 4000,
    radius: float = 0.4,
    sides: int = 5,
    decimate_eps: float = 0.6,
    min_points: int = 4,
    seed: int = 0,
) -> trimesh.Trimesh:
    """Subsample + decimate + sweep streamlines into one direction-colored mesh."""
    rng = np.random.default_rng(seed)
    if len(streamlines) > max_lines:
        idx = rng.choice(len(streamlines), max_lines, replace=False)
        streamlines = [streamlines[i] for i in idx]

    Vs, Fs, Cs = [], [], []
    off = 0
    for s in streamlines:
        s = _rdp_decimate(np.asarray(s, dtype=float), decimate_eps)
        if len(s) < min_points:
            continue
        res = sweep_tube(s, radius, sides=sides)
        if res is None:
            continue
        v, f, rgb = res
        Vs.append(v)
        Fs.append(f + off)
        Cs.append(rgb)
        off += len(v)

    if not Vs:
        raise ValueError("no streamlines survived decimation")

    V = np.vstack(Vs)
    F = np.vstack(Fs)
    C = np.vstack(Cs)
    rgba = np.hstack([(C * 255).astype(np.uint8),
                      np.full((len(C), 1), 255, np.uint8)])
    mesh = trimesh.Trimesh(vertices=V, faces=F, process=False)
    mesh.visual.vertex_colors = rgba
    return mesh
