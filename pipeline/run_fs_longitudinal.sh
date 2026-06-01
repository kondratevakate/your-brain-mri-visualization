#!/usr/bin/env bash
# FreeSurfer longitudinal template (Reuter 2012):
#   stage 2a  cross-sectional recon-all per session   (INDEPENDENT -> run in parallel)
#   stage 2b  unbiased -base template                 (needs ALL of 2a -> barrier)
#   stage 2c  -long pass per session                  (INDEPENDENT -> run in parallel)
#
# Why parallel: recon-all is largely single-threaded (talairach, normalize,
# skull-strip); `-threads N` only speeds up a few surface steps. So the real lever
# is DATA-parallelism — run several subjects at once on few threads each — not
# thread-parallelism on one subject. Tune with FS_PARALLEL / FS_THREADS.
#
# Idempotent: skips any stage whose recon-all.done marker exists (safe to re-run /
# resume). 2022 (5mm) / 2024 (odd contrast) may fail surface recon; the base is
# built from whatever timepoints succeeded (need >=2) — a partial run is a finding.

set -uo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

DATA="${DATA:?Set DATA to the dataset root (folder with images/ and reprocessed_2026/)}"
LIC="${FS_LICENSE_FILE:?Set FS_LICENSE_FILE to your FreeSurfer license.txt path}"
IMG="freesurfer/freesurfer:7.4.1"
SD="/data/reprocessed_2026/fs_long"
LOGD="$DATA/reprocessed_2026/logs"
BASE_ID="${FS_BASE_ID:-kate_base}"
PAR="${FS_PARALLEL:-3}"      # subjects in flight at once (RAM: ~2-4 GB each)
THREADS="${FS_THREADS:-2}"   # OpenMP threads per subject (cores/PAR is a good target)
mkdir -p "$DATA/reprocessed_2026/fs_long" "$LOGD"

fs() {
  MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm --user root \
    -v "$DATA:/data" -v "$LIC:/fs_license/license.txt:ro" \
    -e FS_LICENSE=/fs_license/license.txt -e SUBJECTS_DIR="$SD" "$IMG" "$@"
}
done_marker() { [ -f "$DATA/reprocessed_2026/fs_long/$1/scripts/recon-all.done" ]; }
throttle()    { while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do sleep 10; done; }

declare -A TP=(
  [2018]="/data/images/2018/nifti/3_fspgr_bravo_10mm_ax.nii.gz"
  [2022]="/data/images/2022/nifti/4_t1_se_sag.nii.gz"
  [2024]="/data/images/2024/nifti/901_3di_mc_hr.nii.gz"
)

run_cross() {
  local s="$1"
  done_marker "$s" && { echo "[skip] cross $s"; return 0; }
  echo "[start] cross $s $(date +%T)"
  fs recon-all -all -s "$s" -i "${TP[$s]}" -threads "$THREADS" > "$LOGD/fs_cross_${s}.log" 2>&1
  done_marker "$s" && echo "[done] cross $s $(date +%T)" || echo "[FAIL] cross $s (see fs_cross_${s}.log)"
}
run_long() {
  local s="$1" lid="$1.long.$BASE_ID"
  [ -f "$DATA/reprocessed_2026/fs_long/$lid/scripts/recon-all.done" ] && { echo "[skip] long $s"; return 0; }
  echo "[start] long $s $(date +%T)"
  fs recon-all -long "$s" "$BASE_ID" -all -threads "$THREADS" > "$LOGD/fs_long_${s}.log" 2>&1
  [ -f "$DATA/reprocessed_2026/fs_long/$lid/scripts/recon-all.done" ] && echo "[done] long $s $(date +%T)" || echo "[FAIL] long $s"
}

# --- Stage 2a: cross-sectional, PAR subjects at a time ---
echo "== stage 2a: cross-sectional (PAR=$PAR, THREADS=$THREADS) =="
for s in 2018 2022 2024; do throttle; run_cross "$s" & done
wait
ok=(); for s in 2018 2022 2024; do done_marker "$s" && ok+=("$s"); done
echo "cross-sectional succeeded: ${ok[*]}"
if [ "${#ok[@]}" -lt 2 ]; then
  echo "Only ${#ok[@]} timepoint(s) ok; need >=2 for a base template. Stopping."; exit 1
fi

# --- Stage 2b: base template (BARRIER — needs all of 2a) ---
echo "== stage 2b: -base $BASE_ID from ${ok[*]} =="
if [ -f "$DATA/reprocessed_2026/fs_long/$BASE_ID/scripts/recon-all.done" ]; then
  echo "[skip] base (done)"
else
  TPARGS=(); for s in "${ok[@]}"; do TPARGS+=(-tp "$s"); done
  fs recon-all -base "$BASE_ID" "${TPARGS[@]}" -all -threads "$((THREADS*PAR))" > "$LOGD/fs_base.log" 2>&1 \
    && echo "[done] base $(date +%T)" || { echo "[FAIL] base (see fs_base.log)"; exit 1; }
fi

# --- Stage 2c: longitudinal pass, PAR subjects at a time (INDEPENDENT) ---
echo "== stage 2c: -long (parallel, PAR=$PAR) =="
for s in "${ok[@]}"; do throttle; run_long "$s" & done
wait

echo "ALL STAGES DONE $(date +%T). Timepoints: ${ok[*]}"
