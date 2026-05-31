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
