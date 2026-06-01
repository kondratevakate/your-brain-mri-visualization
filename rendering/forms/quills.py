"""Protrusion layer: radial pin/quill field grown on a mesh surface.

Sea-urchin / coral look — thousands of thin tapered rods emitted along
surface normals, with rounded tips. Returns a single trimesh.Trimesh, so it
drops into scene.py as an ordinary Layer (no compositor changes).

The same machinery generalises to CURLED tentacles later: replace the straight
template direction with a curved centerline (curl != 0). Pins are the curl=0
special case.
"""
from __future__ import annotations

import numpy as np
import trimesh


def _pin_template(length: float, base_radius: float, tip_radius: float,
                  segments: int, sides: int):
    """One pin along +Z, base at origin. Returns (verts, faces).

    Rounded tip = an apex vertex pushed slightly beyond the last ring, so the
    specular 'dot' highlight reads at the tip (the signature pin-sculpture look).
    """
    z = np.linspace(0.0, length, segments + 1)
    r = np.linspace(base_radius, tip_radius, segments + 1)
    theta = 2 * np.pi * np.arange(sides) / sides
    cs, sn = np.cos(theta), np.sin(theta)

    rings = np.empty(((segments + 1) * sides, 3))
    for k in range(segments + 1):
        rings[k * sides:(k + 1) * sides, 0] = r[k] * cs
        rings[k * sides:(k + 1) * sides, 1] = r[k] * sn
        rings[k * sides:(k + 1) * sides, 2] = z[k]

    apex = np.array([[0.0, 0.0, length + tip_radius]])  # rounded cap
    verts = np.vstack([rings, apex])
    apex_idx = len(rings)

    faces = []
    for k in range(segments):
        a, b = k * sides, (k + 1) * sides
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append([a + j, a + j2, b + j2])
            faces.append([a + j, b + j2, b + j])
    last = segments * sides
    for j in range(sides):
        j2 = (j + 1) % sides
        faces.append([last + j, last + j2, apex_idx])
    return verts, np.array(faces, dtype=np.int64)


def _rot_z_to(d: np.ndarray) -> np.ndarray:
    """Rotation matrix mapping +Z onto unit vector d (Rodrigues)."""
    z = np.array([0.0, 0.0, 1.0])
    d = d / (np.linalg.norm(d) + 1e-12)
    v = np.cross(z, d)
    c = float(np.dot(z, d))
    if c > 0.99999:
        return np.eye(3)
    if c < -0.99999:
        return np.diag([1.0, -1.0, -1.0])  # 180° flip
    s = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + s + s @ s * (1.0 / (1.0 + c))


def sample_seeds(mesh: trimesh.Trimesh, count: int, seed: int = 0):
    """Area-weighted surface points + outward normals (RANDOM scatter)."""
    pts, fid = trimesh.sample.sample_surface(mesh, count, seed=seed)
    nrm = np.asarray(mesh.face_normals[fid])
    pts = np.asarray(pts)
    # marching_cubes winding is not guaranteed outward — force normals to point
    # away from the mesh centroid so pins grow OUT, not into the volume.
    outward = pts - mesh.centroid
    flip = np.einsum("ij,ij->i", nrm, outward) < 0
    nrm[flip] *= -1.0
    return pts, nrm


def rows_seeds(mesh: trimesh.Trimesh, n_rows: int = 44, pins_per_row: int = 170,
               el_range=(-78.0, 82.0), jitter: float = 0.0, seed: int = 0):
    """Ordered HORIZONTAL ROWS of seeds (concentric-ring layout).

    Cast rays from the centroid on a latitude(row) x longitude(position) grid;
    each ray's farthest surface hit is a pin base, and the radial ray direction
    is the pin orientation. Constant-elevation rays form one horizontal row, so
    pins encircle the body in concentric rings — the signature radial pattern.
    """
    c = np.asarray(mesh.centroid)
    els = np.deg2rad(np.linspace(el_range[0], el_range[1], n_rows))
    azs = np.linspace(0.0, 2 * np.pi, pins_per_row, endpoint=False)
    EL, AZ = np.meshgrid(els, azs, indexing="ij")
    if jitter > 0.0:
        # perturb each pin by a fraction of the grid step -> organic unevenness
        rng = np.random.default_rng(seed)
        d_el = np.deg2rad((el_range[1] - el_range[0]) / max(n_rows - 1, 1))
        d_az = 2 * np.pi / pins_per_row
        EL = EL + (rng.random(EL.shape) - 0.5) * jitter * d_el
        AZ = AZ + (rng.random(AZ.shape) - 0.5) * jitter * d_az
    dirs = np.stack([np.cos(EL) * np.cos(AZ),
                     np.cos(EL) * np.sin(AZ),
                     np.sin(EL)], axis=-1).reshape(-1, 3)

    origins = np.repeat(c[None, :], len(dirs), axis=0)
    locs, ray_idx, _ = mesh.ray.intersects_location(
        origins, dirs, multiple_hits=True)
    # keep the FARTHEST hit per ray (outer shell)
    dist = np.linalg.norm(locs - c, axis=1)
    best = np.full(len(dirs), -1.0)
    pts = np.zeros((len(dirs), 3))
    for i, r in enumerate(ray_idx):
        if dist[i] > best[r]:
            best[r] = dist[i]
            pts[r] = locs[i]
    valid = best > 0
    return pts[valid], dirs[valid]


def pin_field(
    mesh: trimesh.Trimesh,
    count: int = 8000,
    *,
    length: float = 18.0,
    length_jitter: float = 0.25,
    base_radius: float = 0.5,
    tip_radius: float = 0.18,
    segments: int = 3,
    sides: int = 6,
    seed: int = 0,
    seeds=None,
) -> trimesh.Trimesh:
    """Grow pins on the mesh surface, aligned to their seed directions.

    seeds: optional (pts, dirs) tuple (e.g. from rows_seeds for ordered rows).
    If None, falls back to `count` RANDOM area-weighted seeds.
    All lengths in mm (same space as the mesh). Returns one combined mesh.
    """
    if seeds is not None:
        pts, nrm = seeds
        count = len(pts)
    else:
        pts, nrm = sample_seeds(mesh, count, seed=seed)
    tv, tf = _pin_template(length, base_radius, tip_radius, segments, sides)
    nv = len(tv)
    rng = np.random.default_rng(seed)

    V = np.empty((count * nv, 3))
    F = np.empty((count * len(tf), 3), dtype=np.int64)
    for i in range(count):
        L = 1.0 + (rng.random() - 0.5) * 2.0 * length_jitter
        v = tv.copy()
        v[:, 2] *= L                       # per-pin length jitter
        v = v @ _rot_z_to(nrm[i]).T + pts[i]
        V[i * nv:(i + 1) * nv] = v
        F[i * len(tf):(i + 1) * len(tf)] = tf + i * nv

    # process=False: skip expensive vertex-merge on a huge non-manifold field
    return trimesh.Trimesh(vertices=V, faces=F, process=False)
