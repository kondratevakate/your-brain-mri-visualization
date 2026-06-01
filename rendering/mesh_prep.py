"""voxels -> clean triangle mesh, ready for stylised rendering.

Single entry point: `label_to_mesh(nii_path, label_ids, ...)` returns a trimesh.Trimesh
with isotropic spacing applied, Taubin-smoothed (no shrinkage), and decimated to
a target face count (raw cortex from marching_cubes is ~500k faces and renders
as black mush in wireframe mode).
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import nibabel as nib
import trimesh
from skimage import measure
from scipy.ndimage import binary_closing, binary_fill_holes, gaussian_filter
import fast_simplification


def _binary_mask(seg: np.ndarray, label_ids: list[int],
                 envelope: bool = False) -> np.ndarray:
    """Build a binary mask from label IDs.

    envelope=True bridges sulci with morphological closing — produces a smooth
    outer shell suitable for glass rendering. envelope=False keeps anatomical
    detail (sulci/gyri) — suitable for wireframe rendering.
    """
    mask = np.isin(seg, label_ids)
    if envelope:
        # Gaussian-smooth on float -> threshold: closes sulci AND 3D cavities
        # (ventricles, deep folds) in a single shot. sigma in voxels; 3 vox ~ 3 mm
        # for an isotropic 1 mm volume.
        smooth = gaussian_filter(mask.astype(np.float32), sigma=3.0)
        mask = smooth > 0.4   # <0.5 = slight inflation to preserve tips
    else:
        mask = binary_closing(mask, iterations=1)
    mask = binary_fill_holes(mask)
    return mask


def label_to_mesh(
    nii_path: str | Path,
    label_ids: list[int],
    *,
    target_faces: int = 30_000,
    smooth_iter: int = 30,
    keep_largest: bool = True,
    envelope: bool = False,
) -> trimesh.Trimesh:
    """Voxel labels -> smoothed, decimated triangle mesh in canonical RAS mm-space.

    Reorientation to RAS guarantees: X=right, Y=anterior, Z=superior. This makes
    matplotlib camera angles predictable (elev=0, azim=0 = looking from +X = left
    sagittal view of a right-handed brain).
    """
    img = nib.as_closest_canonical(nib.load(str(nii_path)))
    seg = np.asarray(img.dataobj)
    spacing = tuple(float(s) for s in np.sqrt((img.affine[:3, :3] ** 2).sum(axis=0)))

    mask = _binary_mask(seg, label_ids, envelope=envelope)
    if not mask.any():
        raise ValueError(f"no voxels match labels {label_ids} in {nii_path}")

    verts, faces, normals, _ = measure.marching_cubes(
        mask.astype(np.uint8), level=0.5, spacing=spacing, allow_degenerate=False
    )
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals, process=True)

    if keep_largest:
        comps = mesh.split(only_watertight=False)
        if len(comps) > 1:
            mesh = max(comps, key=lambda m: len(m.faces))

    # Taubin = low-pass smoothing that does NOT shrink volume (unlike Laplacian)
    trimesh.smoothing.filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=smooth_iter)

    if target_faces and len(mesh.faces) > target_faces:
        v, f = fast_simplification.simplify(
            mesh.vertices, mesh.faces, target_count=target_faces
        )
        mesh = trimesh.Trimesh(vertices=v, faces=f, process=True)

    return mesh


def center_to_origin(*meshes: trimesh.Trimesh) -> tuple[trimesh.Trimesh, ...]:
    """Recenter all meshes by the SAME translation (first mesh's centroid)."""
    if not meshes:
        return ()
    offset = meshes[0].centroid.copy()
    out = []
    for m in meshes:
        m = m.copy()
        m.apply_translation(-offset)
        out.append(m)
    return tuple(out)
