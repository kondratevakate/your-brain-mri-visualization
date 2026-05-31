#!/usr/bin/env python
"""Method-variance floor via a rotation symmetry test (after M. Reuter).

Goal: separate how much of the volume difference you see between scans is *real*
(scanner / biology) from how much is just *processing noise* (registration,
segmentation, interpolation).

Idea: take ONE scan, make two copies that are interpolated *identically* but
slightly differently (opposite small rotations), and segment both. Since it is
the same brain and same acquisition, any volume difference between the two copies
is pure method noise — the "floor". Compare that floor to the spread you see
across real scanners: if the floor is small, the cross-scanner spread is real.

Caveat (important): interpolate BOTH copies. If you rotate only one and compare
to the original, you measure the interpolation artifact of one-vs-none, not the
method floor. Hence opposite +/-theta rotations, both trilinear.

Usage:
  python symmetry_test.py <in_T1.nii.gz> <out_dir> [theta_degrees=3]
Then segment both outputs (run_synthseg.sh / run_fastsurfer.sh) and compare the
two volume tables; their range/min per structure is the floor.
"""
import sys, os
import numpy as np
import nibabel as nib
from scipy.ndimage import rotate

IN = sys.argv[1] if len(sys.argv) > 1 else sys.exit(
    "usage: symmetry_test.py <in_T1.nii.gz> <out_dir> [theta_deg]")
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else sys.exit(
    "usage: symmetry_test.py <in_T1.nii.gz> <out_dir> [theta_deg]")
THETA = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0

os.makedirs(OUTDIR, exist_ok=True)
img = nib.load(IN)
data = np.asarray(img.dataobj, dtype=np.float32)
stem = os.path.basename(IN).split(".")[0]


def make(theta, tag):
    # order=1 = trilinear; reshape=False keeps the grid so both copies share geometry.
    rot = rotate(data, angle=theta, axes=(0, 1), reshape=False, order=1,
                 mode="constant", cval=0.0)
    out = nib.Nifti1Image(rot.astype(np.float32), img.affine, img.header)
    p = os.path.join(OUTDIR, f"{stem}_rot{tag}.nii.gz")
    nib.save(out, p)
    print(f"wrote {p}  (theta={theta:+.1f} deg, trilinear)")


make(+THETA, "pos")
make(-THETA, "neg")
print("Both copies interpolated identically (opposite rotations). "
      "Segment both, then compare per-structure volumes — range/min is the method floor.")
