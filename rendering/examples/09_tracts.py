"""DTI tracts (public DIPY bundles) swept to direction-colored tubes.

Real anatomy (arcuate fasciculus, corticospinal tract, corpus callosum) from
the DIPY bundles_2_subjects dataset. RGB = |fiber direction| (neuroimaging
convention: red=L-R, green=A-P, blue=I-S).

Run from repo root:
    python -m rendering.examples.09_tracts
"""
from pathlib import Path

from dipy.data import read_bundles_2_subjects

from rendering.mesh_prep import center_to_origin
from rendering.forms.streamlines import tract_tubes
from rendering.scene import Scene, Layer, Material, LightRig, CameraRig, render_scene

OUT = Path("rendering/output/09_tracts.png")

print("[1/3] loading public bundles...")
dix = read_bundles_2_subjects("subj_1", ["t1"],
                              ["af.left", "cst.right", "cc_1"])
streamlines = []
for key in ("af.left", "cst.right", "cc_1"):
    streamlines.extend(list(dix[key]))
print(f"      {len(streamlines)} streamlines loaded")

print("[2/3] sweeping to direction-colored tubes...")
tracts = tract_tubes(streamlines, max_lines=4000, radius=0.45,
                     sides=5, decimate_eps=0.6, seed=3)
print(f"      tracts: {len(tracts.faces)} faces")

(tracts,) = center_to_origin(tracts)

print("[3/3] rendering...")
scene = Scene(
    layers=[Layer(tracts, Material(kind="tract", emission_strength=1.1),
                  name="Tracts")],
    light=LightRig("reef", strength=0.3, background=(0.01, 0.01, 0.02)),
    camera=CameraRig(azim_deg=90, elev_deg=8, distance_factor=2.2, dof=False),
    resolution=(1200, 1200),
    samples=48,
)
out = render_scene(scene, OUT)
print(f"wrote {out}")
