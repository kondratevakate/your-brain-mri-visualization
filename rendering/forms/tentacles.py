"""Curled tentacle field (sea-anemone look) — the protrusion layer's organic
sibling of straight pins. Built on the shared sweep engine.

Features matching a real anemone:
  - tentacles grow UPWARD (direction blends toward +Z as they extend)
  - size scales with base height (taller near the crown, short near the base)
  - per-tentacle curl direction + jitter => varied, lifelike bends
  - clubbed (bulbous) tips, like the pale tips in the reference
  - per-vertex parameter t (0 base -> 1 tip) for SSS tip glow
"""
from __future__ import annotations

import numpy as np
import trimesh

from rendering.forms.sweep import sweep_tube
from rendering.forms.quills import sample_seeds


def _grow_centerline(p0, d0, length, segments, up_bias, curl_dir, curl,
                     jitter, rng):
    UP = np.array([0.0, 0.0, 1.0])
    d0 = d0 / (np.linalg.norm(d0) + 1e-12)
    pts = [p0.copy()]
    p, d = p0.copy(), d0.copy()
    step = length / segments
    for k in range(1, segments + 1):
        frac = k / segments
        target = (1 - up_bias) * d0 + up_bias * UP + curl * curl_dir * frac
        target /= np.linalg.norm(target) + 1e-12
        d = d + (target - d) * 0.5 + (rng.random(3) - 0.5) * jitter
        d /= np.linalg.norm(d) + 1e-12
        p = p + d * step
        pts.append(p.copy())
    return np.asarray(pts)


def _radii_profile(n, base_radius, tip_radius, bulb=1.5):
    """Taper base->tip with a clubbed (bulbous) tip."""
    t = np.linspace(0.0, 1.0, n)
    r = base_radius * (1 - t) + tip_radius * t
    club = t > 0.82
    r[club] = tip_radius * bulb * np.sin(np.linspace(0.5, np.pi / 2, club.sum()))
    r[-1] = tip_radius * 0.6
    return r


def tentacle_field(
    mesh: trimesh.Trimesh,
    count: int = 450,
    *,
    base_length: float = 38.0,
    size_by_height=(0.55, 1.7),     # length scale at base / crown
    base_radius: float = 2.2,        # thicker than pins
    tip_radius: float = 1.1,
    segments: int = 12,
    sides: int = 6,
    up_bias: float = 0.62,           # how strongly tentacles reach up
    curl: float = 0.55,
    curl_jitter: float = 0.22,       # +~20% bend variety
    top_fraction: float = 0.45,      # only seed the upper crown
    seed: int = 0,
):
    """Grow a curled, upward tentacle crown. Returns mesh with vertex t in
    mesh.vertex_attributes['t'] and direction-free RGBA tip gradient hint."""
    rng = np.random.default_rng(seed)
    # oversample, then keep the upper crown by normalized height h
    pts, nrm = sample_seeds(mesh, count * 4, seed=seed)
    z = pts[:, 2]
    h = (z - z.min()) / (z.ptp() + 1e-9)
    keep = h >= (1.0 - top_fraction)
    pts, nrm, h = pts[keep], nrm[keep], h[keep]
    if len(pts) > count:
        idx = rng.choice(len(pts), count, replace=False)
        pts, nrm, h = pts[idx], nrm[idx], h[idx]

    lo, hi = size_by_height
    Vs, Fs, Ts = [], [], []
    off = 0
    for i in range(len(pts)):
        size = lo + (hi - lo) * h[i]
        length = base_length * size
        d0 = nrm[i] / (np.linalg.norm(nrm[i]) + 1e-12)
        d0 = 0.6 * d0 + 0.4 * np.array([0.0, 0.0, 1.0])   # start leaning up
        ang = rng.uniform(0, 2 * np.pi)
        curl_dir = np.array([np.cos(ang), np.sin(ang), 0.3])
        this_curl = curl * (1.0 + (rng.random() - 0.5) * 2 * curl_jitter)
        cl = _grow_centerline(pts[i], d0, length, segments, up_bias,
                              curl_dir, this_curl, jitter=0.06, rng=rng)
        radii = _radii_profile(len(cl), base_radius * size, tip_radius * size)
        res = sweep_tube(cl, radii, sides=sides)
        if res is None:
            continue
        v, f, _ = res
        # tip apex cap
        apex = cl[-1] + (cl[-1] - cl[-2]) * 0.4
        apex_idx = len(v)
        v = np.vstack([v, apex])
        last = (len(cl) - 1) * sides
        cap = [[last + j, last + (j + 1) % sides, apex_idx] for j in range(sides)]
        f = np.vstack([f, np.array(cap)])
        tvals = np.concatenate([np.repeat(np.linspace(0, 1, len(cl)), sides),
                                [1.0]])
        Vs.append(v)
        Fs.append(f + off)
        Ts.append(tvals)
        off += len(v)

    V = np.vstack(Vs)
    F = np.vstack(Fs)
    T = np.concatenate(Ts)
    m = trimesh.Trimesh(vertices=V, faces=F, process=False)
    m.vertex_attributes["t"] = T
    return m
