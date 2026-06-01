"""Corrections 1 & 2: wireframe brain with hippocampus and amygdala highlighted.

Two renders, each isolating one limbic structure (bilateral) inside the
wireframe cortical shell.

Run from repo root:
    python -m rendering.examples.12_wireframe_limbic
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.style_wireframe_roi import render_wireframe_roi, WireframeStyle

NII = "example_data/aparc+aseg.nii.gz"
OUTDIR = Path("rendering/output")

# FreeSurferColorLUT: 17/53 Hippocampus L/R, 18/54 Amygdala L/R
STRUCTURES = {
    "hippocampus": ([17, 53], "#c0392b"),
    "amygdala":    ([18, 54], "#8e44ad"),
}

print("meshing wireframe cortical shell (detailed)...")
brain = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=15_000, smooth_iter=40, envelope=False)

for name, (labels, color) in STRUCTURES.items():
    print(f"meshing {name}...")
    roi = label_to_mesh(NII, labels, target_faces=8_000,
                        smooth_iter=20, keep_largest=False)
    b, r = center_to_origin(brain, roi)
    out = OUTDIR / f"12_wireframe_{name}.png"
    render_wireframe_roi(b, r, out,
                         style=WireframeStyle(elev=4, azim=8,
                                              roi_color=color, roi_alpha=0.95))
    print(f"  wrote {out}")

print("done")
