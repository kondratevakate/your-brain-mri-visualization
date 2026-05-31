#!/usr/bin/env bash
# FastSurfer --seg_only (CPU) on the 2 FastSurfer-valid T1s for cross-pipeline
# volume comparison vs SynthSeg. seg_only needs NO FreeSurfer license.
# Default vox_size conforms to 1mm -> comparable across 2018 (1mm) and 2024 (0.5mm)
# and comparable to SynthSeg's 1mm internal grid.

set -euo pipefail
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

# export DATA=/path/to/dataset_root (folder with images/ and reprocessed_2026/)
DATA="${DATA:?Set DATA to the dataset root (folder with images/ and reprocessed_2026/)}"
IMG="deepmi/fastsurfer:latest"
SD_HOST="$DATA/reprocessed_2026/fastsurfer"
LOG_DIR="$DATA/reprocessed_2026/logs"
mkdir -p "$SD_HOST" "$LOG_DIR"

run_one() {
  local sid="$1" rel="$2"
  local log="$LOG_DIR/fastsurfer_segonly_${sid}.log"
  echo "[start] $sid  $rel"
  docker run --rm \
    --user root \
    -v "$DATA:/data" \
    "$IMG" \
    --t1 "/data/$rel" \
    --sid "$sid" --sd /data/reprocessed_2026/fastsurfer \
    --seg_only --vox_size 1 --device cpu --threads 4 --allow_root \
    >"$log" 2>&1 && echo "[done ] $sid" || echo "[FAIL ] $sid (see $log)"
}

# Only the 2 FastSurfer-valid scans (verified <=1mm via nibabel).
run_one 2018_ge_fspgr "images/2018/nifti/3_fspgr_bravo_10mm_ax.nii.gz"
run_one 2024_phi_3di  "images/2024/nifti/901_3di_mc_hr.nii.gz"
