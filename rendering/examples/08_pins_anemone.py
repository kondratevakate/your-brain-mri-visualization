"""Sea-urchin / coral look — dense radial pin field on the brain envelope.

The pin field is just another mesh Layer, so it composes through scene.py with
no compositor changes. Swap Material.color for red / pink / chartreuse variants.

Run from repo root:
    python -m rendering.examples.08_pins_anemone
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.forms.quills import pin_field
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig, render_scene

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/08_pins_anemone.png")
PIN_COLOR = (0.90, 0.90, 0.91, 1.0)   # white porcelain; try (0.80,0.10,0.12) red

print("[1/3] meshing brain envelope (the body under the pins)...")
shell = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=12_000, smooth_iter=80, envelope=True)

print("[2/3] growing pin field...")
pins = pin_field(shell, count=7000, length=34.0, length_jitter=0.16,
                 base_radius=0.9, tip_radius=0.32, segments=4, seed=7)
print(f"      pins: {len(pins.faces)} faces")

shell, pins = center_to_origin(shell, pins)

print("[3/3] composing + rendering...")
scene = Scene(
    layers=[
        Layer(shell, Material(kind="stone", color=PIN_COLOR, roughness=0.55),
              name="Body"),
        Layer(pins,  Material(kind="stone", color=PIN_COLOR, roughness=0.32),
              smooth=True, name="Pins"),
    ],
    light=LightRig("reef", strength=1.0, background=(0.72, 0.72, 0.74)),
    camera=CameraRig(azim_deg=20, elev_deg=6, distance_factor=3.0, dof=False),
    resolution=(1100, 1100),
    samples=64,
)
out = render_scene(scene, OUT)
print(f"wrote {out}")
