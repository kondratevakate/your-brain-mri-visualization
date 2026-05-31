#!/usr/bin/env python
"""Assemble SynthSeg (and later FastSurfer) volumes into the deliverable tables.

Table 1 - cross-vendor longitudinal (T1 only): 2018 GE / 2022 Siemens / 2024 Philips
Table 2 - within-session multi-contrast (2024 Philips): 3DI / FFE ax / FFE sag / FLAIR / T2 TSE

All volumes reported in mL (mm^3 / 1000). Numbers are re-checked by verify_outputs.py
before this script trusts them.
"""
import sys, os, csv
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Dataset root: pass as argv[1] or set $DATA. No hard-coded path.
BASE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DATA")
if not BASE:
    sys.exit("Usage: build_summary.py <dataset_root>  (or set $DATA)")
VOL_DIR = os.path.join(BASE, "reprocessed_2026", "vol")
QC_DIR = os.path.join(BASE, "reprocessed_2026", "qc")

# Region label -> CSV column name (normalised). Report these in the tables.
REGIONS = [
    ("L Hippocampus", "left hippocampus"),
    ("R Hippocampus", "right hippocampus"),
    ("L Amygdala", "left amygdala"),
    ("R Amygdala", "right amygdala"),
    ("L Thalamus", "left thalamus"),
    ("R Thalamus", "right thalamus"),
    ("L Caudate", "left caudate"),
    ("R Caudate", "right caudate"),
    ("L Putamen", "left putamen"),
    ("R Putamen", "right putamen"),
    ("L Pallidum", "left pallidum"),
    ("R Pallidum", "right pallidum"),
]

TABLE1 = [  # (scan_id, column label for the table)
    ("2018_ge_fspgr", "2018 (3T GE)"),
    ("2022_sie_t1se", "2022 (1.5T Siemens)"),
    ("2024_phi_3di", "2024 (1.5T Philips)"),
]
TABLE2 = [
    ("2024_phi_3di", "T1 3DI (0.5mm)"),
    ("2024_phi_t1ffe_ax", "T1 FFE ax"),
    ("2024_phi_t1ffe_sag", "T1 FFE sag"),
    ("2024_phi_flair", "T2 FLAIR"),
    ("2024_phi_t2tse_ax", "T2 TSE ax"),
    ("2024_phi_t2tse_cor", "T2 TSE cor"),
]


def norm(s):
    return s.strip().strip('"').lower().replace("-", " ").replace("_", " ")


def load_vol_mL(scan_id):
    """Return {normalised column name -> mL} for one scan, or None if absent."""
    p = os.path.join(VOL_DIR, f"vol_{scan_id}.csv")
    if not os.path.exists(p):
        return None
    with open(p, newline="") as f:
        rows = list(csv.reader(f))
    header, values = rows[0], rows[1]

    def to_mL(v):
        try:
            return float(v) / 1000.0  # SynthSeg writes mm^3
        except (TypeError, ValueError):
            return None  # non-numeric cell (e.g. the 'subject' filename column)

    return {norm(h): to_mL(v) for h, v in zip(header, values)}


# ============================================================================
# DESIGN DECISION (your input): how to quantify "Max Δ %" across the columns.
# This single choice sets how dramatic the hook slide reads. Three defensible
# definitions of the spread of one region's volume across scanners/contrasts:
#
#   A) range / min   : (max - min) / min * 100   -> largest, most dramatic
#   B) range / mean  : (max - min) / mean * 100   -> symmetric, "coefficient of range"
#   C) range / median: (max - min) / median * 100 -> robust to one outlier scan
#
# A overstates when the minimum is a degenerate low-res estimate (e.g. 5mm 2022
# amygdala). C is robust but hides a real single-scanner failure. B is the
# conventional reproducibility spread. There is no neutral choice - it is a
# scientific claim about what "disagreement" means for n=1.
#
# TODO(Kate): implement max_delta_pct(values) returning a float percent.
# `values` is a list of per-scan mL floats with Nones already removed.
# Pick A, B, or C (or define your own, e.g. relative to the 0.5mm scan as
# reference truth). Keep it ~3-5 lines so the reasoning stays visible on the slide.
# ============================================================================
def max_delta_pct(values):
    # Variant A: range relative to the smallest scan (most direct "how far apart").
    lo, hi = min(values), max(values)
    return (hi - lo) / lo * 100.0 if lo > 0 else float("nan")


def build_table(scan_cols, title):
    cols = {sid: load_vol_mL(sid) for sid, _ in scan_cols}
    lines = [f"### {title}", ""]
    head = "| Region | " + " | ".join(lbl for _, lbl in scan_cols) + " | Max Δ % |"
    sep = "|" + "---|" * (len(scan_cols) + 2)
    lines += [head, sep]
    for region_label, colname in REGIONS:
        cells, vals = [], []
        for sid, _ in scan_cols:
            d = cols.get(sid)
            v = None if d is None else d.get(colname)
            cells.append("—" if v is None else f"{v:.2f}")
            if v is not None:
                vals.append(v)
        try:
            delta = f"{max_delta_pct(vals):.1f}" if len(vals) >= 2 else "—"
        except NotImplementedError:
            delta = "?"
        lines.append(f"| {region_label} | " + " | ".join(cells) + f" | {delta} |")
    return "\n".join(lines)


def qc_summary():
    lines = ["### SynthSeg QC scores (native, 0–1; flag < 0.65)", ""]
    files = sorted(f for f in os.listdir(QC_DIR) if f.startswith("qc_") and f.endswith(".csv"))
    if not files:
        return "\n".join(lines + ["_no QC files yet_"])
    for fn in files:
        with open(os.path.join(QC_DIR, fn), newline="") as f:
            rows = list(csv.reader(f))
        if len(rows) < 2:
            continue
        hdr, val = rows[0], rows[1]
        sid = fn[3:-4]
        scores = {h: float(v) for h, v in zip(hdr[1:], val[1:])}
        flagged = [f"{k}={v:.2f}" for k, v in scores.items() if v < 0.65]
        mn = min(scores.values())
        status = "FLAG " + ", ".join(flagged) if flagged else "ok"
        lines.append(f"- **{sid}**: min={mn:.2f} — {status}")
    return "\n".join(lines)


def main():
    parts = ["# Kate n=1 reprocessing — SynthSeg volumetry (MIDL 2026 hook)", ""]
    parts.append(build_table(TABLE1, "Table 1 — cross-vendor longitudinal (T1, SynthSeg)"))
    parts.append("")
    parts.append(build_table(TABLE2, "Table 2 — within-session multi-contrast (2024 Philips, SynthSeg)"))
    parts.append("")
    parts.append(qc_summary())
    md = "\n".join(parts) + "\n"
    out = os.path.join(BASE, "reprocessed_2026", "summary.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
