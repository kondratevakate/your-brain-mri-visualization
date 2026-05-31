#!/usr/bin/env python
"""Independent check that a SynthSeg volume CSV is trustworthy.

A pipeline returning exit 0 is not proof the numbers are right — segmentation can
fail silently and emit plausible-but-wrong values. This re-derives each volume a
second way (count the voxels in the label map and multiply by the voxel volume)
and compares it to the CSV. It catches the two classic silent bugs:
  * unit mistakes (mm^3 reported as mL, off by 1000x)
  * left/right column swaps
It also bounds a few structures to human physiological ranges.

Usage:
  python verify_volumes.py <seg.nii.gz> <vol.csv>
Exit code is non-zero if any hard check fails.
"""
import sys, csv
import numpy as np
import nibabel as nib

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
except Exception:
    pass

SEG = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: verify_volumes.py <seg.nii.gz> <vol.csv>")
VOL = sys.argv[2] if len(sys.argv) > 2 else sys.exit("usage: verify_volumes.py <seg.nii.gz> <vol.csv>")

LABELS = {17: "L_Hippocampus", 53: "R_Hippocampus", 18: "L_Amygdala", 54: "R_Amygdala",
          10: "L_Thalamus", 49: "R_Thalamus", 11: "L_Caudate", 50: "R_Caudate",
          12: "L_Putamen", 51: "R_Putamen", 13: "L_Pallidum", 52: "R_Pallidum"}
NAME_TO_ID = {"left hippocampus": 17, "right hippocampus": 53, "left amygdala": 18,
              "right amygdala": 54, "left thalamus": 10, "right thalamus": 49,
              "left thalamus proper": 10, "right thalamus proper": 49,
              "left caudate": 11, "right caudate": 50, "left putamen": 12,
              "right putamen": 51, "left pallidum": 13, "right pallidum": 52}
BOUNDS_mL = {"Hippocampus_LR": (4.0, 10.0), "Amygdala_LR": (1.5, 5.0), "Thalamus_LR": (10.0, 22.0)}


def norm(s):
    return s.strip().strip('"').lower().replace("-", " ").replace("_", " ")


def read_csv_mm3(path):
    rows = list(csv.reader(open(path, newline="")))
    out = {}
    for name, val in zip(rows[0], rows[1]):
        nid = NAME_TO_ID.get(norm(name))
        if nid is not None:
            try:
                out[nid] = float(val)
            except ValueError:
                pass
    return out


seg_img = nib.load(SEG)
seg = np.asarray(seg_img.dataobj).astype(int)
vox_mm3 = float(np.prod(seg_img.header.get_zooms()[:3]))
csv_mm3 = read_csv_mm3(VOL)

hard = []
print(f"voxel volume {vox_mm3:.4f} mm^3   seg shape {seg.shape}")
for lid, name in LABELS.items():
    if lid not in csv_mm3:
        continue
    voxel_mm3 = int((seg == lid).sum()) * vox_mm3
    csv_val = csv_mm3[lid]
    if csv_val <= 0:
        continue
    rel = abs(voxel_mm3 - csv_val) / csv_val
    flag = "  !" if rel > 0.05 else "   "
    print(f"{flag} {name:14s} CSV={csv_val/1000:7.3f} mL  voxel={voxel_mm3/1000:7.3f} mL  d={rel*100:4.1f}%")
    if rel > 0.05:
        hard.append(f"{name}: CSV vs voxel disagree {rel*100:.1f}% -> unit or column bug")


def mL(lid):
    return csv_mm3.get(lid, 0.0) / 1000.0


for key, (lo, hi) in BOUNDS_mL.items():
    a, b = {"Hippocampus_LR": (17, 53), "Amygdala_LR": (18, 54), "Thalamus_LR": (10, 49)}[key]
    v = mL(a) + mL(b)
    if not (lo <= v <= hi):
        print(f"  flag {key}={v:.2f} mL outside [{lo},{hi}] (low-res / artifact?)")

if hard:
    print("\nFAIL:")
    for h in hard:
        print("  -", h)
    sys.exit(1)
print("\nOK: all volumes re-derived from the label map within 5%.")
