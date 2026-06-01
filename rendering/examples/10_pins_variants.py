"""Radial pin-field variants (sea-urchin / coral). Renders a couple of colorways.

Geometry is generated ONCE (deterministic seed) and reused across colorways —
only the Material changes. Run from repo root:
    python -m rendering.examples.10_pins_variants
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.forms.quills import pin_field, rows_seeds
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig, render_scene

NII = "example_data/aparc+aseg.nii.gz"
OUTDIR = Path("rendering/output")

# Concentric-ring layout: ORDERED horizontal rows (not random scatter) + SHORT pins,
# so the radial ring pattern reads and tips form a tight surface.
print("meshing body + seeding rows + growing pins (once)...")
shell = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=12_000, smooth_iter=80, envelope=True)
# fewer rows (more vertical gap) + fewer per row => ~half the pins, and a touch
# of jitter for natural unevenness. Pins are 50% thicker to keep coverage.
seeds = rows_seeds(shell, n_rows=46, pins_per_row=160, jitter=0.35, seed=5)
pins = pin_field(shell, length=14.0, length_jitter=0.10,
                 base_radius=1.13, tip_radius=0.42, segments=4, seed=7,
                 seeds=seeds)
print(f"pins: {len(seeds[0])} rods, {len(pins.faces)} faces")
shell, pins = center_to_origin(shell, pins)

VARIANTS = [
    ("white", (0.90, 0.90, 0.91, 1.0), (0.72, 0.72, 0.74)),
    ("red",   (0.78, 0.07, 0.09, 1.0), (0.78, 0.78, 0.80)),
]

for name, color, bg in VARIANTS:
    out = OUTDIR / f"10_pins_{name}.png"
    print(f"rendering {name} -> {out.name}")
    scene = Scene(
        layers=[
            Layer(shell, Material(kind="stone", color=color, roughness=0.55),
                  name="Body"),
            Layer(pins,  Material(kind="stone", color=color, roughness=0.34),
                  name="Pins"),
        ],
        light=LightRig("reef", strength=1.0, background=bg),
        # isometric-ish 3/4 view
        camera=CameraRig(azim_deg=45, elev_deg=33, distance_factor=3.0, dof=False),
        resolution=(1100, 1100),
        samples=64,
    )
    render_scene(scene, out)
    print(f"  wrote {out}")

print("done")
