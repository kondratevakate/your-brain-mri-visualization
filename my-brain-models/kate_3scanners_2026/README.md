# Kate's brain — 3 scanners, one pipeline (2026)

> The `.stl` meshes are in the [`models-2026` release](https://github.com/kondratevakate/your-brain-mri-visualization/releases/tag/models-2026)
> (`kate-3scanners-2026.zip`), not in git. This folder keeps only provenance.

Derived 3D models for the MIDL 2026 "my brain, 3 scanners, 6 years" demonstration
(companion to *Benchmarking the Reproducibility of Brain Tissue Segmentation
Across MRI Scanners*). Single subject (n=1, self).

**Privacy:** these are surface meshes only — cortical pial surfaces and deep
subcortical structures. No skin, skull, or facial features are included, so the
models are not face-reconstructable. No raw T1 volumes are published here.

## Sessions

| Session | Scanner | Field | Native res | Sequence |
|---|---|---|---|---|
| 2018 | GE Signa HDxt | 3.0 T | 1.0 mm | FSPGR BRAVO (T1) |
| 2022 | Siemens Symphony | 1.5 T | 5.0 mm | T1 SE sag |
| 2024 | Philips Achieva | 1.5 T | 0.5 mm | 3D-IR (T1) |

## Files

| File | Source | Tool |
|---|---|---|
| `2018_ge_lh_pial.stl`, `2018_ge_rh_pial.stl` | FreeSurfer 7-style full recon (FastSurfer surface module) of the 2018 GE scan | `mris_convert` on `surf/{lh,rh}.pial` |
| `2018_ge_fspgr_subcortical.stl` | SynthSeg (FreeSurfer 8 `mri_synthseg --robust`), 2018 | `mri_binarize` + `mri_tessellate` + `mris_convert` |
| `2022_sie_t1se_subcortical.stl` | SynthSeg, 2022 | same |
| `2024_phi_3di_subcortical.stl` | SynthSeg, 2024 | same |

Subcortical meshes merge labels: hippocampus (17/53), amygdala (18/54),
thalamus (10/49), caudate (11/50), putamen (12/51), pallidum (13/52) — one fused
mesh per scanner, so you can overlay the three in Blender and see how the same
deep structures shift across scanners/resolutions.

## Reproduce

Segmentations come from `mri_synthseg --i <T1> --o <seg> --robust` (contrast- and
resolution-agnostic; the only pipeline that handled all three scanners, including
the 5 mm 2022 and the 0.5 mm 3D-IR 2024). Cortical surfaces come from the
FastSurfer surface module (`run_fastsurfer.sh`, no `--seg_only`) on the 2018 scan.
