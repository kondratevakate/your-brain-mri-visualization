# your-brain-mri-visualization

Turn your own brain MRI into 3D models you can spin around (or 3D-print) in
**Blender** — and *quality-check* the segmentation before you trust it.

Run a FreeSurfer / FastSurfer / SynthSeg segmentation → export the structures you
care about as `.stl` meshes → render. The `tools/` folder also has small scripts
to verify the numbers and measure how reproducible they are.

![viz](https://github.com/kondratevakate/your-brain-mri-visualization/blob/master/viz/aseg_nd_aparc.png)

> **Privacy first.** Everything tracked here is *surface meshes* and *label
> volumes* — no skin, skull, or facial features, nothing face-reconstructable.
> Never commit a raw whole-head T1 (it can be used to reconstruct a face); deface
> first with `mri_deface` / `pydeface`.

## What's inside

```
tools/             all scripts: segment, verify, mesh, report  (start here)
examples/          a canonical FreeSurfer output to try the pipeline on
my-brain-models/   provenance for the demo subject (meshes live in Releases)
viz/               rendered example image
```
Mesh binaries (`.stl`) are in the
[**Releases**](https://github.com/kondratevakate/your-brain-mri-visualization/releases),
not in git (they bloat history and pack poorly).

## Quickstart

```bash
export DATA=/path/to/data_root              # mounted as /data in Docker
export FS_LICENSE_FILE=/path/to/license.txt # free FreeSurfer license

# 1. segment a T1 (contrast/resolution-agnostic; handles 5 mm or 0.5 mm scans)
bash tools/run_synthseg.sh sub/t1.nii.gz mybrain

# 2. check the numbers are self-consistent (catches unit / L-R bugs)
python tools/verify_volumes.py "$DATA/synthseg/seg_mybrain.nii.gz" "$DATA/synthseg/vol_mybrain.csv"

# 3. binarize a structure group and mesh it
mri_binarize --i "$DATA/synthseg/seg_mybrain.nii.gz" \
  --match 17 53 18 54 10 49 11 50 12 51 13 52 --o subcortical_bin.nii.gz
bash tools/stl_files_creation.sh /folder/with/bin_niftis    # -> .stl

# 4. import the .stl into Blender (File -> Import -> STL), render.
```
Full tool list and the FreeSurfer/FastSurfer gotchas we hit are in
[`tools/README.md`](tools/README.md).

## How reproducible is this — on one real brain (n=1)?

These scripts were built while reprocessing **one person's brain across three
scanners over six years** (GE 3T 2018, Siemens 1.5T 2022, Philips 1.5T 2024).
There is no in-vivo ground truth, so these are *reproducibility / agreement*
numbers (SynthSeg subcortical volumes), not accuracy-vs-truth:

| Check | What it measures | Result |
|---|---|---|
| Native SynthSeg QC | per-structure confidence (0–1) | 0.72–0.86 (one 0.60 flag on the 0.5 mm IR scan) |
| **Method-variance floor** | re-segment the *same* scan rotated ±3° → pure pipeline noise | **median 1.4%** (max 2.6%) |
| **Cross-scanner spread** | same brain, 3 scanners | **median ~17%**, worst pallidum **45%**, R amygdala **28%** |
| Cross-pipeline (SynthSeg vs FastSurfer, 2018) | same scan, two tools | hippocampus/thalamus 1–8%, amygdala ~15%, pallidum ~20% |
| Surface QC (FastSurfer full, 2018) | topological defect holes | 45 holes (clean), cortical thickness 2.50/2.52 mm, eTIV 1380 mL |

**Takeaway:** the pipeline itself is stable (~1–2% floor), but the *scanner*
moves small subcortical volumes by 10–45%. Big structures (thalamus ~3–5%) are
robust; small, low-contrast ones (amygdala, pallidum) are where scanner choice
dominates — so a single-scanner longitudinal design matters. Numbers come from
`tools/qc_report.py` and `tools/symmetry_test.py`.

## Requirements
- **FreeSurfer 7.4+** or **FastSurfer** (recon + `mri_binarize` / `mri_tessellate` / `mris_convert`).
- **Blender 3.x+** (built-in STL importer).
- A FreeSurfer license (free: https://surfer.nmr.mgh.harvard.edu/registration.html).

## Label reference
Subcortical FreeSurfer label IDs: hippocampus 17/53, amygdala 18/54, thalamus
10/49, caudate 11/50, putamen 12/51, pallidum 13/52. Full list:
`$FREESURFER_HOME/FreeSurferColorLUT.txt`.

## Example: one brain, three scanners (MIDL 2026)
The `kate-3scanners-2026` release set is the *same* brain segmented from GE 3T,
Siemens 1.5T, and Philips 1.5T scans — overlay the three subcortical meshes in
Blender to see scanner-driven differences. Companion to *Benchmarking the
Reproducibility of Brain Tissue Segmentation Across MRI Scanners*.

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). MIT licensed.

---

**Keywords:** brain MRI visualization · FreeSurfer · FastSurfer · SynthSeg · brain
segmentation · subcortical structures · cortical surface · STL · Blender · 3D brain
model · 3D printing brain · neuroimaging · medical imaging · NIfTI · aseg · aparc ·
T1-weighted MRI · neuroscience · reproducibility · quality control
`#neuroimaging #brainMRI #freesurfer #fastsurfer #synthseg #blender #3dbrain #STL #medicalimaging`
