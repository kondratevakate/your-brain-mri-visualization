"""Template build script for a contribution.

Must, when run from the repo root, produce `output` (and ideally `preview`).
Use the public rendering API — presets + scene compositor.

    python -m contributions._TEMPLATE.build      # (after copying & renaming)
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.presets import glass_frosted
from rendering.scene import render_scene

HERE = Path(__file__).resolve().parent
NII = "example_data/aparc+aseg.nii.gz"


def build():
    shell = label_to_mesh(NII, list(range(1000, 3000)),
                          target_faces=40_000, smooth_iter=40, envelope=True)
    (shell,) = center_to_origin(shell)

    scene = glass_frosted(shell)        # pick any preset, then tweak fields
    scene.samples = 128

    # fast EEVEE thumbnail for the gallery, then the final Cycles render
    render_scene(scene, HERE / "thumbnail.png", preview=True)
    render_scene(scene, HERE / "my_glass_brain.png")


if __name__ == "__main__":
    build()
