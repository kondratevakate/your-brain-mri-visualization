# tools — process & quality-check your brain MRI

Small, dependency-light scripts to segment a T1 and then *sanity-check* the
result before you trust the numbers (or turn them into meshes). Everything runs
through Docker, takes paths via environment variables (no hard-coded paths), and
works on any single T1.

## Setup
```bash
export DATA=/path/to/data_root             # this folder is mounted as /data
export FS_LICENSE_FILE=/path/to/license.txt # FreeSurfer license (free registration)
```
Docker images used: `freesurfer/freesurfer:8.0.0` (SynthSeg), `deepmi/fastsurfer:latest`.

## Segment

| Script | What |
|---|---|
| `run_synthseg.sh <t1_rel> <id>` | SynthSeg — contrast/resolution-agnostic, handles 5 mm or 0.5 mm or odd contrasts. Outputs label map + volumes (mm³) + native QC scores. |
| `run_fastsurfer.sh <t1_rel> <sid> [seg\|full]` | FastSurfer. `seg` = fast VINN volumes (no license). `full` = + surfaces → cortical thickness + Euler number (needs license, hours). |

## Mesh & convert

| Script | What |
|---|---|
| `save_nii_named.sh <SUBJECTS_DIR>` | Convert each subject's `norm.mgz` / `aparc+aseg.mgz` to named NIfTI. |
| `stl_files_creation.sh <folder_of_bin_niftis>` | `mri_tessellate` + `mris_convert` each binarized volume to `.stl`. |
| `freesurfer_stats_to_csv.py` | Pull region volumes out of a FreeSurfer `aseg.stats` into CSV. |

## Quality checks (the point of this folder)

| Script | Question it answers |
|---|---|
| `verify_volumes.py <seg> <vol.csv>` | "Are these volumes even self-consistent?" Re-derives every volume by counting voxels in the label map and comparing to the CSV — catches mm³-vs-mL bugs and L/R column swaps that pass silently. |
| `symmetry_test.py <T1> <out_dir> [theta]` | "How much of my variability is just the pipeline?" Makes two identically-interpolated rotated copies of one scan; segment both → their spread is the **method-variance floor**. |
| `qc_report.py a=vol_a.csv b=vol_b.csv ...` | "How much do the numbers move across scans, and does asymmetry stay stable?" CV%, range/min, and a left/right asymmetry index per scan (watch for **sign flips**). |
| (built into SynthSeg) | `qc_*.csv` holds native QC scores 0–1; flag any structure < 0.65. |

### Typical workflow
```bash
# 1. segment a few scans of the same person
bash run_synthseg.sh sub/ses1/t1.nii.gz ses1
bash run_synthseg.sh sub/ses2/t1.nii.gz ses2

# 2. confirm each result is internally consistent
python tools/verify_volumes.py "$DATA/synthseg/seg_ses1.nii.gz" "$DATA/synthseg/vol_ses1.csv"

# 3. measure the processing-noise floor on one scan
python tools/symmetry_test.py sub/ses1/t1.nii.gz "$DATA/sym"
bash run_synthseg.sh sym/t1_rotpos.nii.gz rotpos
bash run_synthseg.sh sym/t1_rotneg.nii.gz rotneg

# 4. compare spread vs floor
python tools/qc_report.py ses1="$DATA/synthseg/vol_ses1.csv" ses2="$DATA/synthseg/vol_ses2.csv"
python tools/qc_report.py rotpos="$DATA/synthseg/vol_rotpos.csv" rotneg="$DATA/synthseg/vol_rotneg.csv"
```
If the cross-scan spread (step 4a) is much larger than the rotation floor
(step 4b), the differences you see are real, not processing noise.

## Lessons baked into the scripts (so you don't hit them)

- **FastSurfer `--vox_size 1`** is forced. On sub-millimetre input FastSurfer
  auto-selects `vox_size=min`, conforms to a ~640³ grid, and the VINN step gets
  OOM-killed (the log just stops after "conforming"). Fixing the voxel size also
  makes scans comparable.
- **FastSurfer `--user root`** is forced. The image's default `nonroot` user
  can't write to a Docker Desktop bind mount; outputs silently fail otherwise.
- **Trust outputs, not exit codes.** A silent OOM kill can still return 0 —
  `run_fastsurfer.sh` checks the stats file exists, and `verify_volumes.py`
  re-derives the numbers.
- **Contrast / resolution limits.** FastSurfer's VINN collapses on 3D
  inversion-recovery (out-of-distribution) and its surface module needs ≲1.5 mm
  slices. SynthSeg `--robust` is the fallback that handled all of these.
- **SynthSeg `--robust` uses ~15 GB RAM.** Run scans serially on a 16 GB box.
- **Git Bash path mangling.** `MSYS_NO_PATHCONV=1` is set so `/data`-style
  container paths aren't rewritten into Windows paths.
- **Interpolate both copies** in the symmetry test, or you measure interpolation
  bias instead of the method floor.
