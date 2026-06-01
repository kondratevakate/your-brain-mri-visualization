"""Adaptivity proof: glass cortical shell + colored internal nuclei.

One Scene, two layer TYPES (glass + emission), same source volume. This is the
template that tracts and tentacles will plug into later — they are just more
layers.

Run from repo root:
    python -m rendering.examples.07_glass_shell_internal_nuclei
"""
from pathlib import Path

from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig, render_scene

NII = "example_data/aparc+aseg.nii.gz"
OUT = Path("rendering/output/07_glass_shell_internal_nuclei.png")

CORTEX = list(range(1000, 3000))
# FreeSurferColorLUT subcortical groups (L+R):
NUCLEI = {
    "thalamus":    ([10, 49], (0.95, 0.65, 0.15)),   # amber
    "hippocampus": ([17, 53], (0.90, 0.20, 0.20)),   # red
    "putamen":     ([12, 51], (0.20, 0.70, 0.90)),   # cyan
}

print("[1/3] meshing glass shell (envelope)...")
shell = label_to_mesh(NII, CORTEX, target_faces=40_000, smooth_iter=60, envelope=True)

print("[2/3] meshing internal nuclei...")
nuclei_meshes = {}
for name, (labels, _color) in NUCLEI.items():
    nuclei_meshes[name] = label_to_mesh(NII, labels, target_faces=6_000,
                                        smooth_iter=25, keep_largest=False)
    print(f"      {name}: {len(nuclei_meshes[name].faces)} faces")

# center EVERYTHING by the shell's centroid so layers stay aligned
all_meshes = center_to_origin(shell, *nuclei_meshes.values())
shell = all_meshes[0]
centered_nuclei = dict(zip(nuclei_meshes.keys(), all_meshes[1:]))

print("[3/3] composing scene + rendering...")
layers = [
    Layer(shell, Material(kind="glass", color=(0.92, 0.95, 1.0, 1.0),
                          roughness=0.05, ior=1.45,
                          absorption_color=(0.85, 0.92, 1.0),
                          absorption_density=0.004),
          subdivision=1, name="Cortex"),
]
for name, (labels, color) in NUCLEI.items():
    layers.append(
        Layer(centered_nuclei[name],
              Material(kind="emission", emission_color=color, emission_strength=6.0),
              name=name)
    )

scene = Scene(
    layers=layers,
    # dark background so internal structures glow out of it (tract-figure look).
    # Swapping ONLY the light axis — layers/geometry untouched. That's adaptivity.
    light=LightRig("reef", strength=0.6, background=(0.02, 0.03, 0.05)),
    camera=CameraRig(azim_deg=25, elev_deg=10, distance_factor=2.3, dof=False),
    resolution=(1100, 1100),
    samples=80,
)
out = render_scene(scene, OUT)
print(f"wrote {out}")
