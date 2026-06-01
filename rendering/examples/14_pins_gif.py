"""Looping GIF: slow brain rotation + gentle white-pin sway.

Small/low-sample for animation speed. Run from repo root:
    python -m rendering.examples.14_pins_gif
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.forms.quills import rows_seeds, pin_field
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig
from rendering.animate import render_whip_gif

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/14_pins_sway.gif")
PIN_COLOR = (0.90, 0.90, 0.91, 1.0)

print("meshing body + seeding rows (once)...")
shell = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=12_000, smooth_iter=80, envelope=True)
pts, dirs = rows_seeds(shell, n_rows=46, pins_per_row=160, jitter=0.35, seed=5)

# center shell AND seed points by the same offset (dirs are unaffected by shifts)
offset = shell.centroid.copy()
shell.apply_translation(-offset)
pts = pts - offset

PIN_KWARGS = dict(length=15.0, base_radius=1.13, tip_radius=0.42,
                  segments=6, sides=6)


def scene_factory(shell_r, pins):
    return Scene(
        layers=[
            Layer(shell_r, Material(kind="stone", color=PIN_COLOR, roughness=0.55),
                  name="Body"),
            Layer(pins, Material(kind="stone", color=PIN_COLOR, roughness=0.34),
                  name="Pins"),
        ],
        light=LightRig("reef", strength=1.0, background=(0.72, 0.72, 0.74)),
        camera=CameraRig(azim_deg=45, elev_deg=33, distance_factor=3.0),
        resolution=(480, 480),     # small for GIF
        samples=20,                # low + denoise; matte white tolerates it
    )


render_whip_gif(
    shell, (pts, dirs), PIN_KWARGS, scene_factory, OUT,
    n_frames=44,
    total_deg=18.0,   # brain turns ~18deg with acceleration
    whip_deg=48.0,    # BIG visible tip whip (pins bend, not tilt)
    w0=3.5, zeta=0.08,  # low damping => several visible bounces before settling
    fps=22,
)
