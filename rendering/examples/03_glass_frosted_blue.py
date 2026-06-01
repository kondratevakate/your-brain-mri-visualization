"""Style #2 — frosted blue glass brain via Blender Cycles.

Run from repo root:
    python -m rendering.examples.03_glass_frosted_blue

Expect 1-8 minutes depending on GPU/CPU.
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.style_glass_blender import render_glass, style_frosted_blue

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/03_glass_frosted_blue.png")

CORTEX_LABELS = list(range(1000, 3000))

print("[1/2] meshing whole cortex (high-res for glass)...")
brain = label_to_mesh(NII, CORTEX_LABELS, target_faces=80_000,
                      smooth_iter=80, envelope=True)
print(f"      brain: {len(brain.faces)} faces, {len(brain.vertices)} verts")

(brain,) = center_to_origin(brain)

print("[2/2] rendering with Cycles...")
style = style_frosted_blue()
# trim render time for first iteration; bump to 256 once we're happy
style.samples = 64
style.resolution = (1200, 1200)
out = render_glass(brain, rois=None, out_path=OUT, style=style)
print(f"wrote {out}")
