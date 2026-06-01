# Contributing

Thanks for wanting to improve this repo. It is a small, practical toolkit for
turning your own brain MRI into 3D models and checking the segmentation quality
along the way. Contributions that make it easier or more reliable for other
people to do that are very welcome.

## Good first contributions
- A new segmentation target (e.g. a `--match` recipe + label list for a structure
  group) wired into `scripts/`.
- Support for another tool (FreeSurfer 7.4 `recon-all`, ANTs, etc.) as a
  `scripts/run_*.sh` with the same env-var interface.
- A Blender import/material script so people get a nice render in one step.
- Better quality checks, or porting `verify_volumes.py` / `qc_report.py` to other
  segmenters' output formats.
- Docs, examples, and fixes to the gotchas list in `scripts/README.md`.

## Ground rules
1. **No personal/identifiable data in git.** Surface meshes only — never commit a
   raw, un-defaced T1 (a whole-head volume can be used to reconstruct a face).
   Never commit a FreeSurfer `license.txt` or any credentials.
2. **No hard-coded absolute paths.** Scripts take inputs via arguments and the
   `DATA` / `FS_LICENSE_FILE` environment variables, so they run on any machine.
3. **Large binaries go to Releases, not git.** `.stl` and other big meshes are
   attached to a GitHub Release; `*.stl` is gitignored. Keep the git tree small.
4. **Keep scripts in `scripts/`.** The repo root stays readable — code lives in
   `scripts/`, example inputs in `example_data/`, rendered images in `gallery/`.
5. **Test before you push.** Shell scripts should pass `bash -n`; Python should
   pass `python -c "import ast,sys; ast.parse(open(sys.argv[1]).read())"` and,
   where possible, a quick run on the `example_data/` data.

## How to submit
1. Fork and branch (`feature/your-thing`).
2. Make the change; update the relevant README if behaviour changes.
3. Open a pull request describing what it does and how you tested it.

## Layout
```
README.md          overview, quickstart, accuracy notes
CONTRIBUTING.md    this file
LICENSE            MIT
scripts/           all scripts (segment, verify, mesh, report) + their README
example_data/      a canonical FreeSurfer output to try the pipeline on
gallery/           rendered example image(s)
```
Mesh binaries (`.stl`) live in GitHub Releases, not in git.

---

## Marketplace: contribute a brain figurine or animation

Beyond tooling, this repo is a **gallery of brain renders**. Anyone can add their
own figurine or animation as a self-contained folder under `contributions/`.

### Quick start
1. **Fork & clone**, then `git lfs install` (large assets use Git LFS).
2. **Copy the template:**
   ```bash
   cp -r contributions/_TEMPLATE contributions/<yourhandle>-<short-name>
   ```
3. **Edit `manifest.yaml`** — title, author, type, preset/params, license.
4. **Write `build.py`** using the public API (`rendering.presets`,
   `rendering.scene`, `rendering.forms.*`). It must produce your `output` and a
   small `preview` (use `render_scene(..., preview=True)` for a fast EEVEE thumb).
5. **Render:** `python -m contributions.<yourhandle>-<short-name>.build`
6. **Validate & refresh gallery:**
   ```bash
   python scripts/validate_contributions.py
   python scripts/build_gallery.py
   ```
7. **Open a PR.** CI re-runs validation; a maintainer merges.

### The building blocks (compose freely)
| Axis | Where | Examples |
|---|---|---|
| Form | `mesh_prep`, `forms/quills`, `forms/tentacles` | envelope, pins, tentacles |
| Material | `scene.Material` | glass, sss, stone, emission, tract |
| Surface | `scene.Surface` | WOOD / STUCCI / VORONOI displacement |
| Light | `scene.LightRig` | studio, reef, dramatic, underwater |
| Camera | `scene.CameraRig` | angle, depth-of-field |
| Animation | `animate` | turntable + whip physics → GIF |
| Presets | `presets` | glass_clear, pin_brain, dti, anemone, atlas |

### Bring your own brain
Drop your parcellation at `data/brains/<handle>/aparc+aseg.nii.gz` (LFS) and point
`manifest.data.brain` at it. HCP-style tracts: `python scripts/fetch_data.py
--tracts` → reference `data/tracts/hcp/*.trk`. Each render auto-writes a sidecar
`.json` for reproducibility. **Never commit a raw T1** (see `data/README.md`).
