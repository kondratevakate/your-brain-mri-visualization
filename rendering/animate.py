"""Turntable + pin-sway GIF builder.

Renders a seamless looping GIF of the brain slowly rotating while its pins sway
like an anemone in a current. Geometry rotates (camera + lights stay fixed) for
a true turntable look; pins sway via a traveling wave over the surface.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import imageio.v2 as imageio
import trimesh

from rendering.forms.quills import pin_field
from rendering.forms.sweep import sweep_tube
from rendering.scene import Scene, Layer, render_scene


def _rz(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _rotate_about_axis(v, axis, ang):
    """Rodrigues rotation of vectors v (N,3) about per-row unit axis (N,3)."""
    axis = axis / (np.linalg.norm(axis, axis=1, keepdims=True) + 1e-12)
    cosA = np.cos(ang)[:, None]
    sinA = np.sin(ang)[:, None]
    dot = np.einsum("ij,ij->i", axis, v)[:, None]
    return (v * cosA
            + np.cross(axis, v) * sinA
            + axis * dot * (1.0 - cosA))


def sway_dirs(pts, base_dirs, t, *, amp_deg=7.0, cycles=2.0,
              wavelen=55.0, wave_dir=(1.0, 0.3, 0.0)):
    """Sway each pin direction by a small angle from a traveling wave.

    t in [0,1) is loop phase. The wave phase depends on each pin's position so
    the sway sweeps across the body. Sway axis is lateral (perp to the pin), so
    tips lean sideways rather than stretch.
    """
    wave_dir = np.asarray(wave_dir, float)
    wave_dir /= np.linalg.norm(wave_dir) + 1e-12
    phase = (pts @ wave_dir) / wavelen
    ang = np.deg2rad(amp_deg) * np.sin(2 * np.pi * (cycles * t + phase))
    # lateral axis = dir x up (fallback x-axis if near-vertical)
    up = np.array([0.0, 0.0, 1.0])
    axis = np.cross(base_dirs, up)
    bad = np.linalg.norm(axis, axis=1) < 1e-6
    axis[bad] = np.array([1.0, 0.0, 0.0])
    return _rotate_about_axis(base_dirs, axis, ang)


def build_whip_pins(pts, dirs, whip, *, length=14.0, base_radius=1.13,
                    tip_radius=0.42, segments=5, sides=6):
    """Build BENT pins: root planted at pts, tip lagging by `whip` (rad) about Z.

    The azimuthal bend grows with height along each pin (root=0, tip=whip), so
    pins curve like flexible hair rather than tilting rigidly. `whip` is per-pin.
    """
    Vs, Fs = [], []
    off = 0
    ks = np.linspace(0.0, 1.0, segments + 1)
    radii = np.linspace(base_radius, tip_radius, segments + 1)
    for i in range(len(pts)):
        d0 = dirs[i] / (np.linalg.norm(dirs[i]) + 1e-12)
        P = pts[i][None, :] + np.outer(ks * length, d0)      # straight rod
        ang = whip[i] * ks                                    # bend grows to tip
        rel = P - pts[i]
        c, s = np.cos(ang), np.sin(ang)
        relx = rel[:, 0] * c - rel[:, 1] * s
        rely = rel[:, 0] * s + rel[:, 1] * c
        Pc = np.stack([pts[i, 0] + relx, pts[i, 1] + rely,
                       pts[i, 2] + rel[:, 2]], axis=1)
        res = sweep_tube(Pc, radii, sides=sides)
        if res is None:
            continue
        v, f, _ = res
        apex = Pc[-1] + (Pc[-1] - Pc[-2]) * 0.5
        apex_idx = len(v)
        v = np.vstack([v, apex])
        last = segments * sides
        cap = [[last + j, last + (j + 1) % sides, apex_idx] for j in range(sides)]
        Vs.append(v)
        Fs.append(np.vstack([f, np.array(cap)]) + off)
        off += len(v)
    return trimesh.Trimesh(vertices=np.vstack(Vs), faces=np.vstack(Fs),
                           process=False)


def render_fur_gif(shell, layers, scene_factory, out_gif, *,
                   n_frames=40, schedule=None, total_deg=18.0, whip_deg=48.0,
                   w0=4.0, zeta=0.1, fps=15, seed=11,
                   tmpdir="rendering/output/_frames"):
    """Multi-layer fur animation (e.g. dark stiff undercoat + long soft topcoat).

    layers: list of dicts, each:
        seeds=(pts, dirs)         # pre-centered random seeds (sample_seeds)
        pin_kwargs=dict(...)      # length/radius/segments for build_whip_pins
        name="Topcoat"
        whip_scale=1.0            # >1 = whips more (soft), <1 = stiffer
    scene_factory(shell_r, {name: pin_mesh}) -> Scene.
    """
    rng = np.random.default_rng(seed)
    for L in layers:
        n = len(L["seeds"][0])
        L["_factors"] = rng.uniform(0.6, 1.2, n) * L.get("whip_scale", 1.0)
    body, lag = (schedule if schedule is not None else
                 whip_schedule(n_frames, total_deg=total_deg, whip_deg=whip_deg,
                               w0=w0, zeta=zeta))
    tmpdir = Path(tmpdir); tmpdir.mkdir(parents=True, exist_ok=True)
    out_gif = Path(out_gif)

    frames = []
    for i in range(n_frames):
        R = _rz(body[i])
        shell_r = shell.copy(); shell_r.vertices = shell_r.vertices @ R.T
        meshes = {}
        for L in layers:
            pts0, dirs0 = L["seeds"]
            pts_r = pts0 @ R.T
            dirs_r = dirs0 @ R.T
            meshes[L["name"]] = build_whip_pins(
                pts_r, dirs_r, lag[i] * L["_factors"], **L["pin_kwargs"])
        fp = tmpdir / f"frame_{i:03d}.png"
        render_scene(scene_factory(shell_r, meshes), fp)
        frames.append(imageio.imread(fp))
        print(f"  frame {i+1}/{n_frames}")
    imageio.mimsave(out_gif, frames, fps=fps, loop=0)
    print(f"wrote {out_gif} ({n_frames} frames @ {fps}fps)")
    return out_gif


def _rz_per_row(v, phi):
    """Rotate each row of v (N,3) about +Z by per-row angle phi (N,)."""
    c, s = np.cos(phi), np.sin(phi)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    return np.stack([x * c - y * s, x * s + y * c, z], axis=1)


def whip_schedule(n_frames, *, total_deg=15.0, whip_deg=18.0,
                  w0=4.0, zeta=0.16, fine=900):
    """Primary brain angle + secondary pin-whip lag, both sampled per frame.

    Returns (body_angle[n], lag[n]) in radians.
      body_angle: A/2*(1-cos 2pi t)  -> smooth loop, strong accel at the ends
      lag: damped-oscillator response to the body's angular ACCELERATION,
           rescaled so its peak == whip_deg (so whip_deg is the real knob).
    """
    A = np.deg2rad(total_deg)
    tf = np.linspace(0.0, 1.0, fine)
    angle_f = A / 2 * (1 - np.cos(2 * np.pi * tf))
    return _schedule_from_body(angle_f, n_frames, whip_deg, w0, zeta)


def _damped_response(accel_f, w0, zeta, n_loops=8):
    """Steady-state periodic lag of a damped oscillator driven by accel_f.

    Integrated over several loops of the PERIODIC drive so the kept (last) loop
    is periodic (start==end) => seamless animation.
    """
    fine = len(accel_f)
    w = 2 * np.pi * w0
    theta, omega = 0.0, 0.0
    dt = 1.0 / (fine - 1)
    lag_f = np.empty(fine)
    for loop in range(n_loops):
        for i in range(fine):
            drive = -accel_f[i]                  # inertia opposes acceleration
            omega += (drive - 2 * zeta * w * omega - w * w * theta) * dt
            theta += omega * dt
            if loop == n_loops - 1:
                lag_f[i] = theta
    return lag_f


def _schedule_from_body(angle_f, n_frames, whip_deg, w0, zeta):
    tf = np.linspace(0.0, 1.0, len(angle_f))
    accel_f = np.gradient(np.gradient(angle_f, tf), tf)
    lag_f = _damped_response(accel_f, w0, zeta)
    lag_f *= np.deg2rad(whip_deg) / (np.max(np.abs(lag_f)) + 1e-12)
    idx = np.floor(np.linspace(0, len(angle_f) - 1, n_frames)).astype(int)
    return angle_f[idx], lag_f[idx]


def shake_schedule(n_frames, *, shake_deg=30.0, n_shakes=5, whip_deg=75.0,
                   w0=5.0, zeta=0.12, fine=1400):
    """Dog-shake body motion + fur whip lag.

    body = shake_deg * sin(2*pi*n_shakes*t) * sin(pi*t)
      -> n_shakes rapid twists inside a rise-and-fall window (seamless loop).
    The violent acceleration drives the fur to whip hard and settle.
    """
    tf = np.linspace(0.0, 1.0, fine)
    angle_f = np.deg2rad(shake_deg) * np.sin(2 * np.pi * n_shakes * tf) * np.sin(np.pi * tf)
    return _schedule_from_body(angle_f, n_frames, whip_deg, w0, zeta)


def render_whip_gif(
    shell: trimesh.Trimesh,
    base_seeds,                      # (pts, dirs) pre-centered
    pin_kwargs: dict,
    scene_factory,                   # callable(shell, pins) -> Scene
    out_gif: str | Path,
    *,
    n_frames: int = 40,
    total_deg: float = 15.0,         # net brain rotation over the whole loop
    whip_deg: float = 18.0,          # peak pin overshoot from inertia
    w0: float = 4.0,                 # whip bounce frequency
    zeta: float = 0.16,              # whip damping (lower = more bounces)
    fps: int = 20,
    seed: int = 11,
    schedule=None,                   # optional (body, lag) arrays len n_frames
    tmpdir: str | Path = "rendering/output/_frames",
):
    pts0, dirs0 = base_seeds
    rng = np.random.default_rng(seed)
    factors = rng.uniform(0.6, 1.2, len(pts0))   # per-pin whip variety
    if schedule is not None:
        body, lag = schedule
    else:
        body, lag = whip_schedule(n_frames, total_deg=total_deg,
                                  whip_deg=whip_deg, w0=w0, zeta=zeta)

    tmpdir = Path(tmpdir)
    tmpdir.mkdir(parents=True, exist_ok=True)
    out_gif = Path(out_gif)

    frames = []
    for i in range(n_frames):
        # roots + base directions rotate rigidly with the body; the BEND (tip
        # lag) is applied per-pin inside build_whip_pins so pins curve like hair.
        pts_r = pts0 @ _rz(body[i]).T
        dirs_r = dirs0 @ _rz(body[i]).T
        shell_r = shell.copy()
        shell_r.vertices = shell_r.vertices @ _rz(body[i]).T

        pins = build_whip_pins(pts_r, dirs_r, lag[i] * factors, **pin_kwargs)
        frame_path = tmpdir / f"frame_{i:03d}.png"
        render_scene(scene_factory(shell_r, pins), frame_path)
        frames.append(imageio.imread(frame_path))
        print(f"  frame {i+1}/{n_frames}  body={np.degrees(body[i]):.1f}deg "
              f"lag={np.degrees(lag[i]):.1f}deg")

    imageio.mimsave(out_gif, frames, fps=fps, loop=0)
    print(f"wrote {out_gif} ({n_frames} frames @ {fps}fps)")
    return out_gif
