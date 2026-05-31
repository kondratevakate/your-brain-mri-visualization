#!/usr/bin/env bash
# Full FastSurfer recon (seg + surf) on the ONLY FastSurfer-valid-and-successful
# scan: 2018 GE 3T 1mm. Gives Euler number (real topological QC) + cortical
# thickness. Multi-hour CPU run, intended to run overnight.
# 2022 (5mm) and 2024 (3D-IR, VINN failed) are excluded - surfaces would be garbage.

set -euo pipefail
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

# export DATA=/path/to/dataset_root ; export FS_LICENSE_FILE=/path/to/license.txt
DATA="${DATA:?Set DATA to the dataset root (folder with images/ and reprocessed_2026/)}"
LICENSE="${FS_LICENSE_FILE:?Set FS_LICENSE_FILE to your FreeSurfer license.txt path}"
IMG="deepmi/fastsurfer:latest"
LOG="$DATA/reprocessed_2026/logs/fastsurfer_full_2018.log"
mkdir -p "$DATA/reprocessed_2026/fastsurfer"

echo "[start] 2018_ge_fspgr_full $(date +%T)"
docker run --rm --user root \
  -v "$DATA:/data" \
  -v "$LICENSE:/fs_license/license.txt:ro" \
  "$IMG" \
  --t1 /data/images/2018/nifti/3_fspgr_bravo_10mm_ax.nii.gz \
  --sid 2018_ge_fspgr_full --sd /data/reprocessed_2026/fastsurfer \
  --fs_license /fs_license/license.txt \
  --vox_size 1 --3T --device cpu --threads 8 --allow_root \
  >"$LOG" 2>&1 && echo "[done ] 2018_ge_fspgr_full $(date +%T)" \
                || echo "[FAIL ] 2018_ge_fspgr_full (see $LOG)"

# Euler number lands in stats/{lh,rh}.{surf}; surf QC summary:
echo "=== Euler / surface holes (if completed) ==="
grep -riE "euler|holes|defect" "$DATA/reprocessed_2026/fastsurfer/2018_ge_fspgr_full/scripts/recon-surf.log" 2>/dev/null | tail -8 || echo "(no surf log yet)"
