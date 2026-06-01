"""Style #3 — gray wireframe brain + opaque ROI overlay.

Pure matplotlib (no VTK), so it works on machines where Application Control
policy blocks vtkWebCore. Output: publication-grade PNG with white background.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.colors import LightSource, to_rgba
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


@dataclass
class WireframeStyle:
    # brain shell
    brain_face_rgba: tuple = (1.0, 1.0, 1.0, 0.0)    # invisible faces
    brain_edge_rgba: tuple = (0.30, 0.30, 0.34, 0.28)  # gray edges, low alpha
    brain_linewidth: float = 0.12
    # ROI
    roi_color: str = "#d92b2b"           # arterial red, matches reference #3
    roi_edge_rgba: tuple = (0.55, 0.0, 0.0, 0.9)
    roi_linewidth: float = 0.15
    roi_alpha: float = 0.95
    roi_shade: bool = True               # add fake lighting to ROI for depth
    # scene
    background: str = "white"
    figsize: tuple = (10, 10)
    dpi: int = 200
    # camera: matplotlib elev/azim in degrees. Sagittal-left default.
    # RAS canonical convention (see mesh_prep.label_to_mesh):
    #   elev=0, azim=0   -> left lateral (looking from +X toward origin)
    #   elev=0, azim=180 -> right lateral
    #   elev=90          -> superior (top-down)
    elev: float = 8.0
    azim: float = 5.0
    zoom: float = 0.78                   # <1 zooms in; cuts whitespace


def _shaded_face_colors(mesh: trimesh.Trimesh, base_rgb, light_azdeg=315, light_altdeg=45):
    """Per-face shading via Lambert-ish normal dot light direction."""
    ls = LightSource(azdeg=light_azdeg, altdeg=light_altdeg)
    # face normals
    n = mesh.face_normals
    # light direction (unit)
    az = np.deg2rad(light_azdeg)
    al = np.deg2rad(light_altdeg)
    L = np.array([np.cos(al) * np.cos(az), np.cos(al) * np.sin(az), np.sin(al)])
    intensity = np.clip(n @ L, 0, 1)
    intensity = 0.45 + 0.55 * intensity  # avoid pure black on back faces
    base = np.array(to_rgba(base_rgb))[:3]
    rgb = intensity[:, None] * base[None, :]
    return rgb


def _add_mesh(ax, mesh: trimesh.Trimesh, *, face_rgba, edge_rgba, linewidth,
              shade_base=None, alpha=None):
    tris = mesh.vertices[mesh.faces]  # (F, 3, 3)
    coll = Poly3DCollection(
        tris,
        linewidths=linewidth,
        edgecolors=edge_rgba,
    )
    if shade_base is not None:
        rgb = _shaded_face_colors(mesh, shade_base)
        a = alpha if alpha is not None else 1.0
        face_arr = np.concatenate([rgb, np.full((len(rgb), 1), a)], axis=1)
        coll.set_facecolors(face_arr)
    else:
        coll.set_facecolor(face_rgba)
    ax.add_collection3d(coll)


def render_wireframe_roi(
    brain: trimesh.Trimesh,
    rois: list[trimesh.Trimesh] | trimesh.Trimesh,
    out_path: str | Path,
    style: WireframeStyle | None = None,
) -> Path:
    """Render a brain shell + one-or-more solid ROIs to PNG.

    Centering is the caller's responsibility — use mesh_prep.center_to_origin
    on (brain, *rois) first so they share a common origin.
    """
    style = style or WireframeStyle()
    if isinstance(rois, trimesh.Trimesh):
        rois = [rois]

    fig = plt.figure(figsize=style.figsize, dpi=style.dpi, facecolor=style.background)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(style.background)

    _add_mesh(
        ax, brain,
        face_rgba=style.brain_face_rgba,
        edge_rgba=style.brain_edge_rgba,
        linewidth=style.brain_linewidth,
    )
    for roi in rois:
        _add_mesh(
            ax, roi,
            face_rgba=to_rgba(style.roi_color, style.roi_alpha),
            edge_rgba=style.roi_edge_rgba,
            linewidth=style.roi_linewidth,
            shade_base=style.roi_color if style.roi_shade else None,
            alpha=style.roi_alpha if style.roi_shade else None,
        )

    # uniform axis limits from brain bounds (so the figure isn't distorted)
    bounds = brain.bounds   # (2, 3)
    span = (bounds[1] - bounds[0]).max() * style.zoom
    center = bounds.mean(axis=0)
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center):
        setter(c - span / 2, c + span / 2)

    ax.view_init(elev=style.elev, azim=style.azim)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    plt.tight_layout(pad=0)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=style.dpi, bbox_inches="tight",
                pad_inches=0, facecolor=style.background)
    plt.close(fig)
    return out_path
