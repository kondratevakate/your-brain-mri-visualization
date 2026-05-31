---
name: brain-mri-reproducibility
description: >-
  Quality-check and reproducibility analysis for brain MRI segmentation
  (SynthSeg, FastSurfer, FreeSurfer). Use when segmenting subcortical/cortical
  structures and you need to know whether the volumes are trustworthy: verifying
  outputs, measuring the method-variance floor via rotation, separating physics
  from model instability, comparing scanners, comparing pipelines, or building a
  multi-angle TTA estimate. Triggers on: "is this segmentation reliable", "scanner
  reproducibility", "test-retest brain volume", "segmentation QC", "method floor",
  "compare SynthSeg and FastSurfer", "rotation robustness".
---

# Brain MRI segmentation reproducibility & QC

A practical methodology for deciding whether brain-segmentation volumes can be
trusted, and for measuring where the error comes from. All scripts live in
`scripts/` of this repo and take paths via `DATA` / `FS_LICENSE_FILE` env vars.

## Mental model: where does the variability come from?

A reported volume differs from a "true" volume because of several stacked sources.
Measure them in this order — each isolates one source:

```
physics (interpolation)      ~0.05%   ← decompose_floor.py
model instability (rotation) ~1.4%    ← symmetry_test.py + tta_sweep_report.py
cross-pipeline (SynthSeg/FS)  1-20%   ← cross_method_corr.py
cross-scanner (vendor/field)  10-45%  ← qc_report.py
clinical signal to detect    ~2%/yr
```

The key question is always: **is the effect I care about larger than the floor
below it?** Cross-scanner (17%) >> method floor (1.4%) means scanner effects are
real, not processing noise. But model floor (1.4%) vs annual atrophy (2%) means
single-subject cross-sectional tracking is barely above noise.

## Workflow

1. **Segment** — `run_synthseg.sh <t1> <id>` (contrast/resolution-agnostic, works
   on 5 mm or 0.5 mm) or `run_fastsurfer.sh <t1> <sid> [seg|full]`.

2. **Verify the output is self-consistent** — `verify_volumes.py <seg> <vol.csv>`
   re-derives every volume by counting label voxels. Catches mm³-vs-mL and L/R
   bugs that pass silently. **Never trust an exit code** — a silent OOM kill
   returns 0; check the stats file exists and the numbers re-derive.

3. **Measure the method floor** — `symmetry_test.py <t1> <out>` makes two
   identically-interpolated rotated copies (interpolate BOTH, or you measure
   interpolation bias, not the floor). Segment both; their spread is the floor.
   For the full picture, loop over angles (−12°…+12°) and run `tta_sweep_report.py`.

4. **Decompose the floor** — `decompose_floor.py <seg_orig> <seg_rotpos> <seg_rotneg>`
   splits it into physics (interpolation) vs model instability. If model >> physics,
   the network is far from rotation-equivariant — the floor is a model property,
   not unavoidable noise.

5. **Compare scanners / pipelines** — `qc_report.py a=.. b=.. c=..` gives CV%,
   range/min, and the L/R asymmetry index per scan (watch for **sign flips** —
   a scanner reversing which side looks bigger is a strong reproducibility failure).
   `cross_method_corr.py` checks whether two segmenters fail the same way.

## Hard-won gotchas (these will bite you)

- **FastSurfer `--vox_size 1`** is mandatory on sub-mm input. It auto-selects
  `vox_size=min`, conforms to ~640³, and the VINN step gets OOM-killed (log stops
  after "conforming", exit code can still be 0).
- **FastSurfer `--user root`** — the default nonroot user can't write to a Docker
  Desktop bind mount; outputs silently fail.
- **3D inversion-recovery (IR) contrast collapses FastSurfer VINN** (out of
  distribution; BrainSeg drops to ~1/8). SynthSeg `--robust` is the fallback.
- **Surface recon needs ≲1.5 mm slices.** 5 mm scans fail the surface module.
- **Cross-method bias is not noise.** SynthSeg and FastSurfer define boundaries
  differently (amygdala offset ~14%). Combine relative changes (Δ%) across methods,
  never absolute volumes. Average absolute volumes only WITHIN one method (TTA).
- **Git Bash on Windows** mangles `/data`-style container paths — set
  `MSYS_NO_PATHCONV=1` for every `docker run`.
- **SynthSeg `--robust` peaks at ~15 GB RAM.** Run scans serially on a 16 GB box.

## What this method does NOT give you

- **Accuracy vs ground truth.** There is no in-vivo gold standard for subcortical
  volumes (would need histology). Everything here is *reproducibility / agreement*,
  not accuracy. Say so explicitly.
- **A fix for cross-scanner bias.** Harmonisation (ComBat) needs N>20 subjects per
  site — it cannot help a single subject. Longitudinal pipelines reduce within-
  subject variance but not cross-scanner bias.

## Pilot reference numbers (n=1, 3 scanners, SynthSeg)

These are the order-of-magnitude values to sanity-check against:
physics floor 0.05%, model floor 1.4% (97% of which is model, not interpolation),
9-angle TTA CV 1.24%, cross-scanner median 17% (pallidum 45%, R amygdala 28%),
SynthSeg↔FastSurfer rotation-response correlation r ≈ 0 (independent failures).
