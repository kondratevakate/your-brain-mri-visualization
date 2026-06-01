"""Radial pin brain: ordered horizontal rows of thick pins (sea-urchin / coral).

    python -m contributions.kondratevakate-pin-brain.build
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.forms.quills import rows_seeds, pin_field
from rendering.presets import pin_brain
from rendering.scene import render_scene

HERE = Path(__file__).resolve().parent
NII = "example_data/aparc+aseg.nii.gz"


def build():
    shell = label_to_mesh(NII, list(range(1000, 3000)),
                          target_faces=12_000, smooth_iter=80, envelope=True)
    seeds = rows_seeds(shell, n_rows=46, pins_per_row=160, jitter=0.35, seed=5)
    pins = pin_field(shell, length=14.0, length_jitter=0.10,
                     base_radius=1.13, tip_radius=0.42, segments=4, seeds=seeds)
    shell, pins = center_to_origin(shell, pins)

    scene = pin_brain(shell, pins)
    render_scene(scene, HERE / "thumbnail.png", preview=True)
    render_scene(scene, HERE / "pin_brain.png")


if __name__ == "__main__":
    build()
