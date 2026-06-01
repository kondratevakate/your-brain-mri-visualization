# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions use SemVer.

## [0.1.0] — 2026-06-01

First public release: an adaptive, composable **code-driven brain rendering
toolkit** plus a community **marketplace**.

### Added — rendering toolkit (`rendering/`)
- **Composable Scene compositor** (`scene.py`): `Scene(layers × LightRig × CameraRig)`
  with swappable `Material` (glass / sss / stone / emission / tract) and `Surface`
  (procedural displacement: WOOD / STUCCI / MUSGRAVE / VORONOI).
- **Mesh prep** (`mesh_prep.py`): NIfTI labels → smoothed RAS mesh; `detail` vs
  `envelope` modes; Taubin smoothing + quadric decimation.
- **Forms**: `quills.py` (radial pin fields, random or concentric-row layout),
  `tentacles.py` (curled upward sea-anemone tentacles), shared `sweep.py`
  (rotation-minimising tube sweep) reused by tracts and tentacles.
- **DTI tracts** (`forms/streamlines.py`): load `.trk/.tck`, subsample, RDP
  decimate, direction-coloured tubes.
- **Wireframe** matplotlib renderer (`style_wireframe_roi.py`) — no VTK required.
- **Animation** (`animate.py`): turntable + inertial whip physics (damped
  oscillator driven by angular acceleration), seamless loops, plus a **dog-shake**
  motion profile; bent-pin deformation for hair-like fur.
- **Presets** (`presets.py`): glass_clear, glass_frosted, pin_brain, dti, anemone,
  atlas.
- **UX**: fast EEVEE `preview=True` mode and a reproducibility **sidecar JSON**
  written next to every render.
- Lighting rigs: studio, reef, dramatic, underwater.

### Added — marketplace (`contributions/`)
- Category structure: **reports · anatomical-models · 3d-art · anime · universes**.
- Manifest schema + `scripts/validate_contributions.py` (CI gate) +
  `scripts/build_gallery.py` (auto gallery, grouped by category).
- Report templates: **brain-age** dashboard and **PVS** (perivascular spaces).
- Printable **brain.stl** with print + stand instructions and a brain-character
  catalogue.
- GitHub Action validating contribution manifests on PRs.

### Added — data & packaging
- **Git LFS** tracking for `.stl/.ply/.trk/.nii.gz/.gif/.blend` (`.gitattributes`).
- `scripts/fetch_data.py` (public DTI bundles), `data/README.md`.
- `requirements.txt`, `pyproject.toml`.

### Notes
- Privacy: only label volumes / meshes are shared — never raw, face-reconstructable
  T1s. See `data/README.md`.
- Cycles renders need `pip install bpy`; tracts need `pip install dipy`.
