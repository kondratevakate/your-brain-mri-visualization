#!/usr/bin/env python
"""Are two segmenters' errors correlated? (decides if combining them helps)

Give it the same perturbation (e.g. a +3° rotation) segmented by two different
methods (SynthSeg and FastSurfer), each with an original and a perturbed volume.
It reports, per structure, how each method's volume moved under the perturbation,
and the correlation of those movements across structures.

Why this matters:
  * If errors are correlated (r near +1): the methods fail the same way; combining
    them gives little.
  * If errors are independent (r near 0): they fail differently; averaging within
    a method reduces variance — BUT only relative changes (Δ%) can be combined
    across methods, because the methods have systematic offsets (different boundary
    definitions). Absolute volumes must NOT be averaged across methods.

Usage:
  python cross_method_corr.py \
      --a-orig <ss_vol_orig.csv> --a-pert <ss_vol_pert.csv> \
      --b-orig <fs_aseg_orig.stats> --b-pert <fs_aseg_pert.stats>

SynthSeg inputs are vol CSVs; FastSurfer inputs are aseg+DKT.VINN.stats files.
The script auto-detects format by extension (.csv vs .stats).
"""
import sys
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# region -> (synthseg csv name, fastsurfer StructName)
PAIRS = [
    ("L Hippo", "left hippocampus", "Left-Hippocampus"),
    ("R Hippo", "right hippocampus", "Right-Hippocampus"),
    ("L Amyg", "left amygdala", "Left-Amygdala"),
    ("R Amyg", "right amygdala", "Right-Amygdala"),
    ("L Thal", "left thalamus", "Left-Thalamus"),
    ("R Thal", "right thalamus", "Right-Thalamus"),
    ("L Caud", "left caudate", "Left-Caudate"),
    ("R Caud", "right caudate", "Right-Caudate"),
    ("L Put", "left putamen", "Left-Putamen"),
    ("R Put", "right putamen", "Right-Putamen"),
    ("L Pall", "left pallidum", "Left-Pallidum"),
    ("R Pall", "right pallidum", "Right-Pallidum"),
]


def norm(s):
    return s.strip().strip('"').lower().replace("-", " ").replace("_", " ")


def load(path):
    """Auto-detect: .csv = SynthSeg vol (key=normalised name), else FreeSurfer .stats."""
    import csv as _csv
    out = {}
    if path.endswith(".csv"):
        r = list(_csv.reader(open(path, newline="")))
        for h, v in zip(r[0], r[1]):
            try:
                out[norm(h)] = float(v) / 1000
            except ValueError:
                pass
    else:  # FreeSurfer stats: Index SegId NVoxels Volume_mm3 StructName ...
        for line in open(path):
            if line.startswith("#") or not line.strip():
                continue
            c = line.split()
            if len(c) >= 5:
                try:
                    out[c[4]] = float(c[3]) / 1000
                except ValueError:
                    pass
    return out


def arg(flag):
    i = sys.argv.index(flag)
    return sys.argv[i + 1]


try:
    a_orig = load(arg("--a-orig")); a_pert = load(arg("--a-pert"))
    b_orig = load(arg("--b-orig")); b_pert = load(arg("--b-pert"))
except (ValueError, IndexError):
    sys.exit(__doc__)

print("Perturbation response per method (Δ% from original)\n")
print(f"{'Region':8s} | {'A Δ%':>7s} | {'B Δ%':>7s} | same direction?")
print("-" * 45)
a_d, b_d, same = [], [], 0
for label, a_key, b_key in PAIRS:
    ao, ap = a_orig.get(a_key), a_pert.get(a_key)
    bo, bp = b_orig.get(b_key), b_pert.get(b_key)
    if not all([ao, ap, bo, bp]):
        continue
    da = (ap - ao) / ao * 100
    db = (bp - bo) / bo * 100
    agree = (da > 0) == (db > 0)
    same += agree
    a_d.append(da); b_d.append(db)
    print(f"{label:8s} | {da:+6.2f}% | {db:+6.2f}% | {'agree' if agree else 'OPPOSITE'}")

r = np.corrcoef(a_d, b_d)[0, 1]
print(f"\nCorrelation of perturbation response: r = {r:.3f}")
print(f"Same direction: {same}/{len(a_d)} structures")
if abs(r) < 0.3:
    print("=> errors are near-INDEPENDENT. Within-method TTA reduces variance; "
          "but combine only Δ% across methods, never absolute volumes (systematic offset).")
else:
    print("=> errors are correlated. The methods share a failure mode; "
          "combining gives limited benefit.")
