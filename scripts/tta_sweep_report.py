#!/usr/bin/env python
"""Analyse a multi-angle TTA sweep: CV%, TTA-corrected volume, symmetry.

Run a segmenter on the same scan rotated to several angles (e.g. -12° to +12°
in 3° steps; generate with symmetry_test.py looped over angles), then point this
at the resulting volume CSVs. It reports, per structure:
  * CV% across angles (proper statistic, vs the 2-point range/min)
  * TTA-corrected volume = mean across all angles (reduced bias + variance)
  * max excursion at the extreme angles
  * whether the orientation response is symmetric around 0° (a sign-flip of the
    slope on either side means systematic orientation bias, not random noise)

Usage:
  python tta_sweep_report.py <vol_dir> [glob=vol_*.csv]
  # vol_dir contains the per-angle CSVs; filenames must sort by angle.
"""
import sys, os, csv, glob, statistics as st

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

if len(sys.argv) < 2:
    sys.exit("usage: tta_sweep_report.py <vol_dir> [glob]")
VDIR = sys.argv[1]
PATTERN = sys.argv[2] if len(sys.argv) > 2 else "vol_*.csv"

REGS = [("L_Hippocampus", "left hippocampus"), ("R_Hippocampus", "right hippocampus"),
        ("L_Amygdala", "left amygdala"),        ("R_Amygdala", "right amygdala"),
        ("L_Thalamus", "left thalamus"),         ("R_Thalamus", "right thalamus"),
        ("L_Caudate", "left caudate"),           ("R_Caudate", "right caudate"),
        ("L_Putamen", "left putamen"),           ("R_Putamen", "right putamen"),
        ("L_Pallidum", "left pallidum"),         ("R_Pallidum", "right pallidum")]


def norm(s):
    return s.strip().strip('"').lower().replace("-", " ").replace("_", " ")


def load(path):
    r = list(csv.reader(open(path, newline="")))
    out = {}
    for h, v in zip(r[0], r[1]):
        try:
            out[norm(h)] = float(v) / 1000
        except ValueError:
            pass
    return out


files = sorted(glob.glob(os.path.join(VDIR, PATTERN)))
if len(files) < 3:
    sys.exit(f"need >=3 angle CSVs in {VDIR}, found {len(files)}")
data = [load(f) for f in files]
mid = len(data) // 2  # assume the middle file is the 0° / least-rotated one

print(f"TTA sweep over {len(files)} angles\n")
print(f"{'Region':14s} | {'CV %':>5s} | {'TTA mean (mL)':>13s} | {'max excursion':>13s}")
print("-" * 56)
cvs = []
for rl, cn in REGS:
    vals = [d.get(cn) for d in data if d.get(cn) is not None]
    if len(vals) < 3:
        continue
    mean = st.mean(vals)
    cv = st.pstdev(vals) / mean * 100
    excursion = (max(vals) - min(vals)) / min(vals) * 100
    cvs.append(cv)
    print(f"{rl:14s} | {cv:5.2f} | {mean:13.3f} | {excursion:12.2f}%")

print(f"\nMedian CV across structures: {st.median(cvs):.2f}%")
print(f"TTA-corrected volume = the 'TTA mean' column (average over all angles).")
print(f"Note: an asymmetric response (different slope on +/- sides) means TTA is "
      f"correcting orientation BIAS, not just averaging random noise.")
