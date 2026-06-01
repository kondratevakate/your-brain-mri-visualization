"""Reproduce the pin-whip animation: slow accelerated turn + inertial pin whip.

    python contributions/3d-art/kondratevakate-pin-whip/build.py

Hyphenated folder -> run as a FILE; bootstrap puts repo root on sys.path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root

from rendering.mesh_prep import label_to_mesh
from rendering.forms.quills import rows_seeds
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig
from rendering.animate import render_whip_gif

HERE = Path(__file__).resolve().parent
NII = "example_data/aparc+aseg.nii.gz"
COLOR = (0.90, 0.90, 0.91, 1.0)


def build():
    shell = label_to_mesh(NII, list(range(1000, 3000)),
                          target_faces=12_000, smooth_iter=80, envelope=True)
    pts, dirs = rows_seeds(shell, n_rows=46, pins_per_row=160, jitter=0.35, seed=5)
    offset = shell.centroid.copy()
    shell.apply_translation(-offset)
    pts = pts - offset

    pin_kwargs = dict(length=15.0, base_radius=1.13, tip_radius=0.42,
                      segments=6, sides=6)

    def scene_factory(shell_r, pins):
        return Scene(
            layers=[
                Layer(shell_r, Material(kind="stone", color=COLOR, roughness=0.55),
                      name="Body"),
                Layer(pins, Material(kind="stone", color=COLOR, roughness=0.34),
                      name="Pins"),
            ],
            light=LightRig("reef", strength=1.0, background=(0.72, 0.72, 0.74)),
            camera=CameraRig(azim_deg=45, elev_deg=33, distance_factor=3.0),
            resolution=(480, 480), samples=20,
        )

    render_whip_gif(shell, (pts, dirs), pin_kwargs, scene_factory,
                    HERE / "pin_whip.gif",
                    n_frames=44, total_deg=18.0, whip_deg=48.0,
                    w0=3.5, zeta=0.08, fps=22)


if __name__ == "__main__":
    build()
