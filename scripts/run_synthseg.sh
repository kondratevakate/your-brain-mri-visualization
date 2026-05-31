#!/usr/bin/env bash
# Segment one T1 with SynthSeg (FreeSurfer 8) — contrast- and resolution-agnostic,
# so it works on non-1mm, non-MPRAGE scans where atlas pipelines struggle.
#
# Usage:
#   export DATA=/path/to/data_root             # mounted as /data in the container
#   export FS_LICENSE_FILE=/path/to/license.txt
#   bash run_synthseg.sh <t1_relpath_under_DATA> <out_id>
#
# Writes under $DATA/synthseg/:
#   seg_<id>.nii.gz   label map (FreeSurfer LUT)
#   vol_<id>.csv      volumes in mm^3 (divide by 1000 for mL)
#   qc_<id>.csv       native SynthSeg QC scores 0-1 (flag < 0.65)
#
# Note: ~15 GB peak RAM with --robust; run serially, not in parallel, on <16 GB.
set -euo pipefail
# Git Bash mangles /data-style args into Windows paths; disable that for docker.
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

DATA="${DATA:?set DATA to your data root (mounted as /data)}"
LIC="${FS_LICENSE_FILE:?set FS_LICENSE_FILE to your FreeSurfer license.txt}"
T1="${1:?usage: run_synthseg.sh <t1_relpath_under_DATA> <out_id>}"
ID="${2:?usage: run_synthseg.sh <t1_relpath_under_DATA> <out_id>}"

mkdir -p "$DATA/synthseg"
docker run --rm \
  -v "$DATA:/data" -v "$LIC:/fs_license/license.txt:ro" \
  -e FS_LICENSE=/fs_license/license.txt \
  freesurfer/freesurfer:8.0.0 \
  mri_synthseg \
    --i "/data/$T1" \
    --o "/data/synthseg/seg_${ID}.nii.gz" \
    --vol "/data/synthseg/vol_${ID}.csv" \
    --qc "/data/synthseg/qc_${ID}.csv" \
    --robust --cpu --threads 4
echo "done -> $DATA/synthseg/{seg,vol,qc}_${ID}.*"
