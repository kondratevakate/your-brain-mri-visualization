"""DTI tract variants from different camera angles, saved to the repo.

Streamlines loaded + swept ONCE; only the camera changes per render.
Run from repo root:
    python -m rendering.examples.11_tracts_variants
"""
from pathlib import Path

from dipy.data import read_bundles_2_subjects

from rendering.mesh_prep import center_to_origin
from rendering.forms.streamlines import tract_tubes
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig, render_scene

OUTDIR = Path("rendering/output")

print("loading + sweeping bundles (once)...")
dix = read_bundles_2_subjects(subj_id="subj_1", metrics=["t1"],
                              bundles=["af.left", "cst.right", "cc_1"])
streamlines = []
for key in ("af.left", "cst.right", "cc_1"):
    streamlines.extend(list(dix[key]))
tracts = tract_tubes(streamlines, max_lines=4500, radius=0.45,
                     sides=5, decimate_eps=0.6, seed=3)
(tracts,) = center_to_origin(tracts)
print(f"tracts: {len(tracts.faces)} faces")

# (name, azim, elev) — sagittal side view and superior top-down view
VIEWS = [
    ("sagittal", 90, 6),
    ("superior", 0, 88),
]

for name, azim, elev in VIEWS:
    out = OUTDIR / f"11_tracts_{name}.png"
    print(f"rendering {name} -> {out.name}")
    scene = Scene(
        layers=[Layer(tracts, Material(kind="tract", emission_strength=1.1),
                      name="Tracts")],
        light=LightRig("reef", strength=0.3, background=(0.01, 0.01, 0.02)),
        camera=CameraRig(azim_deg=azim, elev_deg=elev, distance_factor=2.2),
        resolution=(1200, 1200),
        samples=48,
    )
    render_scene(scene, out)
    print(f"  wrote {out}")

print("done")
