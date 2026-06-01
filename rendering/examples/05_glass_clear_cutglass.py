"""Style #1 — iStock-like clear cut-glass brain.

Subdivision Surface modifier + procedural studio HDR environment + sharp
near-zero roughness give the cut-glass highlights.

Run from repo root:
    python -m rendering.examples.05_glass_clear_cutglass
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.style_glass_blender import render_glass, style_clear_glass

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/05_glass_clear_cutglass.png")

CORTEX_LABELS = list(range(1000, 3000))

print("[1/2] meshing whole cortex (envelope mode, base for subdiv)...")
# Lower target_faces because Subdivision Surface will quadruple it twice.
brain = label_to_mesh(NII, CORTEX_LABELS, target_faces=25_000,
                     smooth_iter=80, envelope=True)
print(f"      base: {len(brain.faces)} faces (subdiv x2 -> ~{len(brain.faces)*16})")

(brain,) = center_to_origin(brain)

print("[2/2] rendering with Cycles (clear cut-glass)...")
style = style_clear_glass()
style.samples = 96
style.resolution = (1200, 1200)
out = render_glass(brain, rois=None, out_path=OUT, style=style)
print(f"wrote {out}")
