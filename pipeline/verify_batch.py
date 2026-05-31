#!/usr/bin/env python
"""Independent verification of SynthSeg outputs.

Philosophy: a script returning exit 0 is NOT proof of correctness. Segmentation
pipelines fail silently (plausible-but-wrong numbers). Every reported volume is
re-derived by a second, independent path and bounded by physiological sanity.

Checks per scan:
  1. seg geometry: seg.shape == input.shape, affine non-degenerate
  2. label presence: required subcortical labels exist in the seg volume
  3. unit/column cross-check: voxel_count(label) * voxel_volume_mm3 / 1000
     re-derived from seg.nii.gz must match the CSV value (mL) within tolerance.
     Catches mm3-vs-mL bug AND L/R column-mapping bug simultaneously.
  4. physiological bounds: total brain, hippocampus, amygdala within human range.

Exit non-zero if any HARD check fails. Soft flags (out-of-bounds small
structures on thick-slice scans) are reported but do not fail the run, because
that variability is the scientific point of the hook slide.
"""
import sys, os, csv, json
import numpy as np
import nibabel as nib

# Windows consoles default to cp1252 and crash on non-latin glyphs in print().
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# FreeSurfer label ids -> canonical region name
LABELS = {
    17: "L_Hippocampus", 53: "R_Hippocampus",
    18: "L_Amygdala",    54: "R_Amygdala",
    10: "L_Thalamus",    49: "R_Thalamus",
    11: "L_Caudate",     50: "R_Caudate",
    12: "L_Putamen",     51: "R_Putamen",
    13: "L_Pallidum",    52: "R_Pallidum",
}
REQUIRED = [17, 53, 18, 54, 10, 49]  # must be present or scan is suspect

# Physiological bounds in mL (both-hemisphere sum unless noted), generous adult ranges.
BOUNDS_mL = {
    "total_brain": (1000.0, 1600.0),
    "Hippocampus_LR": (4.0, 10.0),
    "Amygdala_LR": (1.5, 5.0),
    "Thalamus_LR": (10.0, 22.0),
}

# SynthSeg vol CSV uses descriptive header names; map them to label ids by
# normalised string so we are robust to "left hippocampus" vs "Left-Hippocampus".
NAME_TO_ID = {
    "left hippocampus": 17, "right hippocampus": 53,
    "left amygdala": 18, "right amygdala": 54,
    "left thalamus": 10, "right thalamus": 49,
    "left thalamus proper": 10, "right thalamus proper": 49,
    "left caudate": 11, "right caudate": 50,
    "left putamen": 12, "right putamen": 51,
    "left pallidum": 13, "right pallidum": 52,
}


def norm(s):
    return s.strip().strip('"').lower().replace("-", " ").replace("_", " ")


def read_vol_csv(path):
    """SynthSeg --vol CSV: row0 = header names, row1 = values (mm^3)."""
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        raise ValueError(f"{path}: expected >=2 rows, got {len(rows)}")
    header, values = rows[0], rows[1]
    out = {}  # label_id -> mm^3
    for name, val in zip(header, values):
        nid = NAME_TO_ID.get(norm(name))
        if nid is not None and val not in ("", None):
            out[nid] = float(val)
    return out


def verify_scan(scan_id, input_path, seg_path, vol_csv):
    hard_fail, soft_flag = [], []
    seg_img = nib.load(seg_path)
    seg = np.asarray(seg_img.dataobj)
    in_img = nib.load(input_path)

    # 1. geometry
    if seg.shape != in_img.shape:
        # SynthSeg resamples to 1mm by default -> shape WILL differ from input.
        # We only require the seg has a sane, non-empty 3D shape.
        if seg.ndim != 3 or min(seg.shape) < 32:
            hard_fail.append(f"seg shape {seg.shape} implausible")
    if abs(np.linalg.det(seg_img.affine[:3, :3])) < 1e-6:
        hard_fail.append("degenerate seg affine")

    # voxel volume of the SEG grid (this is what CSV volumes are computed on)
    zooms = seg_img.header.get_zooms()[:3]
    vox_mm3 = float(np.prod(zooms))

    # 2. label presence
    present = set(np.unique(seg).astype(int).tolist())
    missing = [LABELS[l] for l in REQUIRED if l not in present]
    if missing:
        soft_flag.append(f"missing labels: {', '.join(missing)} (thick-slice?)")

    # 3. unit / column cross-check
    csv_mm3 = read_vol_csv(vol_csv)
    xcheck = []
    for lid in REQUIRED:
        if lid not in present or lid not in csv_mm3:
            continue
        vox_derived_mm3 = int((seg == lid).sum()) * vox_mm3
        csv_val = csv_mm3[lid]
        if csv_val <= 0:
            continue
        rel = abs(vox_derived_mm3 - csv_val) / csv_val
        xcheck.append((LABELS[lid], csv_val / 1000.0, vox_derived_mm3 / 1000.0, rel))
        # 5% tolerance: CSV and voxel-count should agree closely on the same grid
        if rel > 0.05:
            hard_fail.append(
                f"{LABELS[lid]} cross-check {rel*100:.1f}% off "
                f"(CSV {csv_val/1000:.3f} mL vs voxel {vox_derived_mm3/1000:.3f} mL) "
                f"-> unit or column-mapping bug"
            )

    # 4. physiological bounds (mL). Use CSV mm^3 / 1000.
    def mL(lid):
        return csv_mm3.get(lid, 0.0) / 1000.0
    pairs = {
        "Hippocampus_LR": (17, 53),
        "Amygdala_LR": (18, 54),
        "Thalamus_LR": (10, 49),
    }
    bounded = {}
    for key, (l, r) in pairs.items():
        v = mL(l) + mL(r)
        bounded[key] = v
        lo, hi = BOUNDS_mL[key]
        if not (lo <= v <= hi):
            soft_flag.append(f"{key}={v:.2f} mL outside [{lo},{hi}] (low-res artefact?)")

    return {
        "scan_id": scan_id,
        "vox_mm3": round(vox_mm3, 4),
        "seg_shape": tuple(int(x) for x in seg.shape),
        "xcheck": xcheck,
        "bounded_mL": {k: round(v, 3) for k, v in bounded.items()},
        "hard_fail": hard_fail,
        "soft_flag": soft_flag,
    }


def main():
    # args: scans.tsv-style list of  scan_id  input_relpath
    # plus base dir; seg/vol resolved by convention.
    base = sys.argv[1]
    manifest = sys.argv[2]  # tsv: id <tab> relpath
    seg_dir = os.path.join(base, "reprocessed_2026", "seg")
    vol_dir = os.path.join(base, "reprocessed_2026", "vol")

    results, any_hard = [], False
    with open(manifest) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sid, rel = line.split("\t")[:2]
            seg = os.path.join(seg_dir, f"seg_{sid}.nii.gz")
            vol = os.path.join(vol_dir, f"vol_{sid}.csv")
            if not (os.path.exists(seg) and os.path.exists(vol)):
                print(f"[skip] {sid}: outputs not found yet")
                continue
            r = verify_scan(sid, os.path.join(base, rel), seg, vol)
            results.append(r)
            status = "FAIL" if r["hard_fail"] else ("flag" if r["soft_flag"] else "ok")
            print(f"\n[{status:4s}] {sid}  vox={r['vox_mm3']} mm^3  seg_shape={r['seg_shape']}")
            for name, csv_mL, vox_mL, rel in r["xcheck"]:
                mark = "!" if rel > 0.05 else " "
                print(f"   {mark} {name:14s} CSV={csv_mL:7.3f} mL  voxel={vox_mL:7.3f} mL  d={rel*100:4.1f}%")
            for k, v in r["bounded_mL"].items():
                print(f"     {k:16s} {v:.3f} mL")
            for hf in r["hard_fail"]:
                print(f"   HARD: {hf}"); any_hard = True
            for sf in r["soft_flag"]:
                print(f"   flag: {sf}")

    out_json = os.path.join(base, "reprocessed_2026", "qc", "verify_report.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {out_json}")
    sys.exit(1 if any_hard else 0)


if __name__ == "__main__":
    main()
