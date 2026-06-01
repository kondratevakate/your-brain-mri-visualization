"""Wireframe brain + hippocampus & amygdala (bilateral) glowing inside.

The "nested" look — limbic structures visible through the transparent cortical
shell — works because matplotlib renders both meshes in the same scene with
shared depth, so the ROI reads as *inside* the brain, not floating on top.

Run from repo root:
    python -m rendering.examples.02_wireframe_hippo_amyg
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.style_wireframe_roi import render_wireframe_roi, WireframeStyle

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/02_wireframe_hippo_amyg.png")

CORTEX_LABELS = list(range(1000, 3000))
# FreeSurferColorLUT:
#   17 Left-Hippocampus    53 Right-Hippocampus
#   18 Left-Amygdala       54 Right-Amygdala
LIMBIC = [17, 53, 18, 54]

print("[1/3] meshing whole cortex...")
brain = label_to_mesh(NII, CORTEX_LABELS, target_faces=15_000, smooth_iter=40)
print(f"      brain: {len(brain.faces)} faces")

print("[2/3] meshing hippocampus + amygdala (L+R)...")
# keep_largest=False — we want BOTH hemispheres as separate components
roi = label_to_mesh(NII, LIMBIC, target_faces=12_000, smooth_iter=25, keep_largest=False)
print(f"      ROI:   {len(roi.faces)} faces")

brain, roi = center_to_origin(brain, roi)

print("[3/3] rendering...")
style = WireframeStyle(
    # nudge view: slightly higher elev so we can see ROI sitting inside the shell
    elev=4.0,
    azim=8.0,
    # slight blue-violet for limbic ROIs reads cleaner than red against gray
    roi_color="#c0392b",
    roi_alpha=0.92,
)
out = render_wireframe_roi(brain, roi, OUT, style=style)
print(f"wrote {out}  ({out.stat().st_size/1024:.0f} KB)")
