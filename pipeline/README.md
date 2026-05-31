# pipeline — batch orchestration (a worked end-to-end example)

`scripts/` holds single-scan tools. This folder is the **batch layer** that runs a
whole multi-scan study from a manifest — the worked example behind the
*one brain, three scanners* demo (n=1 reprocessing).

## Setup
```bash
export DATA=/path/to/data_root              # mounted as /data in Docker
export FS_LICENSE_FILE=/path/to/license.txt
cp pipeline/scans.example.tsv pipeline/scans.tsv   # then edit for your scans
```
`scans.tsv` is a tab-separated manifest: `id <TAB> relpath_to_t1_under_DATA`.

## Run
```bash
# 1. SynthSeg on every scan in the manifest (serial; --robust peaks ~15 GB RAM)
bash pipeline/run_synthseg_all.sh

# 2. verify every output re-derives correctly (batch QC + JSON report)
python pipeline/verify_batch.py "$DATA" pipeline/scans.tsv

# 3. (optional) FastSurfer segmentation on the valid T1s
bash pipeline/run_fastsurfer_segonly.sh
bash pipeline/run_fastsurfer_full.sh        # surfaces: Euler + thickness, hours/scan

# 4. (optional) FreeSurfer 7.4 within-subject longitudinal template
bash pipeline/run_fs_longitudinal.sh        # recon-all x N -> -base -> -long

# 5. assemble the result tables (volumes, QC, cross-pipeline)
python pipeline/build_summary.py "$DATA"    # writes reprocessed_2026/summary.md
```

## Files
| File | What |
|---|---|
| `scans.example.tsv` | manifest format example (copy to `scans.tsv`, edit) |
| `run_synthseg_all.sh` | SynthSeg over the whole manifest, serial |
| `run_fastsurfer_segonly.sh` | FastSurfer VINN segmentation (fast, no license) |
| `run_fastsurfer_full.sh` | FastSurfer full recon (surfaces, needs license) |
| `run_fs_longitudinal.sh` | FreeSurfer 7.4 longitudinal template (cross-sectional → base → long) |
| `verify_batch.py` | independent voxel-count verification over the manifest + JSON report |
| `build_summary.py` | aggregate vol/qc CSVs into result tables |

All scripts are env-configured (`DATA`, `FS_LICENSE_FILE`) — no hard-coded paths.
The same FastSurfer/SynthSeg gotchas documented in `scripts/README.md` apply
(`--vox_size 1`, `--user root`, IR-contrast VINN collapse, exit-code lies).
For the rotation / TTA quality checks, use the single-scan tools in `scripts/`
(`symmetry_test.py`, `decompose_floor.py`, `tta_sweep_report.py`).
