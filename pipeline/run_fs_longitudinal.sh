#!/usr/bin/env bash
# Experiment 2 — FreeSurfer 7.4 longitudinal template "под меня" (Reuter 2012).
# Cross-sectional recon-all per session -> unbiased base template -> -long pass.
# CPU, multi-hour per stage. Idempotent: skips a stage whose .done marker exists.
# 2022 (5mm) / 2024 (3D-IR) may fail cross-sectional surface recon; the base is
# then built from whatever timepoints succeeded (need >=2).

set -uo pipefail
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

# export DATA=/path/to/dataset_root ; export FS_LICENSE_FILE=/path/to/license.txt
DATA="${DATA:?Set DATA to the dataset root (folder with images/ and reprocessed_2026/)}"
LIC="${FS_LICENSE_FILE:?Set FS_LICENSE_FILE to your FreeSurfer license.txt path}"
IMG="freesurfer/freesurfer:7.4.1"
SD="/data/reprocessed_2026/fs_long"
LOGD="$DATA/reprocessed_2026/logs"
mkdir -p "$DATA/reprocessed_2026/fs_long" "$LOGD"

fs() {  # run a recon-all invocation in the container
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm --user root \
    -v "$DATA:/data" -v "$LIC:/fs_license/license.txt:ro" \
    -e FS_LICENSE=/fs_license/license.txt -e SUBJECTS_DIR="$SD" \
    "$IMG" "$@"
}
done_marker() { [ -f "$DATA/reprocessed_2026/fs_long/$1/scripts/recon-all.done" ]; }

declare -A TP=(
  [2018]="/data/images/2018/nifti/3_fspgr_bravo_10mm_ax.nii.gz"
  [2022]="/data/images/2022/nifti/4_t1_se_sag.nii.gz"
  [2024]="/data/images/2024/nifti/901_3di_mc_hr.nii.gz"
)

# --- Stage 2a: cross-sectional ---
ok=()
for s in 2018 2022 2024; do
  if done_marker "$s"; then echo "[skip] cross $s (done)"; ok+=("$s"); continue; fi
  echo "[start] cross $s $(date +%T)"
  fs recon-all -all -s "$s" -i "${TP[$s]}" -threads 8 > "$LOGD/fs_cross_${s}.log" 2>&1
  if done_marker "$s"; then echo "[done] cross $s $(date +%T)"; ok+=("$s")
  else echo "[FAIL] cross $s (see fs_cross_${s}.log)"; fi
done

if [ "${#ok[@]}" -lt 2 ]; then
  echo "Only ${#ok[@]} timepoint(s) succeeded; need >=2 for a base template. Stopping."
  exit 1
fi

# --- Stage 2b: base template from successful timepoints ---
TPARGS=(); for s in "${ok[@]}"; do TPARGS+=(-tp "$s"); done
if [ -f "$DATA/reprocessed_2026/fs_long/kate_base/scripts/recon-all.done" ]; then
  echo "[skip] base (done)"
else
  echo "[start] base kate_base from ${ok[*]} $(date +%T)"
  fs recon-all -base kate_base "${TPARGS[@]}" -all -threads 8 > "$LOGD/fs_base.log" 2>&1 \
    && echo "[done] base $(date +%T)" || echo "[FAIL] base (see fs_base.log)"
fi

# --- Stage 2c: longitudinal pass ---
for s in "${ok[@]}"; do
  long_id="${s}.long.kate_base"
  if [ -f "$DATA/reprocessed_2026/fs_long/${long_id}/scripts/recon-all.done" ]; then
    echo "[skip] long $s (done)"; continue
  fi
  echo "[start] long $s $(date +%T)"
  fs recon-all -long "$s" kate_base -all -threads 8 > "$LOGD/fs_long_${s}.log" 2>&1 \
    && echo "[done] long $s $(date +%T)" || echo "[FAIL] long $s (see fs_long_${s}.log)"
done

echo "ALL STAGES ATTEMPTED $(date +%T). Successful timepoints: ${ok[*]}"
