"""Whole-brain wireframe + precentral gyrus (motor strip) highlighted in red.

Run from repo root:
    python -m rendering.examples.01_wireframe_precentral
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.style_wireframe_roi import render_wireframe_roi, WireframeStyle

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/01_wireframe_precentral.png")

# FreeSurfer DKT/aparc cortical labels live in 1000-2999.
# Subcortical structures: see FreeSurferColorLUT (10..60).
CORTEX_LABELS = list(range(1000, 3000))
PRECENTRAL = [1024, 2024]   # ctx-lh-precentral, ctx-rh-precentral (M1)

print("[1/3] meshing whole cortex...")
brain = label_to_mesh(NII, CORTEX_LABELS, target_faces=15_000, smooth_iter=40)
print(f"      brain: {len(brain.faces)} faces")

print("[2/3] meshing precentral L+R...")
roi = label_to_mesh(NII, PRECENTRAL, target_faces=8_000, smooth_iter=20)
print(f"      ROI:   {len(roi.faces)} faces")

brain, roi = center_to_origin(brain, roi)

print("[3/3] rendering...")
out = render_wireframe_roi(brain, roi, OUT, style=WireframeStyle())
print(f"wrote {out}  ({out.stat().st_size/1024:.0f} KB)")
