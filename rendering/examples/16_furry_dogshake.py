"""Furry brain shaking off like a wet dog — random two-layer pink fur.

Dark short STIFF undercoat + long soft PINK topcoat, randomly distributed (not
rows). Body does a slow dog-shake; the long fur whips with lots of bounce.

    python -m rendering.examples.16_furry_dogshake
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh
from rendering.forms.quills import sample_seeds
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig
from rendering.animate import render_fur_gif, shake_schedule

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/16_furry_dogshake.gif")

PINK = (0.96, 0.58, 0.66, 1.0)         # topcoat (guard hairs)
DARK = (0.45, 0.20, 0.28, 1.0)         # short dark undercoat

print("meshing body + sampling RANDOM fur seeds...")
shell = label_to_mesh(NII, list(range(1000, 3000)),
                      target_faces=12_000, smooth_iter=80, envelope=True)
offset = shell.centroid.copy()
shell.apply_translation(-offset)

# random (not rows) seeds for each coat
u_pts, u_dirs = sample_seeds(shell, 8000, seed=2)     # undercoat
t_pts, t_dirs = sample_seeds(shell, 9000, seed=9)     # topcoat

LAYERS = [
    dict(name="Undercoat", seeds=(u_pts, u_dirs), whip_scale=0.35,
         pin_kwargs=dict(length=7.0, base_radius=0.45, tip_radius=0.14,
                         segments=4, sides=4)),
    dict(name="Topcoat", seeds=(t_pts, t_dirs), whip_scale=1.25,
         pin_kwargs=dict(length=26.0, base_radius=0.42, tip_radius=0.10,
                         segments=7, sides=5)),
]


def scene_factory(shell_r, meshes):
    return Scene(
        layers=[
            Layer(shell_r, Material(kind="stone", color=DARK, roughness=0.75),
                  name="Skin"),
            Layer(meshes["Undercoat"],
                  Material(kind="stone", color=DARK, roughness=0.7),
                  name="Undercoat"),
            Layer(meshes["Topcoat"],
                  Material(kind="stone", color=PINK, roughness=0.5),
                  name="Topcoat"),
        ],
        light=LightRig("reef", strength=1.0, background=(0.74, 0.74, 0.76)),
        camera=CameraRig(azim_deg=40, elev_deg=18, distance_factor=3.2),
        resolution=(480, 480), samples=18,
    )


# slow shake, lots of bounce (low damping), long whip
sched = shake_schedule(48, shake_deg=26.0, n_shakes=3, whip_deg=95.0,
                       w0=4.5, zeta=0.085)

render_fur_gif(shell, LAYERS, scene_factory, OUT,
               n_frames=48, schedule=sched, fps=15)
