"""Correction 3: textured glass that separates from the background.

Fixes the "too smooth, blends with bg" problem:
  - Surface(STUCCI) micro-relief => varied refraction (cast-glass texture)
  - dark background + dramatic rim light => bright Fresnel edges pop the object
  - low roughness => crisp, lively highlights

Run from repo root:
    python -m rendering.examples.13_glass_textured
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.scene import (Scene, Layer, Material, Surface,
                             LightRig, CameraRig, render_scene)

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/13_glass_textured.png")

print("[1/2] meshing shell (envelope, light smoothing keeps relief)...")
shell = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=60_000, smooth_iter=25, envelope=True)
(shell,) = center_to_origin(shell)

print("[2/2] rendering textured glass...")
scene = Scene(
    layers=[
        Layer(
            shell,
            Material(kind="glass", color=(0.88, 0.94, 1.0, 1.0),
                     roughness=0.05, ior=1.48,
                     absorption_color=(0.30, 0.55, 0.92),  # stronger blue depth
                     absorption_density=0.022),
            surface=Surface(texture="STUCCI", strength=1.3,
                            noise_scale=6.0, subdivide=2),
            name="GlassCortex",
        ),
    ],
    # bright studio gradient gives the glass something to refract; the blue
    # absorption + crisp highlights separate it from the light background.
    light=LightRig("studio", strength=1.1),
    camera=CameraRig(azim_deg=28, elev_deg=10, distance_factor=2.4, dof=False),
    resolution=(1100, 1100),
    samples=128,
)
out = render_scene(scene, OUT)
print(f"wrote {out}")
