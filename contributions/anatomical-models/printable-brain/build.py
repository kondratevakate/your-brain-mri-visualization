"""Export a 3D-printable brain STL + a thumbnail.

    python contributions/anatomical-models/printable-brain/build.py

Folders use hyphens, so run as a FILE (not `python -m`). The bootstrap below
puts the repo root on sys.path so `rendering` imports work.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fast_simplification

from rendering.mesh_prep import label_to_mesh, center_to_origin

HERE = Path(__file__).resolve().parent
NII = "example_data/aparc+aseg.nii.gz"


def build():
    # closed envelope = watertight-ish shell, safest for slicing/printing
    mesh = label_to_mesh(NII, list(range(1000, 3000)),
                         target_faces=120_000, smooth_iter=40, envelope=True)
    (mesh,) = center_to_origin(mesh)
    stl = HERE / "brain.stl"
    mesh.export(stl)
    print(f"wrote {stl}  ({len(mesh.faces)} faces, "
          f"{stl.stat().st_size/1e6:.1f} MB)")

    # lightweight shaded thumbnail
    v, f = fast_simplification.simplify(mesh.vertices, mesh.faces,
                                        target_count=4000)
    fig = plt.figure(figsize=(4, 4), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_trisurf(v[:, 0], v[:, 1], f, v[:, 2],
                    color="#dcdce0", edgecolor="none", linewidth=0)
    ax.set_axis_off()
    ax.view_init(elev=8, azim=20)
    ax.set_box_aspect((1, 1, 1))
    fig.savefig(HERE / "thumbnail.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote thumbnail.png")


if __name__ == "__main__":
    build()
