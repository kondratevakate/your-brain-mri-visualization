"""Wireframe brain shell + Kate's amygdala (L+R) in red — deck palette, cream bg.

Uses the repo's own rendering engine (pure matplotlib + trimesh).
Source: Kate's 2018 GE 3T SynthSeg segmentation (1 mm isotropic, cleanest scan).

Run from this repo root:
    python make_kate_amygdala_wireframe.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.style_wireframe_roi import render_wireframe_roi, WireframeStyle

# Override via env vars on any machine:
#   set KATE_BRAIN_DATA=D:\data\01_insidekatesbrain
#   set MIDL_SLIDES_DIR=C:\Projects\02_academia\brain-mri-segmentation-midl\slides
_brain_data = Path(os.environ.get(
    "KATE_BRAIN_DATA",
    Path.home() / "YandexDisk/kondratevakate/01_insidekatesbrain",
))
SEG = _brain_data / "01_my_brain_years/reprocessed_2026/seg/seg_2018_ge_fspgr.nii.gz"

_midl_slides = Path(os.environ.get(
    "MIDL_SLIDES_DIR",
    Path("C:/Projects/02_academia/brain-mri-segmentation-midl/slides"),
))
OUT = _midl_slides / "midl2026/renders/wireframe_amygdala.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

# aseg labels: 2/41 white matter L/R, 3/42 cortex L/R → brain shell
SHELL  = [2, 3, 41, 42]
# 18/54 amygdala L/R
AMYG   = [18, 54]

print("[1/3] meshing brain shell (envelope)...")
brain = label_to_mesh(str(SEG), SHELL, target_faces=16_000,
                      smooth_iter=40, envelope=True)
print(f"      shell: {len(brain.faces)} faces")

print("[2/3] meshing amygdala L+R...")
roi = label_to_mesh(str(SEG), AMYG, target_faces=8_000,
                    smooth_iter=25, keep_largest=False, envelope=False)
print(f"      amygdala: {len(roi.faces)} faces")

brain, roi = center_to_origin(brain, roi)

print("[3/3] rendering on cream...")
style = WireframeStyle(
    background="#F5F1ED",                       # deck cream
    brain_edge_rgba=(0.33, 0.36, 0.43, 0.30),   # muted grey wireframe
    brain_linewidth=0.14,
    roi_color="#B85042",                        # deck terracotta
    roi_edge_rgba=(0.55, 0.20, 0.15, 0.9),
    roi_alpha=0.95,
    elev=6.0, azim=12.0,                        # slight oblique sagittal
    zoom=0.92,
    figsize=(9, 9), dpi=200,
)
out = render_wireframe_roi(brain, roi, OUT, style=style)
print(f"wrote {out}  ({out.stat().st_size/1024:.0f} KB)")
