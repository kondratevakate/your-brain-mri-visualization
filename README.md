# your-brain-mri-visualization

Turn your own brain MRI into 3D models you can spin around (or 3D-print) in
**Blender** — and *quality-check* the segmentation before you trust it.

![viz](https://github.com/kondratevakate/your-brain-mri-visualization/blob/master/gallery/aseg_nd_aparc.png)

> **Privacy first.** Everything tracked here is *surface meshes* and *label
> volumes* — no skin, skull, or facial features, nothing face-reconstructable.
> Never commit a raw whole-head T1 (it can be used to reconstruct a face); deface
> first with `mri_deface` / `pydeface`.

## How to use — 3 steps

1. **Segment** your T1 → `scripts/run_synthseg.sh` (or `run_fastsurfer.sh`)
2. **Check & mesh** → `scripts/verify_volumes.py` to confirm the numbers, then
   binarize a structure and `scripts/stl_files_creation.sh` to make `.stl`
3. **Render** the `.stl` in Blender (`File → Import → STL`)

Try it on the sample in `example_data/` before using your own scan.

## Repository layout

| Folder | What's in it |
|---|---|
| **`scripts/`** | Everything you run: segment (`run_synthseg.sh`, `run_fastsurfer.sh`), quality-check (`verify_volumes.py`, `symmetry_test.py`, `qc_report.py`), and mesh/convert (`stl_files_creation.sh`, `save_nii_named.sh`, `freesurfer_stats_to_csv.py`). See [`scripts/README.md`](scripts/README.md). |
| **`example_data/`** | A canonical FreeSurfer output (`aparc+aseg.nii.gz` + `aseg.stats` + color tables) so you can try the pipeline without your own recon. |
| **`gallery/`** | Rendered example image(s). |
| **Releases** | The `.stl` mesh binaries — [download here](https://github.com/kondratevakate/your-brain-mri-visualization/releases). They're kept out of git (they bloat history). |

## Quickstart

```bash
export DATA=/path/to/data_root              # mounted as /data in Docker
export FS_LICENSE_FILE=/path/to/license.txt # free FreeSurfer license

# 1. segment a T1 (contrast/resolution-agnostic; handles 5 mm or 0.5 mm scans)
bash scripts/run_synthseg.sh sub/t1.nii.gz mybrain

# 2. check the numbers are self-consistent (catches unit / L-R bugs)
python scripts/verify_volumes.py "$DATA/synthseg/seg_mybrain.nii.gz" "$DATA/synthseg/vol_mybrain.csv"

# 3. binarize a structure group and mesh it
mri_binarize --i "$DATA/synthseg/seg_mybrain.nii.gz" \
  --match 17 53 18 54 10 49 11 50 12 51 13 52 --o subcortical_bin.nii.gz
bash scripts/stl_files_creation.sh /folder/with/bin_niftis    # -> .stl

# 4. import the .stl into Blender, render.
```

## How reproducible is this — on one real brain (n=1)?

These scripts were built while reprocessing **one person's brain across three
scanners over six years**:

| Session | Scanner | Field | Native res |
|---|---|---|---|
| 2018 | GE Signa HDxt | 3.0 T | 1.0 mm |
| 2022 | Siemens Symphony | 1.5 T | 5.0 mm |
| 2024 | Philips Achieva | 1.5 T | 0.5 mm |

There is no in-vivo ground truth, so these are *reproducibility / agreement*
numbers (SynthSeg subcortical volumes), not accuracy-vs-truth:

| Check | What it measures | Result |
|---|---|---|
| Native SynthSeg QC | per-structure confidence (0–1) | 0.72–0.86 (one 0.60 flag on the 0.5 mm IR scan) |
| **Method-variance floor** | re-segment the *same* scan rotated ±3° → pure pipeline noise | **median 1.4%** (max 2.6%) |
| **Cross-scanner spread** | same brain, 3 scanners | **median ~17%**, worst pallidum **45%**, R amygdala **28%** |
| Cross-pipeline (SynthSeg vs FastSurfer, 2018) | same scan, two tools | hippocampus/thalamus 1–8%, amygdala ~15%, pallidum ~20% |
| Surface QC (FastSurfer full, 2018) | topological defect holes | 45 holes (clean), cortical thickness 2.50/2.52 mm, eTIV 1380 mL |

**Takeaway:** the pipeline itself is stable (~1–2% floor), but the *scanner* moves
small subcortical volumes by 10–45%. Big structures (thalamus ~3–5%) are robust;
small, low-contrast ones (amygdala, pallidum) are where scanner choice dominates —
so a single-scanner longitudinal design matters. Numbers come from
`scripts/qc_report.py` and `scripts/symmetry_test.py`.

The same-brain-three-scanners meshes are in the
[`kate-3scanners-2026` release](https://github.com/kondratevakate/your-brain-mri-visualization/releases) —
overlay the three subcortical models in Blender to see the differences. Companion
to *Benchmarking the Reproducibility of Brain Tissue Segmentation Across MRI
Scanners* (MIDL 2026).

## Requirements
- **FreeSurfer 7.4+** or **FastSurfer** (recon + `mri_binarize` / `mri_tessellate` / `mris_convert`).
- **Blender 3.x+** (built-in STL importer).
- A FreeSurfer license (free: https://surfer.nmr.mgh.harvard.edu/registration.html).

## Label reference
Subcortical FreeSurfer label IDs: hippocampus 17/53, amygdala 18/54, thalamus
10/49, caudate 11/50, putamen 12/51, pallidum 13/52. Full list:
`$FREESURFER_HOME/FreeSurferColorLUT.txt`.

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). MIT licensed.

---

**Keywords:** brain MRI visualization · FreeSurfer · FastSurfer · SynthSeg · brain
segmentation · subcortical structures · cortical surface · STL · Blender · 3D brain
model · 3D printing brain · neuroimaging · medical imaging · NIfTI · aseg · aparc ·
T1-weighted MRI · neuroscience · reproducibility · quality control
`#neuroimaging #brainMRI #freesurfer #fastsurfer #synthseg #blender #3dbrain #STL #medicalimaging`
