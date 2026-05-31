#!/usr/bin/env python
"""Reproducibility report across several SynthSeg volume CSVs.

Give it the vol_*.csv files from two or more scans of the same person (e.g. the
same brain on different scanners, or a test-retest pair) and it prints, per deep
structure:
  * the volume in each scan (mL)
  * CV% (SD/mean) and range/min — how much the number moves
  * a left/right asymmetry index per scan — does the asymmetry even keep its sign?

If you pass a rotation pair from symmetry_test.py (two CSVs of the *same* scan),
the same range/min is the method-variance floor: compare it to the cross-scanner
spread to see how much of the difference is real vs processing noise.

Usage:
  python qc_report.py <label1>=<vol1.csv> <label2>=<vol2.csv> [...]
  # e.g. python qc_report.py GE3T=vol_2018.csv Sie15T=vol_2022.csv Phi15T=vol_2024.csv
"""
import sys, csv, statistics as st

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

if len(sys.argv) < 3:
    sys.exit("usage: qc_report.py <label>=<vol.csv> <label>=<vol.csv> [...]")

REGIONS = [("L Hippocampus", "left hippocampus"), ("R Hippocampus", "right hippocampus"),
           ("L Amygdala", "left amygdala"), ("R Amygdala", "right amygdala"),
           ("L Thalamus", "left thalamus"), ("R Thalamus", "right thalamus"),
           ("L Caudate", "left caudate"), ("R Caudate", "right caudate"),
           ("L Putamen", "left putamen"), ("R Putamen", "right putamen"),
           ("L Pallidum", "left pallidum"), ("R Pallidum", "right pallidum")]
PAIRS = [("Hippocampus", "left hippocampus", "right hippocampus"),
         ("Amygdala", "left amygdala", "right amygdala"),
         ("Thalamus", "left thalamus", "right thalamus"),
         ("Caudate", "left caudate", "right caudate"),
         ("Putamen", "left putamen", "right putamen"),
         ("Pallidum", "left pallidum", "right pallidum")]


def norm(s):
    return s.strip().strip('"').lower().replace("-", " ").replace("_", " ")


def load(path):
    rows = list(csv.reader(open(path, newline="")))
    out = {}
    for h, v in zip(rows[0], rows[1]):
        try:
            out[norm(h)] = float(v) / 1000.0  # mm^3 -> mL
        except ValueError:
            pass
    return out


labels, data = [], {}
for arg in sys.argv[1:]:
    lab, path = arg.split("=", 1)
    labels.append(lab)
    data[lab] = load(path)

print("\n## Volumes (mL) + spread\n")
print("| Region | " + " | ".join(labels) + " | CV % | range/min % |")
print("|" + "---|" * (len(labels) + 3))
for rl, cn in REGIONS:
    vals = [data[l].get(cn) for l in labels]
    cells = [f"{v:.2f}" if v is not None else "—" for v in vals]
    nn = [v for v in vals if v is not None]
    if len(nn) >= 2:
        cv = st.pstdev(nn) / st.mean(nn) * 100
        rng = (max(nn) - min(nn)) / min(nn) * 100
        print(f"| {rl} | " + " | ".join(cells) + f" | {cv:.1f} | {rng:.1f} |")
    else:
        print(f"| {rl} | " + " | ".join(cells) + " | — | — |")

print("\n## Asymmetry index (L-R)/(0.5*(L+R))*100 per scan\n")
print("(watch for sign flips — that means a scanner reversed which side looks bigger)\n")
print("| Structure | " + " | ".join(labels) + " |")
print("|" + "---|" * (len(labels) + 1))
for lbl, l, r in PAIRS:
    cells = []
    for lab in labels:
        L, R = data[lab].get(l), data[lab].get(r)
        cells.append(f"{(L - R) / (0.5 * (L + R)) * 100:+.1f}" if L and R else "—")
    print(f"| {lbl} | " + " | ".join(cells) + " |")
