#!/usr/bin/env bash
# Run FastSurfer on one T1.
#   seg  = VINN segmentation only — fast (~15-40 min CPU), no license, gives volumes.
#   full = seg + surfaces — slow (hours CPU), needs license, gives cortical
#          thickness and the Euler number / surface-hole count (topological QC).
#
# Usage:
#   export DATA=/path/to/data_root
#   export FS_LICENSE_FILE=/path/to/license.txt   # only needed for 'full'
#   bash run_fastsurfer.sh <t1_relpath_under_DATA> <sid> [seg|full]
#
# Hard-won defaults baked in:
#   --vox_size 1   FastSurfer auto-picks vox_size=min on sub-mm input, which conforms
#                  to a huge 640^3 grid and OOM-kills the VINN step. Forcing 1 mm fixes
#                  it and makes scans comparable. (Found the hard way on a 0.5 mm scan.)
#   --user root    the image's default 'nonroot' user can't write to a bind mount on
#                  Docker Desktop; run as root so outputs land in $DATA.
# Known limits: 3D inversion-recovery (IR) contrast makes VINN collapse (out of
# distribution); slices thicker than ~1.5 mm fail the surface module.
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

DATA="${DATA:?set DATA to your data root (mounted as /data)}"
T1="${1:?usage: run_fastsurfer.sh <t1_relpath_under_DATA> <sid> [seg|full]}"
SID="${2:?usage: run_fastsurfer.sh <t1_relpath_under_DATA> <sid> [seg|full]}"
MODE="${3:-seg}"

mkdir -p "$DATA/fastsurfer"
common=(--t1 "/data/$T1" --sid "$SID" --sd /data/fastsurfer
        --vox_size 1 --device cpu --threads 8 --allow_root)

if [ "$MODE" = full ]; then
  LIC="${FS_LICENSE_FILE:?full mode needs FS_LICENSE_FILE (surfaces call FreeSurfer)}"
  docker run --rm --user root \
    -v "$DATA:/data" -v "$LIC:/fs_license/license.txt:ro" \
    deepmi/fastsurfer:latest \
    "${common[@]}" --fs_license /fs_license/license.txt --3T
else
  docker run --rm --user root \
    -v "$DATA:/data" \
    deepmi/fastsurfer:latest \
    "${common[@]}" --seg_only
fi
# Sanity: seg_only is "done" only if stats exist (exit code can lie on a silent kill).
if [ -f "$DATA/fastsurfer/$SID/stats/aseg+DKT.VINN.stats" ]; then
  echo "OK $SID -> $DATA/fastsurfer/$SID/stats/"
else
  echo "WARNING $SID: no aseg stats produced — check $DATA/fastsurfer/$SID/scripts/*.log" >&2
fi
