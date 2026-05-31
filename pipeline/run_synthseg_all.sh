#!/usr/bin/env bash
# Run SynthSeg via FreeSurfer 8 Docker on all scans, max 2 in parallel.
# Inputs are listed in scans.tsv (id<TAB>relpath_to_t1).
# Outputs: /data/reprocessed_2026/seg/seg_<id>.nii.gz, vol/vol_<id>.csv

set -euo pipefail

# Git Bash (MSYS) rewrites Unix-looking args like /data and /fs_license/... into
# Windows paths before docker sees them, breaking -v targets and in-container paths.
# Disable that conversion for every docker invocation in this script.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

# Configure via environment (no hard-coded paths):
#   export DATA=/path/to/dataset_root        # folder containing images/ and reprocessed_2026/
#   export FS_LICENSE_FILE=/path/to/license.txt
DATA="${DATA:?Set DATA to the dataset root (folder with images/ and reprocessed_2026/)}"
LICENSE="${FS_LICENSE_FILE:?Set FS_LICENSE_FILE to your FreeSurfer license.txt path}"
IMG="freesurfer/freesurfer:8.0.0"
LOG_DIR="$DATA/reprocessed_2026/logs"
mkdir -p "$LOG_DIR"

run_one() {
  local id="$1" rel="$2"
  local log="$LOG_DIR/synthseg_${id}.log"
  local out="$DATA/reprocessed_2026/seg/seg_${id}.nii.gz"
  if [ -f "$out" ]; then echo "[skip ] $id (exists)"; return 0; fi
  echo "[start] $id  $rel"
  docker run --rm \
    -v "$DATA:/data" \
    -v "$LICENSE:/fs_license/license.txt:ro" \
    -e FS_LICENSE=/fs_license/license.txt \
    "$IMG" \
    mri_synthseg \
      --i "/data/$rel" \
      --o "/data/reprocessed_2026/seg/seg_${id}.nii.gz" \
      --vol "/data/reprocessed_2026/vol/vol_${id}.csv" \
      --qc "/data/reprocessed_2026/qc/qc_${id}.csv" \
      --robust --cpu --threads 4 \
      >"$log" 2>&1 && echo "[done ] $id" || echo "[FAIL ] $id (see $log)"
}

export -f run_one
export DATA LICENSE IMG LOG_DIR

# Serial (-P 1): SynthSeg --robust peaks at ~15.6 GB vmpeak per process
# (measured on smoke test), so 2x parallel would OOM/swap on this 13 GB-free box.
SCANS="$(dirname "$0")/scans.tsv"
awk 'NF && $1 !~ /^#/ {print $1"\t"$2}' "$SCANS" | \
  xargs -P 1 -L 1 bash -c 'run_one "$1" "$2"' _
