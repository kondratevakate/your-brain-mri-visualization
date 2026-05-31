#!/usr/bin/env python
"""Decompose the rotation floor into physics (interpolation) vs model instability.

When you re-segment a rotated copy of a scan, the volume changes. That change
has two causes:
  1. Interpolation: trilinear resampling slightly alters boundary voxels (physics,
     unavoidable, tiny).
  2. Model instability: the network gives a different answer for a slightly
     different input (the model is not rotation-equivariant).

This script separates them. The trick: rotate the *label map* of the original
segmentation (no model re-run) — that isolates the pure interpolation effect.
Volume is rotation-invariant in principle, so any change is interpolation only.
The full floor (re-segmenting rotated images) minus the interpolation-only part
is the model instability.

Usage:
  python decompose_floor.py <seg_orig.nii.gz> <seg_rotpos.nii.gz> <seg_rotneg.nii.gz> [theta_deg=3]

A perfectly equivariant model would give ~0% model instability.
"""
import sys
import numpy as np
import nibabel as nib
from scipy.ndimage import rotate as nd_rotate

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

if len(sys.argv) < 4:
    sys.exit("usage: decompose_floor.py <seg_orig> <seg_rotpos> <seg_rotneg> [theta_deg]")
SEG_ORIG, SEG_POS, SEG_NEG = sys.argv[1:4]
THETA = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0

LABELS = {17: "L_Hippo", 53: "R_Hippo", 18: "L_Amyg", 54: "R_Amyg",
          10: "L_Thal", 49: "R_Thal", 11: "L_Caud", 50: "R_Caud",
          12: "L_Put", 51: "R_Put", 13: "L_Pall", 52: "R_Pall"}

seg_o = nib.load(SEG_ORIG)
arr_o = np.asarray(seg_o.dataobj).astype(np.int16)
arr_p = np.asarray(nib.load(SEG_POS).dataobj).astype(np.int16)
arr_n = np.asarray(nib.load(SEG_NEG).dataobj).astype(np.int16)
vox = float(np.prod(seg_o.header.get_zooms()[:3]))

# Rotate the original LABEL map (order=0 nearest-neighbour: no fractional labels)
arr_o_rot = nd_rotate(arr_o.astype(np.float32), angle=THETA, axes=(0, 1),
                      reshape=False, order=0, mode="constant", cval=0).astype(np.int16)

print(f"Decomposing rotation floor (±{THETA:.0f}°)\n")
print(f"{'Region':10s} | {'interp-only %':>13s} | {'full floor %':>12s} | {'model instab %':>14s}")
print("-" * 60)

interp_all, full_all, model_all = [], [], []
for lid, name in LABELS.items():
    vo = (arr_o == lid).sum() * vox / 1000
    if vo <= 0:
        continue
    vp = (arr_p == lid).sum() * vox / 1000
    vn = (arr_n == lid).sum() * vox / 1000
    vo_rot = (arr_o_rot == lid).sum() * vox / 1000
    interp = abs(vo_rot - vo) / vo * 100
    trio = [vo, vp, vn]
    full = (max(trio) - min(trio)) / min(trio) * 100
    model = max(0.0, full - interp)
    interp_all.append(interp); full_all.append(full); model_all.append(model)
    print(f"{name:10s} | {interp:13.2f} | {full:12.2f} | {model:14.2f}")

import statistics as st
print(f"\n{'MEDIAN':10s} | {st.median(interp_all):13.2f} | {st.median(full_all):12.2f} | {st.median(model_all):14.2f}")
print(f"\nInterpretation: interp-only is the physics floor; model-instability is "
      f"what the network adds. If model >> interp, the network is far from "
      f"rotation-equivariant.")
