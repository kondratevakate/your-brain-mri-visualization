"""Sea-anemone brain, underwater: curled tentacles reaching up from a crown,
sized by height, translucent pink SSS, on a sandy floor with watery haze.

Run from repo root:
    python -m rendering.examples.15_anemone_underwater
"""
from pathlib import Path

import numpy as np
import trimesh

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.forms.tentacles import tentacle_field
from rendering.scene import (Scene, Layer, Material, LightRig, CameraRig,
                             render_scene)

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/15_anemone_underwater.png")

PINK = (0.95, 0.58, 0.58, 1.0)

print("[1/3] meshing body (column)...")
shell = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=20_000, smooth_iter=80, envelope=True)

print("[2/3] growing upward tentacle crown...")
tent = tentacle_field(shell, count=420, base_length=40.0,
                      size_by_height=(0.5, 1.8), base_radius=2.4, tip_radius=1.1,
                      up_bias=0.66, curl=0.55, curl_jitter=0.22,
                      top_fraction=0.5, seed=4)
print(f"      tentacles: {len(tent.faces)} faces")

shell, tent = center_to_origin(shell, tent)

# sandy floor just under the body
floor = trimesh.creation.box(extents=(500, 500, 6))
floor.apply_translation([0, 0, shell.bounds[0][2] - 3])

print("[3/3] rendering underwater...")
scene = Scene(
    layers=[
        Layer(floor, Material(kind="stone", color=(0.80, 0.72, 0.55, 1.0),
                              roughness=0.95), name="Sand"),
        Layer(shell, Material(kind="sss", color=PINK, sss_weight=1.0,
                              sss_radius=(7.0, 3.0, 1.8), roughness=0.45),
              name="Column"),
        Layer(tent, Material(kind="sss", color=PINK, sss_weight=1.0,
                             sss_radius=(8.0, 3.5, 2.2), roughness=0.4),
              name="Tentacles"),
    ],
    light=LightRig("underwater", strength=1.0),
    camera=CameraRig(azim_deg=35, elev_deg=7, distance_factor=2.6, dof=False),
    resolution=(1100, 1100),
    samples=96,
)
render_scene(scene, OUT)
print(f"wrote {OUT}")
