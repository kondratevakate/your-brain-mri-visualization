"""Glass shader sanity-check on an existing closed mesh (subcortical.stl).

This avoids marching-cubes mesh holes and isolates the shader quality.
"""
from pathlib import Path
import trimesh

from rendering.mesh_prep import center_to_origin
from rendering.style_glass_blender import render_glass, style_frosted_blue

STL = "my-brain-models/subcortical.stl"
OUT = Path("rendering/output/04_glass_subcortical.png")

print("[1/2] loading STL...")
brain = trimesh.load(STL, force="mesh")
print(f"      mesh: {len(brain.faces)} faces, watertight={brain.is_watertight}")

(brain,) = center_to_origin(brain)

print("[2/2] rendering with Cycles...")
style = style_frosted_blue()
style.samples = 96
style.resolution = (1200, 1200)
out = render_glass(brain, rois=None, out_path=OUT, style=style)
print(f"wrote {out}")
